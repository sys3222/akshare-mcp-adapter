from fastapi import FastAPI
from docs_config import custom_openapi
from core.mcp_protocol import MCPRequest, MCPResponse
from adaptors.akshare import AKShareAdaptor

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
app.openapi = custom_openapi(app)  # 应用自定义文档

# 原有服务代码...
