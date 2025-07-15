#!/usr/bin/env python3
"""
LLM集成功能演示脚本
展示基于真实LLM模型的智能金融分析功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_llm_availability():
    """检查LLM功能可用性"""
    print("🔍 检查LLM功能可用性...")
    
    # 检查依赖
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI 库已安装")
    except ImportError:
        print("❌ Google Generative AI 库未安装")
        print("   请运行: pip install google-generativeai")
        return False
    
    # 检查API密钥
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        print("✅ GEMINI_API_KEY 环境变量已设置")
        print(f"   密钥前缀: {api_key[:10]}...")
    else:
        print("❌ GEMINI_API_KEY 环境变量未设置")
        print("   请设置环境变量: export GEMINI_API_KEY=your_api_key")
        return False
    
    return True

async def demo_rule_based_analysis():
    """演示基于规则的分析"""
    print("\n📊 基于规则的分析演示")
    print("=" * 50)
    
    from handlers.llm_handler import rule_based_handler
    
    test_queries = [
        "分析000001最近的表现",
        "今日市场概况如何",
        "000001的财务指标怎么样"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        try:
            result = await rule_based_handler.analyze_query(query, "demo_user")
            print(f"摘要: {result.summary}")
            print(f"洞察数量: {len(result.insights)}")
            print(f"建议数量: {len(result.recommendations)}")
            print(f"风险等级: {result.risk_level}")
            print(f"置信度: {result.confidence}")
        except Exception as e:
            print(f"❌ 分析失败: {e}")

async def demo_llm_analysis():
    """演示基于LLM的分析"""
    print("\n🤖 基于LLM的分析演示")
    print("=" * 50)
    
    from handlers.llm_handler import llm_analysis_handler
    
    if not llm_analysis_handler.use_llm:
        print("❌ LLM功能不可用，跳过演示")
        return
    
    test_queries = [
        "帮我分析一下平安银行(000001)最近的股价表现",
        "当前A股市场整体情况如何？",
        "000001和600519哪个投资价值更高？"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        try:
            result = await llm_analysis_handler.analyze_query(query, "demo_user")
            print(f"摘要: {result.summary[:200]}...")
            print(f"洞察: {result.insights[:2]}")
            print(f"建议: {result.recommendations[:2]}")
            print(f"风险等级: {result.risk_level}")
            print(f"置信度: {result.confidence}")
        except Exception as e:
            print(f"❌ LLM分析失败: {e}")

def demo_comparison():
    """对比两种分析模式"""
    print("\n⚖️ 分析模式对比")
    print("=" * 50)
    
    comparison_table = [
        ["特性", "基于规则", "基于LLM"],
        ["响应速度", "快速 (<1s)", "较慢 (3-10s)"],
        ["分析深度", "基础统计分析", "深度智能分析"],
        ["自然语言理解", "有限", "强大"],
        ["数据获取", "预定义接口", "智能选择接口"],
        ["个性化程度", "模板化", "高度个性化"],
        ["成本", "免费", "需要API费用"],
        ["离线可用", "是", "否"],
        ["准确性", "稳定", "更智能但可能有变化"],
        ["扩展性", "需要编程", "通过提示词优化"]
    ]
    
    for row in comparison_table:
        print(f"{row[0]:<12} | {row[1]:<15} | {row[2]:<15}")

def demo_optimization_suggestions():
    """展示基于您代码的优化建议"""
    print("\n🚀 基于您代码的优化建议")
    print("=" * 50)
    
    suggestions = [
        {
            "类别": "Function Calling优化",
            "建议": [
                "✅ 已集成：使用FunctionDeclaration定义工具",
                "✅ 已集成：支持动态接口发现",
                "🔄 可优化：添加更多专业金融分析工具",
                "🔄 可优化：支持多步骤工具调用链"
            ]
        },
        {
            "类别": "对话管理优化", 
            "建议": [
                "✅ 已集成：支持多轮对话历史",
                "🔄 可优化：添加对话上下文记忆",
                "🔄 可优化：支持对话状态管理",
                "🔄 可优化：实现对话意图延续"
            ]
        },
        {
            "类别": "数据处理优化",
            "建议": [
                "✅ 已集成：数据截断防止过载",
                "🔄 可优化：智能数据摘要生成",
                "🔄 可优化：数据可视化建议",
                "🔄 可优化：异常数据检测和处理"
            ]
        },
        {
            "类别": "性能优化",
            "建议": [
                "🔄 可优化：添加LLM响应缓存",
                "🔄 可优化：实现流式响应",
                "🔄 可优化：并行工具调用",
                "🔄 可优化：智能模型选择"
            ]
        }
    ]
    
    for suggestion in suggestions:
        print(f"\n📋 {suggestion['类别']}:")
        for item in suggestion['建议']:
            print(f"  {item}")

async def main():
    """主演示函数"""
    print("🎯 LLM集成功能演示")
    print("=" * 60)
    
    # 检查LLM可用性
    llm_available = check_llm_availability()
    
    # 演示基于规则的分析
    await demo_rule_based_analysis()
    
    # 如果LLM可用，演示LLM分析
    if llm_available:
        await demo_llm_analysis()
    else:
        print("\n⚠️ LLM功能不可用，跳过LLM演示")
        print("请配置GEMINI_API_KEY环境变量后重试")
    
    # 对比分析
    demo_comparison()
    
    # 优化建议
    demo_optimization_suggestions()
    
    print("\n🎉 演示完成！")
    print("\n💡 总结:")
    print("  • 成功集成了您的LLM Function Calling设计")
    print("  • 支持基于规则和基于LLM的双模式分析")
    print("  • 实现了智能工具调用和数据获取")
    print("  • 提供了完整的回退机制和错误处理")
    print("  • 保持了与现有系统的完美兼容性")

if __name__ == "__main__":
    asyncio.run(main())
