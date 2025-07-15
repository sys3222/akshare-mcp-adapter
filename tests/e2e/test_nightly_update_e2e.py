"""
夜间缓存更新的端到端测试
测试完整的夜间更新流程，包括脚本执行、缓存生成、API访问等
"""

import pytest
import asyncio
import subprocess
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import patch, Mock

import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from main import app
from create_user import create_user
from core.database import SessionLocal, create_db_and_tables
from tests.test_data.mock_akshare_data import get_mock_data

class TestNightlyUpdateE2E:
    
    @pytest.fixture(scope="class")
    def test_environment(self):
        """设置测试环境"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        cache_dir = Path(temp_dir) / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试配置
        config_dir = Path(temp_dir) / "scripts"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        test_config = {
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
        
        config_file = config_dir / "nightly_update_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        
        yield {
            "temp_dir": temp_dir,
            "cache_dir": cache_dir,
            "config_file": config_file
        }
        
        # 清理
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def client_with_auth(self):
        """创建带认证的测试客户端"""
        # 确保数据库和表存在
        create_db_and_tables()
        
        # 创建测试用户
        db = SessionLocal()
        try:
            create_user(db, "e2e_testuser", "e2e_testpass")
        except Exception:
            pass  # 用户可能已存在
        finally:
            db.close()
        
        client = TestClient(app)
        
        # 获取认证token
        response = client.post("/api/token", data={
            "username": "e2e_testuser", 
            "password": "e2e_testpass"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        return client, {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_full_nightly_update_workflow(self, test_environment):
        """测试完整的夜间更新工作流程"""
        
        temp_dir = test_environment["temp_dir"]
        cache_dir = test_environment["cache_dir"]
        config_file = test_environment["config_file"]
        
        # 保存原始工作目录
        original_cwd = os.getcwd()
        
        try:
            # 切换到测试目录
            os.chdir(temp_dir)
            
            # 导入并运行更新器
            from scripts.nightly_cache_update import NightlyCacheUpdater
            
            # 创建更新器
            updater = NightlyCacheUpdater(cache_dir=str(cache_dir))
            
            # Mock AkShare调用
            mock_data = get_mock_data("index_zh_a_hist", 
                                    symbol="000001", 
                                    start_date="20240101", 
                                    end_date="20240103")
            
            with patch.object(updater.adaptor, 'call') as mock_call:
                mock_call.return_value = mock_data
                
                # 执行完整更新
                result = await updater.run_full_update()
                
                # 验证更新成功
                assert result is True
                
                # 验证缓存文件生成
                cache_files = list(cache_dir.glob("*.parquet"))
                assert len(cache_files) > 0
                
                # 验证缓存文件内容
                import pandas as pd
                cached_data = pd.read_parquet(cache_files[0])
                assert not cached_data.empty
                assert len(cached_data) == len(mock_data)
        
        finally:
            os.chdir(original_cwd)
    
    def test_cache_status_api_integration(self, test_environment, client_with_auth):
        """测试缓存状态API与实际缓存文件的集成"""
        
        client, auth_headers = client_with_auth
        cache_dir = test_environment["cache_dir"]
        
        # 创建一些测试缓存文件
        test_file = cache_dir / "test_integration.parquet"
        test_content = b"test parquet data for integration"
        test_file.write_bytes(test_content)
        
        # 临时修改缓存目录路径
        with patch('api.routes.Path') as mock_path:
            mock_path.return_value = cache_dir
            
            response = client.get("/api/cache/status", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["total_files"] == 1
            assert data["total_size_mb"] > 0
            assert len(data["files"]) == 1
            assert data["files"][0]["filename"] == "test_integration.parquet"
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, test_environment):
        """测试错误恢复工作流程"""
        
        temp_dir = test_environment["temp_dir"]
        cache_dir = test_environment["cache_dir"]
        
        original_cwd = os.getcwd()
        
        try:
            os.chdir(temp_dir)
            
            from scripts.nightly_cache_update import NightlyCacheUpdater
            
            updater = NightlyCacheUpdater(cache_dir=str(cache_dir))
            
            # Mock第一次失败，第二次成功
            mock_data = get_mock_data("index_zh_a_hist")
            
            with patch.object(updater.adaptor, 'call') as mock_call:
                mock_call.side_effect = [Exception("网络错误"), mock_data]
                
                # 执行单个接口更新（应该重试成功）
                interface_config = {
                    "interface": "index_zh_a_hist",
                    "params": {"symbol": "000001"},
                    "description": "测试接口"
                }
                
                result = await updater.update_single_interface(interface_config)
                
                # 验证重试成功
                assert result is True
                assert mock_call.call_count == 2
        
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_cache_cleanup_workflow(self, test_environment):
        """测试缓存清理工作流程"""
        
        temp_dir = test_environment["temp_dir"]
        cache_dir = test_environment["cache_dir"]
        
        # 创建新旧缓存文件
        new_file = cache_dir / "new_cache.parquet"
        old_file = cache_dir / "old_cache.parquet"
        
        new_file.write_bytes(b"new data")
        old_file.write_bytes(b"old data")
        
        # 设置旧文件的修改时间为8天前
        from datetime import datetime, timedelta
        old_time = (datetime.now() - timedelta(days=8)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        original_cwd = os.getcwd()
        
        try:
            os.chdir(temp_dir)
            
            from scripts.nightly_cache_update import NightlyCacheUpdater
            
            updater = NightlyCacheUpdater(cache_dir=str(cache_dir))
            
            # 执行清理（保留7天内的文件）
            await updater.cleanup_old_cache(days_to_keep=7)
            
            # 验证新文件保留，旧文件删除
            assert new_file.exists()
            assert not old_file.exists()
        
        finally:
            os.chdir(original_cwd)
    
    def test_script_execution_via_subprocess(self, test_environment):
        """测试通过subprocess执行脚本"""
        
        temp_dir = test_environment["temp_dir"]
        cache_dir = test_environment["cache_dir"]
        
        # 创建简化的脚本用于测试
        test_script = Path(temp_dir) / "test_update.py"
        script_content = f'''
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, "{project_root}")
os.chdir("{temp_dir}")

from scripts.nightly_cache_update import NightlyCacheUpdater
from unittest.mock import patch
from tests.test_data.mock_akshare_data import get_mock_data
import asyncio

async def main():
    updater = NightlyCacheUpdater(cache_dir="{cache_dir}")
    
    # Mock数据
    mock_data = get_mock_data("index_zh_a_hist")
    
    with patch.object(updater.adaptor, 'call') as mock_call:
        mock_call.return_value = mock_data
        result = await updater.run_daily_updates()
        print(f"SUCCESS: {{result[0]}}/{{result[1]}}")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        test_script.write_text(script_content)
        
        # 执行脚本
        result = subprocess.run([
            sys.executable, str(test_script)
        ], capture_output=True, text=True, timeout=30)
        
        # 验证脚本执行成功
        assert result.returncode == 0
        assert "SUCCESS: 1/1" in result.stdout
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, test_environment):
        """测试并发缓存访问"""
        
        temp_dir = test_environment["temp_dir"]
        cache_dir = test_environment["cache_dir"]
        
        original_cwd = os.getcwd()
        
        try:
            os.chdir(temp_dir)
            
            from scripts.nightly_cache_update import NightlyCacheUpdater
            from adaptors.akshare import AKShareAdaptor
            
            # 创建多个更新器实例
            updater1 = NightlyCacheUpdater(cache_dir=str(cache_dir))
            adaptor2 = AKShareAdaptor(cache_dir=str(cache_dir))
            
            mock_data = get_mock_data("index_zh_a_hist")
            
            # 并发访问同一缓存
            async def update_task():
                with patch.object(updater1.adaptor, 'call') as mock_call:
                    mock_call.return_value = mock_data
                    return await updater1.run_daily_updates()
            
            async def read_task():
                with patch('akshare.index_zh_a_hist', return_value=mock_data):
                    return await adaptor2.call("index_zh_a_hist", symbol="000001")
            
            # 并发执行
            update_result, read_result = await asyncio.gather(
                update_task(), read_task()
            )
            
            # 验证两个任务都成功
            assert update_result[0] > 0  # 至少一个更新成功
            assert read_result is not None
        
        finally:
            os.chdir(original_cwd)
