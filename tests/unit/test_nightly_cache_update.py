"""
夜间缓存更新功能的单元测试
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.nightly_cache_update import NightlyCacheUpdater
from tests.test_data.mock_akshare_data import get_mock_data

class TestNightlyCacheUpdater:
    
    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_config(self):
        """测试配置"""
        return {
            "daily_updates": [
                {
                    "interface": "index_zh_a_hist",
                    "params": {
                        "symbol": "000001",
                        "period": "daily",
                        "start_date": "20240101",
                        "end_date": "20240107"
                    },
                    "description": "上证指数测试数据"
                }
            ],
            "weekly_updates": [
                {
                    "interface": "stock_zh_a_hist",
                    "params": {
                        "symbol": "600519",
                        "period": "daily",
                        "start_date": "20240101",
                        "end_date": "20240131"
                    },
                    "description": "贵州茅台测试数据"
                }
            ],
            "cache_settings": {
                "cleanup_days": 7,
                "max_file_size_mb": 10,
                "retry_attempts": 2,
                "retry_delay_seconds": 0.1
            }
        }
    
    @pytest.fixture
    def mock_updater(self, temp_cache_dir, test_config):
        """创建Mock的更新器"""
        with patch('scripts.nightly_cache_update.Path') as mock_path:
            # Mock配置文件存在
            mock_config_file = Mock()
            mock_config_file.exists.return_value = True
            mock_path.return_value = mock_config_file
            
            with patch('builtins.open', mock_open_with_json(test_config)):
                updater = NightlyCacheUpdater(cache_dir=temp_cache_dir)
                return updater
    
    def test_init(self, temp_cache_dir):
        """测试初始化"""
        updater = NightlyCacheUpdater(cache_dir=temp_cache_dir)
        
        assert updater.cache_dir.exists()
        assert updater.update_config is not None
        assert "daily_updates" in updater.update_config
        assert "weekly_updates" in updater.update_config
    
    def test_load_default_config(self, temp_cache_dir):
        """测试加载默认配置"""
        with patch('scripts.nightly_cache_update.Path') as mock_path:
            mock_config_file = Mock()
            mock_config_file.exists.return_value = False
            mock_path.return_value = mock_config_file
            
            updater = NightlyCacheUpdater(cache_dir=temp_cache_dir)
            
            assert "daily_updates" in updater.update_config
            assert "weekly_updates" in updater.update_config
            assert len(updater.update_config["daily_updates"]) > 0
    
    @pytest.mark.asyncio
    async def test_update_single_interface_success(self, mock_updater):
        """测试单个接口更新成功"""
        interface_config = {
            "interface": "index_zh_a_hist",
            "params": {"symbol": "000001", "start_date": "20240101", "end_date": "20240107"},
            "description": "测试接口"
        }
        
        # Mock AkShare适配器
        mock_data = get_mock_data("index_zh_a_hist", **interface_config["params"])
        mock_updater.adaptor.call = AsyncMock(return_value=mock_data)
        
        result = await mock_updater.update_single_interface(interface_config)
        
        assert result is True
        mock_updater.adaptor.call.assert_called_once_with(
            "index_zh_a_hist", **interface_config["params"]
        )
    
    @pytest.mark.asyncio
    async def test_update_single_interface_empty_data(self, mock_updater):
        """测试接口返回空数据"""
        interface_config = {
            "interface": "test_interface",
            "params": {},
            "description": "测试接口"
        }
        
        # Mock返回空数据
        mock_updater.adaptor.call = AsyncMock(return_value=None)
        
        result = await mock_updater.update_single_interface(interface_config)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_single_interface_with_retry(self, mock_updater):
        """测试接口更新重试机制"""
        interface_config = {
            "interface": "test_interface",
            "params": {},
            "description": "测试接口"
        }
        
        # Mock第一次失败，第二次成功
        mock_data = get_mock_data("index_zh_a_hist")
        mock_updater.adaptor.call = AsyncMock(side_effect=[Exception("网络错误"), mock_data])
        
        result = await mock_updater.update_single_interface(interface_config)
        
        assert result is True
        assert mock_updater.adaptor.call.call_count == 2
    
    @pytest.mark.asyncio
    async def test_update_single_interface_max_retries(self, mock_updater):
        """测试达到最大重试次数"""
        interface_config = {
            "interface": "test_interface",
            "params": {},
            "description": "测试接口"
        }
        
        # Mock总是失败
        mock_updater.adaptor.call = AsyncMock(side_effect=Exception("持续错误"))
        
        result = await mock_updater.update_single_interface(interface_config)
        
        assert result is False
        assert mock_updater.adaptor.call.call_count == 2  # retry_attempts = 2
    
    @pytest.mark.asyncio
    async def test_run_daily_updates(self, mock_updater):
        """测试每日更新"""
        # Mock成功的接口调用
        mock_data = get_mock_data("index_zh_a_hist")
        mock_updater.adaptor.call = AsyncMock(return_value=mock_data)
        
        success_count, total_count = await mock_updater.run_daily_updates()
        
        assert success_count == 1
        assert total_count == 1
        assert mock_updater.adaptor.call.call_count == 1
    
    @pytest.mark.asyncio
    async def test_run_weekly_updates_not_sunday(self, mock_updater):
        """测试非周日不执行周更新"""
        with patch('scripts.nightly_cache_update.datetime') as mock_datetime:
            # Mock当前是周一 (weekday = 0)
            mock_datetime.now.return_value.weekday.return_value = 0
            
            success_count, total_count = await mock_updater.run_weekly_updates()
            
            assert success_count == 0
            assert total_count == 0
    
    @pytest.mark.asyncio
    async def test_run_weekly_updates_sunday(self, mock_updater):
        """测试周日执行周更新"""
        with patch('scripts.nightly_cache_update.datetime') as mock_datetime:
            # Mock当前是周日 (weekday = 6)
            mock_datetime.now.return_value.weekday.return_value = 6
            
            # Mock成功的接口调用
            mock_data = get_mock_data("stock_zh_a_hist")
            mock_updater.adaptor.call = AsyncMock(return_value=mock_data)
            
            success_count, total_count = await mock_updater.run_weekly_updates()
            
            assert success_count == 1
            assert total_count == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_old_cache(self, mock_updater, temp_cache_dir):
        """测试清理过期缓存"""
        # 创建一些测试缓存文件
        cache_dir = Path(temp_cache_dir)
        
        # 创建新文件
        new_file = cache_dir / "new_cache.parquet"
        new_file.touch()
        
        # 创建旧文件
        old_file = cache_dir / "old_cache.parquet"
        old_file.touch()
        
        # 设置旧文件的修改时间为8天前
        old_time = (datetime.now() - timedelta(days=8)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        await mock_updater.cleanup_old_cache(days_to_keep=7)
        
        # 检查新文件还在，旧文件被删除
        assert new_file.exists()
        assert not old_file.exists()


def mock_open_with_json(json_data):
    """创建返回JSON数据的mock open函数"""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(json_data))
