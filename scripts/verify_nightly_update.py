#!/usr/bin/env python3
"""
验证夜间缓存更新功能
快速验证脚本是否可以正常工作
"""

import asyncio
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from scripts.nightly_cache_update import NightlyCacheUpdater
        from adaptors.akshare import AKShareAdaptor
        from tests.test_data.mock_akshare_data import get_mock_data
        print("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_mock_data_generation():
    """测试Mock数据生成"""
    print("\n🔍 测试Mock数据生成...")
    
    try:
        from tests.test_data.mock_akshare_data import get_mock_data
        
        # 测试不同类型的数据生成
        stock_data = get_mock_data("stock_zh_a_hist", symbol="000001", start_date="20240101", end_date="20240107")
        index_data = get_mock_data("index_zh_a_hist", symbol="000001", start_date="20240101", end_date="20240107")
        spot_data = get_mock_data("stock_zh_a_spot_em")
        
        assert not stock_data.empty, "股票数据不应为空"
        assert not index_data.empty, "指数数据不应为空"
        assert not spot_data.empty, "实时数据不应为空"
        
        print(f"✅ Mock数据生成成功:")
        print(f"   - 股票数据: {len(stock_data)} 行")
        print(f"   - 指数数据: {len(index_data)} 行")
        print(f"   - 实时数据: {len(spot_data)} 行")
        return True
        
    except Exception as e:
        print(f"❌ Mock数据生成失败: {e}")
        return False

async def test_cache_updater():
    """测试缓存更新器"""
    print("\n🔍 测试缓存更新器...")
    
    try:
        from scripts.nightly_cache_update import NightlyCacheUpdater
        from tests.test_data.mock_akshare_data import get_mock_data
        
        # 创建临时缓存目录
        with tempfile.TemporaryDirectory() as temp_dir:
            updater = NightlyCacheUpdater(cache_dir=temp_dir)
            
            # 测试配置加载
            assert updater.update_config is not None, "配置应该被加载"
            assert "daily_updates" in updater.update_config, "应该有每日更新配置"
            
            # Mock数据
            mock_data = get_mock_data("index_zh_a_hist", symbol="000001", start_date="20240101", end_date="20240107")
            
            # 测试单个接口更新
            with patch.object(updater.adaptor, 'call') as mock_call:
                mock_call.return_value = mock_data
                
                interface_config = {
                    "interface": "index_zh_a_hist",
                    "params": {"symbol": "000001", "start_date": "20240101", "end_date": "20240107"},
                    "description": "测试接口"
                }
                
                result = await updater.update_single_interface(interface_config)
                assert result is True, "单个接口更新应该成功"
                
                # 验证调用
                mock_call.assert_called_once()
            
            print("✅ 缓存更新器测试成功")
            return True
            
    except Exception as e:
        print(f"❌ 缓存更新器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_daily_updates():
    """测试每日更新流程"""
    print("\n🔍 测试每日更新流程...")
    
    try:
        from scripts.nightly_cache_update import NightlyCacheUpdater
        from tests.test_data.mock_akshare_data import get_mock_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            updater = NightlyCacheUpdater(cache_dir=temp_dir)
            
            # Mock所有可能的接口调用
            mock_data = get_mock_data("index_zh_a_hist")
            
            with patch.object(updater.adaptor, 'call') as mock_call:
                mock_call.return_value = mock_data
                
                # 执行每日更新
                success_count, total_count = await updater.run_daily_updates()
                
                assert total_count > 0, "应该有要更新的接口"
                assert success_count > 0, "至少应该有一个接口更新成功"
                
                print(f"✅ 每日更新测试成功: {success_count}/{total_count} 接口更新成功")
                return True
                
    except Exception as e:
        print(f"❌ 每日更新测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_cleanup():
    """测试缓存清理"""
    print("\n🔍 测试缓存清理...")
    
    try:
        from scripts.nightly_cache_update import NightlyCacheUpdater
        from datetime import datetime, timedelta
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            updater = NightlyCacheUpdater(cache_dir=temp_dir)
            
            # 创建测试文件
            new_file = cache_dir / "new_cache.parquet"
            old_file = cache_dir / "old_cache.parquet"
            
            new_file.write_bytes(b"new data")
            old_file.write_bytes(b"old data")
            
            # 设置旧文件的修改时间
            old_time = (datetime.now() - timedelta(days=8)).timestamp()
            os.utime(old_file, (old_time, old_time))
            
            # 执行清理
            await updater.cleanup_old_cache(days_to_keep=7)
            
            # 验证结果
            assert new_file.exists(), "新文件应该保留"
            assert not old_file.exists(), "旧文件应该被删除"
            
            print("✅ 缓存清理测试成功")
            return True
            
    except Exception as e:
        print(f"❌ 缓存清理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_workflow():
    """测试完整工作流程"""
    print("\n🔍 测试完整工作流程...")
    
    try:
        from scripts.nightly_cache_update import NightlyCacheUpdater
        from tests.test_data.mock_akshare_data import get_mock_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            updater = NightlyCacheUpdater(cache_dir=temp_dir)
            
            # Mock数据
            mock_data = get_mock_data("index_zh_a_hist")
            
            with patch.object(updater.adaptor, 'call') as mock_call:
                mock_call.return_value = mock_data
                
                # 执行完整更新
                result = await updater.run_full_update()
                
                assert result is True, "完整更新应该成功"
                
                print("✅ 完整工作流程测试成功")
                return True
                
    except Exception as e:
        print(f"❌ 完整工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🚀 开始验证夜间缓存更新功能")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("Mock数据生成", test_mock_data_generation),
        ("缓存更新器", test_cache_updater),
        ("每日更新流程", test_daily_updates),
        ("缓存清理", test_cache_cleanup),
        ("完整工作流程", test_full_workflow)
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                success_count += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 所有验证通过！夜间缓存更新功能正常工作。")
        return 0
    else:
        print(f"\n⚠️ {total_count - success_count} 个验证失败")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
