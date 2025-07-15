"""
夜间缓存更新的集成测试
测试与真实AkShare适配器的集成
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock

import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.nightly_cache_update import NightlyCacheUpdater
from adaptors.akshare import AKShareAdaptor
from tests.test_data.mock_akshare_data import get_mock_data

class TestNightlyCacheIntegration:
    
    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_config_file(self, temp_cache_dir):
        """创建测试配置文件"""
        config = {
            "daily_updates": [
                {
                    "interface": "index_zh_a_hist",
                    "params": {
                        "symbol": "000001",
                        "period": "daily",
                        "start_date": "20240101",
                        "end_date": "20240103"
                    },
                    "description": "上证指数测试数据"
                }
            ],
            "weekly_updates": [],
            "cache_settings": {
                "cleanup_days": 7,
                "max_file_size_mb": 10,
                "retry_attempts": 1,
                "retry_delay_seconds": 0.1
            }
        }
        
        config_dir = Path(temp_cache_dir) / "scripts"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "nightly_update_config.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return config_file
    
    @pytest.mark.asyncio
    async def test_full_update_with_mock_adaptor(self, temp_cache_dir, test_config_file):
        """测试完整更新流程（使用Mock适配器）"""
        
        # 修改工作目录以使用测试配置
        original_cwd = os.getcwd()
        test_project_dir = test_config_file.parent.parent
        
        try:
            os.chdir(test_project_dir)
            
            # 创建更新器
            updater = NightlyCacheUpdater(cache_dir=temp_cache_dir)
            
            # Mock AkShare适配器的call方法
            mock_data = get_mock_data("index_zh_a_hist", 
                                    symbol="000001", 
                                    start_date="20240101", 
                                    end_date="20240103")
            
            with patch.object(updater.adaptor, 'call', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = mock_data
                
                # 执行完整更新
                result = await updater.run_full_update()
                
                assert result is True
                mock_call.assert_called()
                
                # 检查缓存目录中是否有文件生成
                cache_files = list(Path(temp_cache_dir).glob("*.parquet"))
                assert len(cache_files) > 0
        
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_cache_file_creation(self, temp_cache_dir):
        """测试缓存文件创建"""
        
        # 创建AkShare适配器
        adaptor = AKShareAdaptor(cache_dir=temp_cache_dir)
        
        # Mock akshare调用
        mock_data = get_mock_data("index_zh_a_hist", 
                                symbol="000001", 
                                start_date="20240101", 
                                end_date="20240103")
        
        with patch('akshare.index_zh_a_hist', return_value=mock_data):
            # 调用适配器
            result = await adaptor.call("index_zh_a_hist", 
                                      symbol="000001", 
                                      period="daily",
                                      start_date="20240101", 
                                      end_date="20240103")
            
            assert result is not None
            assert not result.empty
            
            # 检查缓存文件是否创建
            cache_files = list(Path(temp_cache_dir).glob("*.parquet"))
            assert len(cache_files) == 1
            
            # 验证缓存文件内容
            import pandas as pd
            cached_data = pd.read_parquet(cache_files[0])
            assert len(cached_data) == len(mock_data)
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, temp_cache_dir):
        """测试缓存命中性能"""
        
        adaptor = AKShareAdaptor(cache_dir=temp_cache_dir)
        mock_data = get_mock_data("index_zh_a_hist")
        
        params = {
            "symbol": "000001",
            "period": "daily", 
            "start_date": "20240101",
            "end_date": "20240103"
        }
        
        with patch('akshare.index_zh_a_hist', return_value=mock_data) as mock_akshare:
            # 第一次调用 - 应该调用AkShare
            result1 = await adaptor.call("index_zh_a_hist", **params)
            assert mock_akshare.call_count == 1
            
            # 第二次调用 - 应该从缓存读取
            result2 = await adaptor.call("index_zh_a_hist", **params)
            assert mock_akshare.call_count == 1  # 没有增加
            
            # 验证结果一致
            import pandas as pd
            pd.testing.assert_frame_equal(result1, result2)
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, temp_cache_dir):
        """测试错误处理集成"""
        
        updater = NightlyCacheUpdater(cache_dir=temp_cache_dir)
        
        # 配置一个会失败的接口
        interface_config = {
            "interface": "non_existent_interface",
            "params": {},
            "description": "不存在的接口"
        }
        
        # 应该优雅地处理错误
        result = await updater.update_single_interface(interface_config)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_updates(self, temp_cache_dir):
        """测试并发更新"""
        
        updater = NightlyCacheUpdater(cache_dir=temp_cache_dir)
        
        # 创建多个接口配置
        configs = [
            {
                "interface": "index_zh_a_hist",
                "params": {"symbol": "000001", "start_date": "20240101", "end_date": "20240103"},
                "description": "上证指数"
            },
            {
                "interface": "index_zh_a_hist", 
                "params": {"symbol": "000300", "start_date": "20240101", "end_date": "20240103"},
                "description": "沪深300"
            }
        ]
        
        # Mock数据
        mock_data = get_mock_data("index_zh_a_hist")
        
        with patch.object(updater.adaptor, 'call', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_data
            
            # 并发执行更新
            tasks = [updater.update_single_interface(config) for config in configs]
            results = await asyncio.gather(*tasks)
            
            # 所有更新都应该成功
            assert all(results)
            assert mock_call.call_count == len(configs)
    
    def test_config_validation(self, temp_cache_dir):
        """测试配置验证"""
        
        # 测试无效配置文件
        invalid_config_dir = Path(temp_cache_dir) / "scripts"
        invalid_config_dir.mkdir(parents=True, exist_ok=True)
        invalid_config_file = invalid_config_dir / "nightly_update_config.json"
        
        # 写入无效JSON
        with open(invalid_config_file, 'w') as f:
            f.write("invalid json content")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(invalid_config_file.parent.parent)
            
            # 应该回退到默认配置
            updater = NightlyCacheUpdater(cache_dir=temp_cache_dir)
            assert "daily_updates" in updater.update_config
            assert "weekly_updates" in updater.update_config
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self, temp_cache_dir):
        """测试大数据处理"""
        
        adaptor = AKShareAdaptor(cache_dir=temp_cache_dir)
        
        # 生成大量数据
        import pandas as pd
        import numpy as np
        
        large_data = pd.DataFrame({
            '日期': pd.date_range('2020-01-01', periods=1000),
            '开盘': np.random.rand(1000) * 100,
            '收盘': np.random.rand(1000) * 100,
            '最高': np.random.rand(1000) * 100,
            '最低': np.random.rand(1000) * 100,
            '成交量': np.random.randint(1000000, 10000000, 1000)
        })
        
        with patch('akshare.stock_zh_a_hist', return_value=large_data):
            result = await adaptor.call("stock_zh_a_hist", 
                                      symbol="000001",
                                      period="daily")
            
            assert result is not None
            assert len(result) == 1000
            
            # 验证缓存文件大小合理
            cache_files = list(Path(temp_cache_dir).glob("*.parquet"))
            assert len(cache_files) == 1
            
            file_size_mb = cache_files[0].stat().st_size / 1024 / 1024
            assert file_size_mb < 50  # 应该小于50MB
