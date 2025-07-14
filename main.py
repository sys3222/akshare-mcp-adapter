import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import logging

from api.routes import router as api_router
from docs_config import custom_openapi
from core.mcp_protocol import MCPRequest, MCPResponse
from adaptors.akshare import AKShareAdaptor
from utils.akshare_utils import init_akshare_cache
from handlers.mcp_handler import handle_mcp_data_request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mcp-unified-service")

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

# Initialize AkShare cache for backtesting
init_akshare_cache()

# Include API routes (backtest functionality)
app.include_router(api_router, prefix="/api")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Redirect to the main page"""
    return RedirectResponse(url="/static/index.html")

@app.get("/api/interfaces")
async def get_available_interfaces():
    """获取所有可用的AkShare接口列表"""
    try:
        # 常用接口分类
        common_interfaces = {
            "股票数据": [
                {"name": "stock_zh_a_hist", "description": "A股历史行情数据"},
                {"name": "stock_zh_a_spot_em", "description": "A股实时行情数据"},
                {"name": "stock_zh_a_daily", "description": "A股日线行情数据"}
            ],
            "指数数据": [
                {"name": "index_zh_a_hist", "description": "中国股票指数历史数据"},
                {"name": "index_stock_cons", "description": "指数成分股数据"}
            ],
            "基金数据": [
                {"name": "fund_em_open_fund_info", "description": "开放式基金信息"},
                {"name": "fund_etf_spot_em", "description": "ETF基金实时行情"}
            ],
            "期货数据": [
                {"name": "futures_zh_daily", "description": "中国期货日线数据"},
                {"name": "futures_zh_spot", "description": "中国期货实时行情"}
            ]
        }
        
        return {
            "status": "success",
            "interfaces": common_interfaces
        }
    except Exception as e:
        logger.error(f"获取接��列表错误: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    logger.info("启动MCP统一服务 - AkShare数据 + 量化回测")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=12001, 
        reload=True
    )
