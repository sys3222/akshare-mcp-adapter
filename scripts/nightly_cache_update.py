#!/usr/bin/env python3
"""
夜间数据缓存更新脚本
每天凌晨自动更新常用的金融数据到本地缓存
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 确保工作目录是项目根目录
os.chdir(project_root)

try:
    from adaptors.akshare import AKShareAdaptor
    from core.mcp_protocol import MCPRequest
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path}")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nightly_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("nightly-cache-update")

class NightlyCacheUpdater:
    def __init__(self, cache_dir="static/cache/system"):
        # 确保缓存目录存在
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

        self.adaptor = AKShareAdaptor(cache_dir=cache_dir)
        self.update_config = self._load_update_config()
        self.cache_dir = cache_path

    def _load_update_config(self):
        """加载需要更新的数据配置"""
        config_file = Path("scripts/nightly_update_config.json")
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"加载配置文件: {config_file}")
                    return config
            else:
                logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")

        # 默认配置 - 使用简单的测试数据
        today = datetime.now()
        start_date = (today - timedelta(days=7)).strftime("%Y%m%d")  # 最近7天
        end_date = today.strftime("%Y%m%d")

        return {
            "daily_updates": [
                {
                    "interface": "index_zh_a_hist",
                    "params": {
                        "symbol": "000001",
                        "period": "daily",
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "description": "上证指数近7天数据"
                },
                {
                    "interface": "index_zh_a_hist",
                    "params": {
                        "symbol": "000300",
                        "period": "daily",
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "description": "沪深300指数近7天数据"
                }
            ],
            "weekly_updates": [
                {
                    "interface": "stock_zh_a_hist",
                    "params": {
                        "symbol": "000001",
                        "period": "daily",
                        "start_date": (today - timedelta(days=30)).strftime("%Y%m%d"),
                        "end_date": end_date
                    },
                    "description": "平安银行近30天数据"
                }
            ],
            "cache_settings": {
                "cleanup_days": 30,
                "max_file_size_mb": 50,
                "retry_attempts": 3,
                "retry_delay_seconds": 5
            }
        }
    
    async def update_single_interface(self, interface_config):
        """更新单个接口数据，带重试机制"""
        interface = interface_config["interface"]
        params = interface_config["params"]
        description = interface_config.get("description", interface)

        cache_settings = self.update_config.get("cache_settings", {})
        retry_attempts = cache_settings.get("retry_attempts", 3)
        retry_delay = cache_settings.get("retry_delay_seconds", 5)

        for attempt in range(retry_attempts):
            try:
                if attempt > 0:
                    logger.info(f"重试第 {attempt} 次: {description}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.info(f"开始更新: {description} ({interface})")

                # 调用AkShare接口
                result = await self.adaptor.call(interface, **params)

                if result is not None and not (hasattr(result, 'empty') and result.empty):
                    data_size = len(result) if hasattr(result, '__len__') else 1
                    logger.info(f"✅ 成功更新: {description} (数据量: {data_size})")
                    return True
                else:
                    logger.warning(f"⚠️ 数据为空: {description}")
                    if attempt == retry_attempts - 1:
                        return False

            except Exception as e:
                logger.error(f"❌ 更新失败 (尝试 {attempt + 1}/{retry_attempts}): {description} - {str(e)}")
                if attempt == retry_attempts - 1:
                    return False

        return False
    
    async def run_daily_updates(self):
        """执行每日更新"""
        logger.info("=== 开始每日数据更新 ===")
        
        daily_configs = self.update_config.get("daily_updates", [])
        success_count = 0
        total_count = len(daily_configs)
        
        for config in daily_configs:
            success = await self.update_single_interface(config)
            if success:
                success_count += 1
            
            # 避免请求过于频繁
            await asyncio.sleep(2)
        
        logger.info(f"=== 每日更新完成: {success_count}/{total_count} 成功 ===")
        return success_count, total_count
    
    async def run_weekly_updates(self):
        """执行每周更新（仅周日执行）"""
        if datetime.now().weekday() != 6:  # 0=Monday, 6=Sunday
            logger.info("今天不是周日，跳过周更新")
            return 0, 0
            
        logger.info("=== 开始每周数据更新 ===")
        
        weekly_configs = self.update_config.get("weekly_updates", [])
        success_count = 0
        total_count = len(weekly_configs)
        
        for config in weekly_configs:
            success = await self.update_single_interface(config)
            if success:
                success_count += 1
            
            # 周更新间隔更长
            await asyncio.sleep(5)
        
        logger.info(f"=== 每周更新完成: {success_count}/{total_count} 成功 ===")
        return success_count, total_count
    
    async def cleanup_old_cache(self, days_to_keep=30):
        """清理过期缓存文件"""
        logger.info(f"=== 开始清理 {days_to_keep} 天前的缓存文件 ===")

        # 使用实例的缓存目录
        if not self.cache_dir.exists():
            logger.info("缓存目录不存在，跳过清理")
            return

        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0

        for cache_file in self.cache_dir.glob("*.parquet"):
            try:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_time < cutoff_time:
                    cache_file.unlink()
                    deleted_count += 1
                    logger.debug(f"删除过期缓存: {cache_file.name}")
            except Exception as e:
                logger.warning(f"删除缓存文件失败 {cache_file.name}: {e}")

        logger.info(f"=== 缓存清理完成: 删除了 {deleted_count} 个过期文件 ===")
    
    async def run_full_update(self):
        """执行完整的夜间更新流程"""
        start_time = datetime.now()
        logger.info(f"🌙 夜间缓存更新开始: {start_time}")
        
        try:
            # 1. 每日更新
            daily_success, daily_total = await self.run_daily_updates()
            
            # 2. 每周更新
            weekly_success, weekly_total = await self.run_weekly_updates()
            
            # 3. 清理过期缓存
            await self.cleanup_old_cache()
            
            # 4. 总结
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"🎉 夜间更新完成!")
            logger.info(f"   耗时: {duration}")
            logger.info(f"   每日更新: {daily_success}/{daily_total}")
            logger.info(f"   每周更新: {weekly_success}/{weekly_total}")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 夜间更新失败: {str(e)}", exc_info=True)
            return False

async def main():
    """主函数"""
    updater = NightlyCacheUpdater()
    success = await updater.run_full_update()
    
    # 退出码：0表示成功，1表示失败
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
