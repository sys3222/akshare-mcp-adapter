from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from fastapi.responses import JSONResponse
import os
import tempfile
import importlib.util
import sys
from typing import List, Optional, Dict, Any

from core.backtest_runner import run_backtest, get_available_data_sources
from models.schemas import BacktestResult, DataSourceList, DataSourceInfo

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

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}