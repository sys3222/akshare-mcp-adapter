from pydantic import BaseModel
from typing import Any, Optional

class MCPRequest(BaseModel):
    interface: str
    params: dict
    request_id: str
    timeout: Optional[int] = 10

class MCPResponse(BaseModel):
    data: Any
    request_id: str
    status: int = 200
    error: Optional[str] = None
