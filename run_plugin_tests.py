#!/usr/bin/env python3
"""
OpenHands插件测试运行器
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """运行所有插件测试"""
    
    print("🧪 OpenHands量化插件测试")
    print("=" * 50)
    
    # 切换到项目目录
    project_root = Path(__file__).parent
    
    test_commands = [
        {
            "name": "因子开发Agent测试",
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/unit/test_openhands_plugins/test_factor_development_agent.py",
                "-v"
            ]
        },
        {
            "name": "市场常识Memory扩展测试", 
            "cmd": [
                sys.executable, "-m", "pytest",
                "tests/unit/test_openhands_plugins/test_market_wisdom_extension.py", 
                "-v"
            ]
        },
        {
            "name": "量化工具测试",
            "cmd": [
                sys.executable, "-m", "pytest",
                "tests/unit/test_openhands_plugins/test_tools.py",
                "-v" 
            ]
        },
        {
            "name": "集成测试",
            "cmd": [
                sys.executable, "-m", "pytest",
                "tests/unit/test_openhands_plugins/test_integration.py",
                "-v"
            ]
        }
    ]
    
    success_count = 0
    total_count = len(test_commands)
    
    for test_config in test_commands:
        print(f"\n🔍 运行 {test_config['name']}...")
        
        try:
            result = subprocess.run(
                test_config['cmd'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"✅ {test_config['name']} - 通过")
                success_count += 1
                
                # 提取测试统计
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'passed' in line and ('failed' in line or 'error' in line):
                        print(f"   📊 {line.strip()}")
                        break
            else:
                print(f"❌ {test_config['name']} - 失败")
                print(f"   错误输出: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_config['name']} - 超时")
        except Exception as e:
            print(f"💥 {test_config['name']} - 异常: {e}")
    
    # 总结
    print(f"\n{'='*50}")
    print(f"📋 测试总结")
    print(f"{'='*50}")
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有插件测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关组件")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
