from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException
from typing import Optional, Dict

from models.schemas import (
    BacktestResult, DataSourceList, AkShareCodeRequest, AkShareCodeResponse
)
from core.mcp_protocol import MCPRequest, MCPResponse
from handlers.backtest_handler import (
    handle_upload_and_run_backtest,
    handle_backtest_with_code_only,
    handle_backtest_with_mcp_data
)
from handlers.data_source_handler import handle_get_data_sources
from handlers.akshare_handler import handle_execute_akshare_code
from handlers.mcp_handler import handle_mcp_data_request

router = APIRouter()

@router.post("/backtest", response_model=BacktestResult, tags=["Backtesting"])
async def upload_and_run_backtest(
    strategy_file: UploadFile = File(...),
    data_file: Optional[UploadFile] = File(None),
    params: Optional[str] = Form(None),
    data_source: Optional[str] = Form(None),
    benchmark_symbol: Optional[str] = Form(None)
):
    """
    Upload strategy and data files to run a backtest.
    - Provide either a `data_file` (CSV) or a `data_source` from the available list.
    """
    return await handle_upload_and_run_backtest(
        strategy_file, data_file, params, data_source, benchmark_symbol
    )

@router.post("/backtest-code", response_model=BacktestResult, tags=["Backtesting"])
async def backtest_with_code_only(
    strategy_code: str = Body(..., embed=True),
    symbol: str = Body(..., embed=True),
    start_date: Optional[str] = Body(None, embed=True),
    end_date: Optional[str] = Body(None, embed=True),
    params: Optional[Dict] = Body(None, embed=True),
    benchmark_symbol: Optional[str] = Body(None, embed=True)
):
    """
    Run a backtest directly from Python code using AkShare for data.
    """
    return await handle_backtest_with_code_only(
        strategy_code, symbol, start_date, end_date, params, benchmark_symbol
    )

@router.post("/backtest-with-mcp", response_model=BacktestResult, tags=["Backtesting"])
async def backtest_with_mcp_data(
    strategy_file: UploadFile = File(...),
    interface: str = Form(...),
    symbol: str = Form(...),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    params: Optional[str] = Form(None),
    benchmark_symbol: Optional[str] = Form(None)
):
    """
    Run a backtest using data fetched directly via an AkShare interface.
    """
    return await handle_backtest_with_mcp_data(
        strategy_file, interface, symbol, start_date, end_date, params, benchmark_symbol
    )

@router.get("/data-sources", response_model=DataSourceList, tags=["Data Sources"])
async def get_data_sources():
    """
    Get the list of available AkShare data sources for backtesting.
    """
    return handle_get_data_sources()

@router.post("/execute-akshare", response_model=AkShareCodeResponse, tags=["AkShare"])
async def execute_akshare_code(request: AkShareCodeRequest):
    """
    Execute a snippet of AkShare Python code and get the result.
    - The last variable that is a DataFrame, list, or dict will be returned.
    """
    return handle_execute_akshare_code(request)

@router.post("/mcp-data", response_model=MCPResponse, tags=["MCP Protocol"])
async def get_mcp_data(request: MCPRequest):
    """

    Get data from AkShare using the MCP (Microservice Control Protocol).
    """
    return await handle_mcp_data_request(request)

@router.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok"}
