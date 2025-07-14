import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from api.routes import router as api_router
from docs_config import custom_openapi
from core.mcp_protocol import MCPRequest, MCPResponse
from adaptors.akshare import AKShareAdaptor

app = FastAPI(
    title="MCP Unified Service",
    description="统一的MCP服务：提供AkShare数据接口和量化回测功能",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 应用自定义文档配置
app.openapi = custom_openapi(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AkShare adaptor
akshare_adaptor = AKShareAdaptor()

# Include API routes (backtest functionality)
app.include_router(api_router, prefix="/api")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Redirect to the main page"""
    return RedirectResponse(url="/static/index.html")

@app.post("/api/mcp", response_model=MCPResponse)
async def mcp_endpoint(request: MCPRequest):
    """
    MCP协议端点 - 提供AkShare数据接口
    
    支持的接口包括：
    - stock_zh_a_hist: 获取A股历史数据
    - fund_em_open_fund_info: 获取基金信息
    - index_zh_a_hist: 获取指数历史数据
    - 等等...
    """
    try:
        # 调用AkShare方法
        result = await akshare_adaptor.call(request.interface, **request.params)
        
        # 如果结果是DataFrame，转换为字典格式
        if hasattr(result, 'to_dict'):
            result = result.to_dict('records')
        
        return MCPResponse(
            data=result,
            request_id=request.request_id,
            status=200
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的接口: {request.interface}"
        )
    except Exception as e:
        return MCPResponse(
            data=None,
            request_id=request.request_id,
            status=500,
            error=str(e)
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=12001, 
        reload=True
    )