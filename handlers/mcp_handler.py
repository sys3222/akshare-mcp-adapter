import logging
import math
import pandas as pd
from typing import Any, Optional, List, Dict
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_fixed

from core.mcp_protocol import MCPRequest
from models.schemas import PaginatedDataResponse
from adaptors.akshare import AKShareAdaptor

logger = logging.getLogger("mcp-unified-service")
akshare_adaptor = AKShareAdaptor()

# Define a maximum data size limit (e.g., 10 MB) for fetched data
MAX_DATA_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

class DataSizeExceededError(ValueError):
    """Custom exception for when fetched data exceeds the size limit."""
    pass

def _get_data_size(data: Any) -> int:
    """Estimates the size of the data in bytes."""
    if isinstance(data, pd.DataFrame):
        return data.memory_usage(deep=True).sum()
    return 0

def _normalize_data(data: Any) -> List[Dict[str, Any]]:
    """
    Normalizes data from various AkShare return types into a list of dictionaries
    that is JSON serializable.
    """
    if isinstance(data, pd.DataFrame):
        df = data.copy()
        for col in df.columns:
            # Check if the column is of datetime64 type
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            # Also check if the column is of object type and its first non-null element is a date/datetime object
            elif df[col].dtype == 'object':
                first_valid_index = df[col].first_valid_index()
                if first_valid_index is not None:
                    import datetime
                    if isinstance(df[col][first_valid_index], (datetime.date, datetime.datetime)):
                        # Convert entire column, handling potential errors
                        df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

        # Replace any remaining non-serializable values like NaT or NaN
        df = df.replace({pd.NaT: None, float('nan'): None})
        return df.to_dict('records')
    
    if isinstance(data, list):
        if not data:
            return []
        # If it's a list of primitives, convert to list of dicts
        if not isinstance(data[0], dict):
            return [{'value': item} for item in data]
        # It's already a list of dicts
        return data
        
    if isinstance(data, dict):
        # Convert a single dict to a list of key-value pairs
        return [{'key': k, 'value': v} for k, v in data.items()]

    # For single primitive values (str, int, float, etc.)
    if data is not None:
        return [{'value': data}]
        
    return []

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
async def _fetch_akshare_data_with_retry(interface: str, params: Dict[str, Any]) -> Any:
    """
    Fetches data from the AkShare adaptor with a retry mechanism.
    """
    logger.info(f"Attempting to fetch data for interface '{interface}' with params: {params}")
    try:
        return await akshare_adaptor.call(interface, **params)
    except Exception as e:
        logger.warning(f"Attempt to fetch '{interface}' failed: {e}. Retrying...")
        raise

async def _get_and_normalize_akshare_data(interface: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Core logic to fetch data from AKShare and normalize it.
    """
    raw_result = await _fetch_akshare_data_with_retry(interface, params)

    data_size = _get_data_size(raw_result)
    if data_size > MAX_DATA_SIZE_BYTES:
        raise DataSizeExceededError(
            f"Fetched data size ({data_size / 1024 / 1024:.2f} MB) exceeds the limit "
            f"of {MAX_DATA_SIZE_BYTES / 1024 / 1024} MB."
        )
    
    return _normalize_data(raw_result)


async def handle_mcp_data_request(
    request: MCPRequest,
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None
) -> PaginatedDataResponse:
    """
    Handles a data request using the MCP protocol and returns paginated data.
    """
    try:
        user_log_prefix = f"User '{username}'" if username else "Anonymous user"
        logger.info(
            f"{user_log_prefix} initiated MCP request (ID: {request.request_id}): "
            f"Interface: {request.interface}, Params: {request.params}"
        )
        
        all_data = await _get_and_normalize_akshare_data(request.interface, request.params)

        total_records = len(all_data)
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_data = all_data[start_index:end_index]
        
        return PaginatedDataResponse(
            data=paginated_data,
            total_records=total_records,
            current_page=page,
            total_pages=total_pages,
            request_id=request.request_id
        )
    except AttributeError:
        logger.warning(f"Unsupported MCP interface called: {request.interface}")
        raise HTTPException(
            status_code=404, 
            detail=f"Interface not found: '{request.interface}' is not a valid AkShare function."
        )
    except DataSizeExceededError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing MCP request for interface '{request.interface}': {e}", exc_info=True)
        return PaginatedDataResponse(
            data=[],
            total_records=0,
            current_page=page,
            total_pages=0,
            request_id=request.request_id,
            error=f"An internal error occurred: {str(e)}"
        )