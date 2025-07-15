import logging
import math
import pandas as pd
from typing import Any, Optional, List, Dict
from fastapi import HTTPException

from core.mcp_protocol import MCPRequest
from models.schemas import PaginatedDataResponse
from adaptors.akshare import AKShareAdaptor

logger = logging.getLogger("mcp-unified-service")
akshare_adaptor = AKShareAdaptor()

# Define a maximum data size limit (e.g., 10 MB) for fetched data
MAX_DATA_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def _get_data_size(data: Any) -> int:
    """Estimates the size of the data in bytes."""
    if isinstance(data, pd.DataFrame):
        return data.memory_usage(deep=True).sum()
    # Add other type estimations if necessary, for now, this is the primary concern
    return 0

def _normalize_data(data: Any) -> List[Dict[str, Any]]:
    """
    Normalizes data from various AkShare return types into a list of dictionaries.
    """
    if isinstance(data, pd.DataFrame):
        # Convert NaT to None (or string) for JSON serialization
        df = data.replace({pd.NaT: None})
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

async def handle_mcp_data_request(
    request: MCPRequest,
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None
) -> PaginatedDataResponse:
    """
    Handles a data request using the MCP protocol and returns paginated data.
    Logs the requesting user if provided.
    """
    try:
        user_log_prefix = f"User '{username}'" if username else "Anonymous user"
        logger.info(
            f"{user_log_prefix} initiated MCP request (ID: {request.request_id}): "
            f"Interface: {request.interface}, Params: {request.params}"
        )
        
        # Call the AkShare adaptor
        raw_result = await akshare_adaptor.call(request.interface, **request.params)

        # Check the size of the fetched data before proceeding
        data_size = _get_data_size(raw_result)
        if data_size > MAX_DATA_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Fetched data size ({data_size / 1024 / 1024:.2f} MB) exceeds the limit "
                       f"of {MAX_DATA_SIZE_BYTES / 1024 / 1024} MB. Please refine your query."
            )
        
        # Normalize the raw result into a list of dictionaries
        all_data = _normalize_data(raw_result)

        # Paginate the data
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
    except HTTPException as e:
        # Re-raise to preserve status code and details
        raise e
    except Exception as e:
        logger.error(f"Error processing MCP request for interface '{request.interface}': {e}", exc_info=True)
        # Return a valid PaginatedDataResponse with an error payload
        return PaginatedDataResponse(
            data=[],
            total_records=0,
            current_page=page,
            total_pages=0,
            request_id=request.request_id,
            error=f"An internal error occurred: {str(e)}"
        )