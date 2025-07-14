from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query, Body
from fastapi.responses import JSONResponse
import os
import tempfile
import importlib.util
import sys
import json
import logging
from typing import List, Optional, Dict, Any

from core.backtest_runner import run_backtest, get_available_data_sources
from models.schemas import BacktestResult, DataSourceList, DataSourceInfo
from core.mcp_protocol import MCPRequest, MCPResponse
from adaptors.akshare import AKShareAdaptor

logger = logging.getLogger("mcp-unified-service")
akshare_adaptor = AKShareAdaptor()

router = APIRouter()

@router.post("/backtest", response_model=BacktestResult)
async def upload_and_run_backtest(
    strategy_file: UploadFile = File(...),
    data_file: Optional[UploadFile] = File(None),
    params: Optional[str] = Form(None),
    data_source: Optional[str] = Form(None),
    benchmark_symbol: Optional[str] = Form(None)
):
    """
    Upload strategy and data files, run backtest, and return metrics
    
    Args:
        strategy_file: Python file containing a Backtrader strategy class
        data_file: CSV file with price data (must have Open, High, Low, Close columns)
        params: JSON string with strategy parameters (optional)
        data_source: AkShare data source symbol (e.g., 'akshare:518880') (optional, alternative to data_file)
        benchmark_symbol: Symbol for benchmark index (e.g., '000300' for CSI 300) (optional)
    """
    try:
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save strategy file
            strategy_path = os.path.join(temp_dir, strategy_file.filename)
            with open(strategy_path, "wb") as f:
                f.write(await strategy_file.read())
            
            # Determine data source
            if data_file:
                # Save data file
                data_path = os.path.join(temp_dir, data_file.filename)
                with open(data_path, "wb") as f:
                    f.write(await data_file.read())
            elif data_source:
                # Use AkShare data source
                data_path = data_source
            else:
                raise HTTPException(status_code=400, detail="Either data_file or data_source must be provided")
            
            # Load strategy module dynamically
            spec = importlib.util.spec_from_file_location("strategy_module", strategy_path)
            strategy_module = importlib.util.module_from_spec(spec)
            sys.modules["strategy_module"] = strategy_module
            spec.loader.exec_module(strategy_module)
            
            # Find the strategy class in the module
            strategy_class = None
            for attr_name in dir(strategy_module):
                attr = getattr(strategy_module, attr_name)
                if isinstance(attr, type) and "Strategy" in attr.__name__:
                    strategy_class = attr
                    break
            
            if not strategy_class:
                raise HTTPException(status_code=400, detail="No strategy class found in uploaded file")
            
            # Run backtest
            result = run_backtest(
                strategy_class=strategy_class, 
                data_path=data_path, 
                params_str=params,
                benchmark_symbol=benchmark_symbol
            )
            
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")

@router.get("/data-sources", response_model=DataSourceList)
async def get_data_sources():
    """Get available data sources"""
    sources = get_available_data_sources()
    
    # Convert to list of DataSourceInfo objects
    source_list = []
    for key, source in sources.items():
        source_list.append(DataSourceInfo(
            name=source["name"],
            description=source["description"],
            symbols=source["symbols"]
        ))
    
    return DataSourceList(sources=source_list)

@router.post("/backtest-with-mcp", response_model=BacktestResult)
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
    Run backtest using data directly from MCP interface
    
    Args:
        strategy_file: Python file containing a Backtrader strategy class
        interface: AkShare interface name (e.g., 'stock_zh_a_hist')
        symbol: Symbol to fetch data for (e.g., '000001')
        start_date: Start date in 'YYYYMMDD' format (optional)
        end_date: End date in 'YYYYMMDD' format (optional)
        params: JSON string with strategy parameters (optional)
        benchmark_symbol: Symbol for benchmark index (e.g., '000300' for CSI 300) (optional)
    """
    try:
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save strategy file
            strategy_path = os.path.join(temp_dir, strategy_file.filename)
            with open(strategy_path, "wb") as f:
                f.write(await strategy_file.read())
            
            # Determine data source based on interface
            if interface == "stock_zh_a_hist":
                data_path = f"akshare:{symbol}"
            elif interface == "fund_etf_hist_em":
                data_path = f"akshare:{symbol}"
            elif interface == "index_zh_a_hist":
                data_path = f"akshare:{symbol}"
            else:
                # Default to stock data
                data_path = f"akshare:{symbol}"
            
            # Add date range if provided
            if start_date and end_date:
                # Convert from YYYYMMDD to YYYY-MM-DD format
                start_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
                end_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
                data_path += f":{start_fmt}:{end_fmt}"
            
            # Load strategy module dynamically
            spec = importlib.util.spec_from_file_location("strategy_module", strategy_path)
            strategy_module = importlib.util.module_from_spec(spec)
            sys.modules["strategy_module"] = strategy_module
            spec.loader.exec_module(strategy_module)
            
            # Find the strategy class in the module
            strategy_class = None
            for attr_name in dir(strategy_module):
                attr = getattr(strategy_module, attr_name)
                if isinstance(attr, type) and "Strategy" in attr.__name__:
                    strategy_class = attr
                    break
            
            if not strategy_class:
                raise HTTPException(status_code=400, detail="No strategy class found in uploaded file")
            
            # Run backtest
            result = run_backtest(
                strategy_class=strategy_class, 
                data_path=data_path, 
                params_str=params,
                benchmark_symbol=benchmark_symbol
            )
            
            return result
            
    except Exception as e:
        logger.error(f"Error running backtest with MCP data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")

@router.post("/mcp-data")
async def get_mcp_data(request: MCPRequest):
    """
    Get data from AkShare using MCP protocol for use in backtesting
    
    This endpoint allows direct access to AkShare data through the MCP protocol,
    which can then be used for backtesting.
    """
    try:
        logger.info(f"MCP数据请求: {request.interface}, 参数: {request.params}")
        
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
        logger.error(f"不支持的接口: {request.interface}, 错误: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的接口: {request.interface}"
        )
    except Exception as e:
        logger.error(f"MCP数据请求错误: {str(e)}")
        return MCPResponse(
            data=None,
            request_id=request.request_id,
            status=500,
            error=str(e)
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}