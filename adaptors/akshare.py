import akshare as ak
import pandas as pd
import asyncio
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("mcp-unified-service")

class AKShareAdaptor:
    def __init__(self, max_workers: int = 8, cache_dir: str = "static/cache"):
        self.executor = ThreadPoolExecutor(max_workers)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, method: str, params: Dict[str, Any]) -> str:
        """Creates a unique hash key for the given method and params."""
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.sha256(f"{method}:{sorted_params}".encode()).hexdigest()

    def _get_cache_ttl(self, params: Dict[str, Any]) -> timedelta:
        """Determines cache Time-To-Live based on request parameters."""
        # For historical data with a defined end date in the past, cache for longer.
        end_date_str = params.get("end_date") or params.get("date")
        if end_date_str and isinstance(end_date_str, str):
            try:
                end_date = datetime.strptime(end_date_str, "%Y%m%d")
                # Compare only the date part to avoid issues with time
                if end_date.date() < (datetime.now() - timedelta(days=1)).date():
                    return timedelta(days=30)  # Cache for 30 days for historical data
            except ValueError:
                pass  # Ignore if date format is wrong
        
        # Default cache for 1 day for recent or non-timeseries data
        return timedelta(days=1)

    async def call(self, method: str, **params) -> Any:
        """
        Executes an AKShare method with caching.
        - Checks for a valid cache entry.
        - If valid, returns cached data.
        - Otherwise, fetches from AKShare, caches the result, and returns it.
        """
        if not hasattr(ak, method):
            raise AttributeError(f"AKShare has no method: {method}")

        cache_key = self._get_cache_key(method, params)
        cache_file = self.cache_dir / f"{cache_key}.parquet"
        cache_ttl = self._get_cache_ttl(params)

        # 1. Check cache
        if cache_file.exists():
            modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - modified_time < cache_ttl:
                logger.info(f"Cache hit for method '{method}' with params {params}. Reading from '{cache_file}'.")
                try:
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(
                        self.executor,
                        lambda: pd.read_parquet(cache_file)
                    )
                except Exception as e:
                    logger.warning(f"Failed to read from cache file '{cache_file}': {e}. Fetching fresh data.")

        # 2. Fetch fresh data if cache miss or invalid
        logger.info(f"Cache miss for method '{method}'. Fetching fresh data.")
        func = getattr(ak, method)
        loop = asyncio.get_running_loop()
        
        try:
            fresh_data = await loop.run_in_executor(
                self.executor,
                lambda: func(**params)
            )
        except Exception as e:
            logger.error(f"Error calling AKShare method '{method}': {e}")
            raise  # Re-raise the exception to be handled by the caller

        # 3. Save to cache if the data is a DataFrame
        if isinstance(fresh_data, pd.DataFrame) and not fresh_data.empty:
            try:
                await loop.run_in_executor(
                    self.executor,
                    lambda: fresh_data.to_parquet(cache_file, index=False)
                )
                logger.info(f"Successfully cached data for method '{method}' to '{cache_file}'.")
            except Exception as e:
                logger.warning(f"Failed to write to cache file '{cache_file}': {e}")

        return fresh_data
