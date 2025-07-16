#!/usr/bin/env python3
"""
基础功能测试脚本
验证核心组件是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试基础导入"""
    print("🔍 测试基础导入...")
    
    try:
        from models.schemas import IntentType, AnalysisContext, AnalysisResult
        print("✅ 模型导入成功")
    except Exception as e:
        print(f"❌ 模型导入失败: {e}")
        return False
    
    try:
        from handlers.llm_handler import LLMAnalysisHandler
        print("✅ LLM处理器导入成功")
    except Exception as e:
        print(f"❌ LLM处理器导入失败: {e}")
        return False
    
    return True

def test_llm_handler():
    """测试LLM处理器基础功能"""
    print("\n🧠 测试LLM处理器...")
    
    try:
        from handlers.llm_handler import LLMAnalysisHandler
        from models.schemas import IntentType
        
        # 创建处理器实例
        handler = LLMAnalysisHandler(use_llm=False)  # 使用规则模式
        print("✅ LLM处理器创建成功")
        
        # 测试意图识别
        context = handler._identify_intent("分析000001")
        print(f"✅ 意图识别成功: {context.intent}, 置信度: {context.confidence}")
        
        # 测试模板加载
        templates = handler.analysis_templates
        print(f"✅ 模板加载成功: {len(templates)} 个模板")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_analysis():
    """测试数据分析功能"""
    print("\n📊 测试数据分析...")
    
    try:
        import pandas as pd
        from handlers.llm_handler import LLMAnalysisHandler
        
        handler = LLMAnalysisHandler(use_llm=False)
        
        # 创建测试数据
        test_data = pd.DataFrame({
            '日期': ['2024-01-01', '2024-01-02', '2024-01-03'],
            '收盘': [10.0, 10.5, 11.0],
            '成交量': [1000000, 1200000, 800000]
        })
        
        # 测试股票数据分析
        data_points = {}
        insights = handler._analyze_stock_data(test_data, data_points)
        
        print(f"✅ 数据分析成功: {len(insights)} 个洞察, {len(data_points)} 个数据点")
        print(f"   价格变化: {data_points.get('price_change_pct', 'N/A')}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_system():
    """测试配置系统"""
    print("\n⚙️ 测试配置系统...")
    
    try:
        from core.config import get_config, ConfigManager
        
        # 测试配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print(f"✅ 配置系统成功: 环境={config.environment}")
        print(f"   LLM配置: provider={config.llm.provider}, model={config.llm.model_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_system():
    """测试监控系统"""
    print("\n📈 测试监控系统...")
    
    try:
        from core.monitoring import PerformanceMonitor
        
        # 创建监控实例
        monitor = PerformanceMonitor()
        
        # 测试指标收集
        stats = monitor.get_summary_stats()
        print(f"✅ 监控系统成功: {len(stats)} 个统计项")
        
        # 测试健康检查
        health = monitor.check_health()
        print(f"   健康状态: {health['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 监控系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 AkShare MCP Adapter - 基础功能测试")
    print("=" * 50)
    
    tests = [
        ("基础导入", test_imports),
        ("LLM处理器", test_llm_handler),
        ("数据分析", test_data_analysis),
        ("配置系统", test_config_system),
        ("监控系统", test_monitoring_system),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📋 测试总结: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有基础功能测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关组件")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
