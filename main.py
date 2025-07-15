import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import logging

from api.routes import router as api_router
from docs_config import custom_openapi
from core.database import create_db_and_tables

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

# Create database and tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Service starting up...")
    create_db_and_tables()
    yield
    logger.info("Service shutting down...")

app = FastAPI(
    title="MCP Unified Service",
    description="统一的MCP服务：提供AkShare数据接口和量化回测功能",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
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

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Redirect to the main page"""
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    logger.info("启动MCP统一服务 - AkShare数据 + 量化回测")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=12001, 
        reload=True
    )