import logging
from fastapi import HTTPException

from core.mcp_protocol import MCPRequest, MCPResponse
from adaptors.akshare import AKShareAdaptor

logger = logging.getLogger("mcp-unified-service")
akshare_adaptor = AKShareAdaptor()

async def handle_mcp_data_request(request: MCPRequest) -> MCPResponse:
    """Handles a data request using the MCP protocol."""
    try:
        logger.info(f"MCP data request received: {request.interface}, Params: {request.params}")
        
        # Call the AkShare adaptor
        result = await akshare_adaptor.call(request.interface, **request.params)
        
        # Convert DataFrame to a list of records (dicts)
        if hasattr(result, 'to_dict'):
            data = result.to_dict('records')
        else:
            data = result
            
        return MCPResponse(
            data=data,
            request_id=request.request_id,
            status=200
        )
    except AttributeError:
        logger.warning(f"Unsupported MCP interface called: {request.interface}")
        raise HTTPException(
            status_code=404, 
            detail=f"Interface not found: '{request.interface}' is not a valid AkShare function."
        )
    except Exception as e:
        logger.error(f"Error processing MCP request for interface '{request.interface}': {e}")
        # Return a valid MCPResponse with an error payload
        return MCPResponse(
            data=None,
            request_id=request.request_id,
            status=500,
            error=f"An internal error occurred: {str(e)}"
        )
