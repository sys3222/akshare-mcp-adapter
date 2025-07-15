#!/usr/bin/env python3
"""
测试运行脚本
运行夜间缓存更新相关的所有测试
"""

import subprocess
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"命令: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.stdout:
            print("📤 标准输出:")
            print(result.stdout)
        
        if result.stderr:
            print("📤 标准错误:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            return True
        else:
            print(f"❌ {description} - 失败 (退出码: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 超时")
        return False
    except Exception as e:
        print(f"💥 {description} - 异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始运行夜间缓存更新测试套件")
    
    # 测试命令列表
    test_commands = [
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/unit/test_nightly_cache_update.py", "-v"],
            "description": "单元测试 - 夜间缓存更新"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/integration/test_nightly_cache_integration.py", "-v"],
            "description": "集成测试 - 夜间缓存更新"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/test_api.py::test_cache_status_unauthenticated", "-v"],
            "description": "API测试 - 缓存状态认证"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/test_api.py::test_cache_status_empty_cache", "-v"],
            "description": "API测试 - 空缓存状态"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/test_api.py::test_cache_status_with_files", "-v"],
            "description": "API测试 - 有文件的缓存状态"
        },
        {
            "cmd": [sys.executable, "-m", "pytest", "tests/e2e/test_nightly_update_e2e.py", "-v", "-s"],
            "description": "端到端测试 - 完整流程"
        }
    ]
    
    # 运行测试
    success_count = 0
    total_count = len(test_commands)
    
    for test_config in test_commands:
        success = run_command(test_config["cmd"], test_config["description"])
        if success:
            success_count += 1
    
    # 总结
    print(f"\n{'='*60}")
    print(f"📊 测试总结")
    print(f"{'='*60}")
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1

def test_nightly_script_directly():
    """直接测试夜间更新脚本"""
    print(f"\n{'='*60}")
    print(f"🌙 直接测试夜间更新脚本")
    print(f"{'='*60}")
    
    try:
        # 导入并运行更新器
        from scripts.nightly_cache_update import NightlyCacheUpdater
        from tests.test_data.mock_akshare_data import get_mock_data
        from unittest.mock import patch
        import asyncio
        import tempfile
        
        async def test_run():
            with tempfile.TemporaryDirectory() as temp_dir:
                updater = NightlyCacheUpdater(cache_dir=temp_dir)
                
                # Mock数据
                mock_data = get_mock_data("index_zh_a_hist")
                
                with patch.object(updater.adaptor, 'call') as mock_call:
                    mock_call.return_value = mock_data
                    
                    # 测试单个接口更新
                    interface_config = {
                        "interface": "index_zh_a_hist",
                        "params": {"symbol": "000001"},
                        "description": "测试接口"
                    }
                    
                    result = await updater.update_single_interface(interface_config)
                    print(f"单个接口更新结果: {result}")
                    
                    # 测试每日更新
                    daily_result = await updater.run_daily_updates()
                    print(f"每日更新结果: {daily_result}")
                    
                    return result and daily_result[0] > 0
        
        result = asyncio.run(test_run())
        
        if result:
            print("✅ 夜间更新脚本直接测试 - 成功")
            return True
        else:
            print("❌ 夜间更新脚本直接测试 - 失败")
            return False
            
    except Exception as e:
        print(f"💥 夜间更新脚本直接测试 - 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 首先测试脚本本身
    script_success = test_nightly_script_directly()
    
    # 然后运行完整测试套件
    test_success = main()
    
    # 综合结果
    if script_success and test_success == 0:
        print("\n🎊 所有测试和验证都通过了！")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试或验证失败")
        sys.exit(1)
