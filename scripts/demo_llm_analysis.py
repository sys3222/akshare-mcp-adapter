#!/usr/bin/env python3
"""
LLM智能分析功能演示脚本
展示意图识别、数据分析和建议生成的完整流程
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from handlers.llm_handler import LLMAnalysisHandler
from models.schemas import PaginatedDataResponse

def create_mock_stock_data():
    """创建模拟股票数据"""
    return pd.DataFrame({
        '日期': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        '开盘': [10.0, 10.2, 10.8, 11.2, 10.9],
        '收盘': [10.2, 10.8, 11.2, 10.9, 11.5],
        '最高': [10.3, 11.0, 11.5, 11.3, 11.8],
        '最低': [9.9, 10.1, 10.7, 10.8, 10.8],
        '成交量': [1000000, 1500000, 2000000, 1200000, 1800000],
        '涨跌幅': [2.0, 5.88, 3.70, -2.68, 5.50]
    })

def create_mock_market_data():
    """创建模拟市场数据"""
    return pd.DataFrame({
        '代码': ['000001', '000002', '000003', '000004', '000005', '000006', '000007', '000008'],
        '名称': ['平安银行', '万科A', '国农科技', '国华网安', '世纪星源', '深振业A', '全新好', '神州高铁'],
        '最新价': [12.5, 8.9, 15.6, 45.2, 3.8, 6.7, 9.2, 4.1],
        '涨跌幅': [3.2, -1.5, 8.7, -4.2, 2.1, 6.3, -2.8, 1.9],
        '成交量': [5000000, 3200000, 1800000, 900000, 2100000, 1500000, 800000, 1200000]
    })

def create_mock_financial_data():
    """创建模拟财务数据"""
    return pd.DataFrame({
        '股票代码': ['000001', '000002', '000003'],
        '股票名称': ['平安银行', '万科A', '国农科技'],
        'PE': [6.8, 12.5, 28.3],
        'PB': [0.9, 1.2, 3.5],
        'ROE': [11.2, 8.9, 15.6],
        '净利润增长率': [12.5, -5.2, 25.8]
    })

async def demo_intent_recognition():
    """演示意图识别功能"""
    print("🧠 意图识别演示")
    print("=" * 50)
    
    handler = LLMAnalysisHandler()
    
    test_queries = [
        "分析000001的表现",
        "今日市场概况如何",
        "000001的PE和PB怎么样",
        "000001未来走势预测",
        "000001 vs 600519哪个更好",
        "推荐一些优质股票",
        "000001投资风险大吗",
        "今天天气怎么样"  # 未知意图
    ]
    
    for query in test_queries:
        context = handler._identify_intent(query)
        print(f"查询: {query}")
        print(f"  意图: {context.intent.value}")
        print(f"  置信度: {context.confidence:.2f}")
        print(f"  实体: {context.entities}")
        print()

async def demo_stock_analysis():
    """演示股票分析功能"""
    print("📈 股票分析演示")
    print("=" * 50)
    
    handler = LLMAnalysisHandler()
    
    # 创建模拟响应
    mock_data = create_mock_stock_data()
    mock_response = PaginatedDataResponse(
        data=mock_data.to_dict('records'),
        total_records=len(mock_data),
        current_page=1,
        total_pages=1
    )
    
    # Mock数据获取
    with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_handler:
        mock_handler.return_value = mock_response
        
        # 执行分析
        result = await handler.analyze_query("分析000001最近表现如何", "demo_user")
        
        print(f"📊 分析摘要:")
        print(f"  {result.summary}")
        print()
        
        print(f"🔍 关键洞察:")
        for insight in result.insights:
            print(f"  • {insight}")
        print()
        
        print(f"💡 投资建议:")
        for recommendation in result.recommendations:
            print(f"  • {recommendation}")
        print()
        
        print(f"⚠️ 风险等级: {result.risk_level}")
        print(f"📊 置信度: {result.confidence:.2f}")
        print(f"📈 建议图表: {', '.join(result.charts_suggested)}")
        print()
        
        print(f"📋 关键数据点:")
        for key, value in result.data_points.items():
            print(f"  {key}: {value}")

async def demo_market_overview():
    """演示市场概览功能"""
    print("🌐 市场概览演示")
    print("=" * 50)
    
    handler = LLMAnalysisHandler()
    
    # 创建模拟响应
    mock_data = create_mock_market_data()
    mock_response = PaginatedDataResponse(
        data=mock_data.to_dict('records'),
        total_records=len(mock_data),
        current_page=1,
        total_pages=1
    )
    
    # Mock数据获取
    with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_handler:
        mock_handler.return_value = mock_response
        
        # 执行分析
        result = await handler.analyze_query("今日市场整体表现如何", "demo_user")
        
        print(f"📊 市场分析摘要:")
        print(f"  {result.summary}")
        print()
        
        print(f"🔍 市场洞察:")
        for insight in result.insights:
            print(f"  • {insight}")
        print()
        
        print(f"💡 市场建议:")
        for recommendation in result.recommendations:
            print(f"  • {recommendation}")
        print()
        
        print(f"⚠️ 市场风险: {result.risk_level}")
        print(f"📈 建议图表: {', '.join(result.charts_suggested)}")

async def demo_financial_analysis():
    """演示财务分析功能"""
    print("💰 财务分析演示")
    print("=" * 50)
    
    handler = LLMAnalysisHandler()
    
    # 创建模拟响应
    mock_data = create_mock_financial_data()
    mock_response = PaginatedDataResponse(
        data=mock_data.to_dict('records'),
        total_records=len(mock_data),
        current_page=1,
        total_pages=1
    )
    
    # Mock数据获取
    with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_handler:
        mock_handler.return_value = mock_response
        
        # 执行分析
        result = await handler.analyze_query("000001的财务指标如何", "demo_user")
        
        print(f"📊 财务分析摘要:")
        print(f"  {result.summary}")
        print()
        
        print(f"🔍 财务洞察:")
        for insight in result.insights:
            print(f"  • {insight}")
        print()
        
        print(f"💡 财务建议:")
        for recommendation in result.recommendations:
            print(f"  • {recommendation}")
        print()

def demo_optimization_suggestions():
    """展示优化建议"""
    print("🚀 LLM处理器优化建议")
    print("=" * 50)
    
    optimizations = [
        {
            "类别": "意图识别优化",
            "建议": [
                "引入更先进的NLP模型（如BERT、GPT）进行意图分类",
                "增加更多训练数据和意图类型",
                "支持多轮对话和上下文理解",
                "添加意图置信度阈值和兜底策略"
            ]
        },
        {
            "类别": "数据获取优化", 
            "建议": [
                "实现智能数据源选择算法",
                "添加数据质量检查和清洗",
                "支持多数据源融合和交叉验证",
                "实现增量数据更新机制"
            ]
        },
        {
            "类别": "分析算法优化",
            "建议": [
                "引入更多技术指标和量化因子",
                "添加机器学习模型进行预测",
                "实现个性化分析和推荐",
                "支持实时流式数据分析"
            ]
        },
        {
            "类别": "建议生成优化",
            "建议": [
                "基于用户画像个性化建议",
                "添加风险偏好和投资目标考虑",
                "实现动态建议更新机制",
                "支持多语言建议生成"
            ]
        },
        {
            "类别": "系统架构优化",
            "建议": [
                "引入LangGraph进行复杂工作流编排",
                "添加缓存和异步处理提升性能",
                "实现分布式计算支持大规模分析",
                "添加监控和日志系统"
            ]
        }
    ]
    
    for opt in optimizations:
        print(f"📋 {opt['类别']}:")
        for suggestion in opt['建议']:
            print(f"  • {suggestion}")
        print()

async def main():
    """主演示函数"""
    print("🎯 LLM智能分析系统演示")
    print("=" * 60)
    print()
    
    demos = [
        ("意图识别", demo_intent_recognition),
        ("股票分析", demo_stock_analysis),
        ("市场概览", demo_market_overview),
        ("财务分析", demo_financial_analysis)
    ]
    
    for name, demo_func in demos:
        await demo_func()
        print("\n" + "-" * 60 + "\n")
    
    # 展示优化建议
    demo_optimization_suggestions()
    
    print("🎉 演示完成！")
    print("\n💡 总结:")
    print("  • LLM处理器实现了完整的'意图判断 → 数据获取 → 结果分析 → 建议生成'流程")
    print("  • 支持多种金融分析场景和自然语言交互")
    print("  • 具备良好的扩展性和优化空间")
    print("  • 可以与现有的夜间缓存更新系统完美配合")

if __name__ == "__main__":
    asyncio.run(main())
