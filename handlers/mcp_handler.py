import logging
import math
from typing import Optional
from fastapi import HTTPException

from core.mcp_protocol import MCPRequest
from models.schemas import PaginatedDataResponse
from adaptors.akshare import AKShareAdaptor

logger = logging.getLogger("mcp-unified-service")
akshare_adaptor = AKShareAdaptor()

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
        result = await akshare_adaptor.call(request.interface, **request.params)
        
        # Convert DataFrame to a list of records (dicts)
        if hasattr(result, 'to_dict'):
            all_data = result.to_dict('records')
        else:
            all_data = result
            
        if not isinstance(all_data, list):
            all_data = [all_data]

        # Paginate the data
        total_records = len(all_data)
        total_pages = math.ceil(total_records / page_size)
        
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
    except Exception as e:
        logger.error(f"Error processing MCP request for interface '{request.interface}': {e}")
        # Return a valid PaginatedDataResponse with an error payload
        return PaginatedDataResponse(
            data=[],
            total_records=0,
            current_page=page,
            total_pages=0,
            request_id=request.request_id,
            error=f"An internal error occurred: {str(e)}"
        )
