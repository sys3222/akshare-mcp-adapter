import os
import tempfile
import importlib.util
import sys
import json
import logging
from typing import Optional, Dict, Type
from fastapi import UploadFile, HTTPException

import backtrader as bt

from core.backtest_runner import run_backtest

logger = logging.getLogger("mcp-unified-service")

def _load_strategy_class(strategy_path: str) -> Type[bt.Strategy]:
    """Dynamically loads a Backtrader strategy class from a Python file."""
    try:
        spec = importlib.util.spec_from_file_location("strategy_module", strategy_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not get spec from {strategy_path}")
            
        strategy_module = importlib.util.module_from_spec(spec)
        sys.modules["strategy_module"] = strategy_module
        spec.loader.exec_module(strategy_module)
        
        # Find the strategy class in the module
        strategy_class = None
        for attr_name in dir(strategy_module):
            attr = getattr(strategy_module, attr_name)
            if isinstance(attr, type) and issubclass(attr, bt.Strategy) and attr is not bt.Strategy:
                strategy_class = attr
                break
        
        if not strategy_class:
            raise ValueError("No Backtrader strategy class found in the provided file.")
            
        return strategy_class
    except Exception as e:
        logger.error(f"Failed to load strategy from {strategy_path}: {e}")
        raise


async def handle_upload_and_run_backtest(
    strategy_file: UploadFile,
    data_file: Optional[UploadFile],
    params: Optional[str],
    data_source: Optional[str],
    benchmark_symbol: Optional[str]
):
    """Handles the logic for running a backtest from uploaded files."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            strategy_path = os.path.join(temp_dir, strategy_file.filename)
            with open(strategy_path, "wb") as f:
                f.write(await strategy_file.read())
            
            if data_file:
                data_path = os.path.join(temp_dir, data_file.filename)
                with open(data_path, "wb") as f:
                    f.write(await data_file.read())
            elif data_source:
                data_path = data_source
            else:
                raise HTTPException(status_code=400, detail="Either data_file or data_source must be provided.")
            
            strategy_class = _load_strategy_class(strategy_path)
            result = run_backtest(
                strategy_class=strategy_class,
                data_path=data_path,
                params_str=params,
                benchmark_symbol=benchmark_symbol
            )
            return result
    except Exception as e:
        logger.error(f"UNHANDLED EXCEPTION in handle_upload_and_run_backtest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


async def handle_backtest_with_code_only(
    strategy_code: str,
    symbol: str,
    start_date: Optional[str],
    end_date: Optional[str],
    params: Optional[Dict],
    benchmark_symbol: Optional[str]
):
    """Handles the logic for running a backtest from strategy code."""
    with tempfile.TemporaryDirectory() as temp_dir:
        strategy_path = os.path.join(temp_dir, "strategy.py")
        with open(strategy_path, "w") as f:
            f.write(strategy_code)
        
        # Construct data_path from AkShare parameters
        data_path = f"akshare:{symbol}"
        if start_date and end_date:
            data_path += f":{start_date}:{end_date}"
            
        params_str = json.dumps(params) if params else None
        
        try:
            strategy_class = _load_strategy_class(strategy_path)
            result = run_backtest(
                strategy_class=strategy_class,
                data_path=data_path,
                params_str=params_str,
                benchmark_symbol=benchmark_symbol
            )
            return result
        except Exception as e:
            logger.error(f"Error during code-based backtest execution: {e}")
            raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")

async def handle_backtest_with_mcp_data(
    strategy_file: UploadFile,
    interface: str,
    symbol: str,
    start_date: Optional[str],
    end_date: Optional[str],
    params: Optional[str],
    benchmark_symbol: Optional[str]
):
    """Handles the logic for running a backtest using data from MCP interface."""
    with tempfile.TemporaryDirectory() as temp_dir:
        strategy_path = os.path.join(temp_dir, strategy_file.filename)
        with open(strategy_path, "wb") as f:
            f.write(await strategy_file.read())

        data_path = f"akshare:{symbol}"
        if start_date and end_date:
            start_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
            end_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
            data_path += f":{start_fmt}:{end_fmt}"

        try:
            strategy_class = _load_strategy_class(strategy_path)
            result = run_backtest(
                strategy_class=strategy_class,
                data_path=data_path,
                params_str=params,
                benchmark_symbol=benchmark_symbol
            )
            return result
        except Exception as e:
            logger.error(f"Error during MCP-based backtest execution: {e}")
            raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")
