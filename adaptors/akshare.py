import akshare as ak
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor
import asyncio

class AKShareAdaptor:
    def __init__(self, max_workers: int = 8):
        self.executor = ThreadPoolExecutor(max_workers)
        
    async def call(self, method: str, **params) -> Any:
        """执行AKShare方法（同步转异步）"""
        if not hasattr(ak, method):
            raise AttributeError(f"AKShare has no method: {method}")
            
        func = getattr(ak, method)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: func(**params)
        )
