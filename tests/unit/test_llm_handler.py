"""
LLM智能分析处理器的单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from handlers.llm_handler import (
    LLMAnalysisHandler, IntentType, AnalysisContext, AnalysisResult
)
from models.schemas import PaginatedDataResponse

class TestLLMAnalysisHandler:
    
    @pytest.fixture
    def handler(self):
        """创建LLM分析处理器实例"""
        return LLMAnalysisHandler()
    
    def test_intent_identification_stock_analysis(self, handler):
        """测试股票分析意图识别"""
        queries = [
            "分析000001",
            "000001怎么样",
            "平安银行表现如何",
            "查看000001的情况"
        ]
        
        for query in queries:
            context = handler._identify_intent(query)
            assert context.intent == IntentType.STOCK_ANALYSIS
            assert context.confidence > 0.5
            assert 'stock_codes' in context.entities or 'entity_0' in context.entities
    
    def test_intent_identification_market_overview(self, handler):
        """测试市场概览意图识别"""
        queries = [
            "市场概况如何",
            "今日大盘情况",
            "整体市场表现",
            "市场行情怎么样"
        ]
        
        for query in queries:
            context = handler._identify_intent(query)
            assert context.intent == IntentType.MARKET_OVERVIEW
            assert context.confidence > 0.5
    
    def test_intent_identification_financial_metrics(self, handler):
        """测试财务指标意图识别"""
        queries = [
            "000001的PE如何",
            "财务指标分析",
            "市盈率情况",
            "ROE怎么样"
        ]
        
        for query in queries:
            context = handler._identify_intent(query)
            assert context.intent == IntentType.FINANCIAL_METRICS
            assert context.confidence > 0.5
    
    def test_intent_identification_unknown(self, handler):
        """测试未知意图"""
        queries = [
            "今天天气怎么样",
            "你好",
            "随机文本"
        ]
        
        for query in queries:
            context = handler._identify_intent(query)
            assert context.intent == IntentType.UNKNOWN
            assert context.confidence < 0.8
    
    def test_entity_extraction(self, handler):
        """测试实体提取"""
        # 测试股票代码提取
        context = handler._identify_intent("分析000001和600519")
        assert 'stock_codes' in context.entities
        assert '000001' in context.entities['stock_codes']
        assert '600519' in context.entities['stock_codes']
        
        # 测试时间范围提取
        context = handler._identify_intent("最近30天的000001表现")
        assert 'time_range' in context.entities
        assert '30' in context.entities['time_range']
    
    def test_stock_data_analysis(self, handler):
        """测试股票数据分析"""
        # 创建模拟股票数据
        mock_data = pd.DataFrame({
            '日期': ['2024-01-01', '2024-01-02', '2024-01-03'],
            '收盘': [10.0, 10.5, 11.0],
            '成交量': [1000000, 1200000, 800000]
        })
        
        data_points = {}
        insights = handler._analyze_stock_data(mock_data, data_points)
        
        assert len(insights) > 0
        assert 'price_change_pct' in data_points
        assert data_points['price_change_pct'] == 10.0  # (11-10)/10*100
        assert 'volatility' in data_points
        assert 'volume_ratio' in data_points
    
    def test_market_data_analysis(self, handler):
        """测试市场数据分析"""
        # 创建模拟市场数据
        mock_data = pd.DataFrame({
            '代码': ['000001', '000002', '000003', '000004'],
            '涨跌幅': [5.0, -2.0, 3.0, -1.0]
        })
        
        data_points = {}
        insights = handler._analyze_market_data(mock_data, data_points)
        
        assert len(insights) > 0
        assert 'rising_ratio' in data_points
        assert data_points['rising_ratio'] == 50.0  # 2/4*100
    
    def test_financial_data_analysis(self, handler):
        """测试财务数据分析"""
        # 创建模拟财务数据
        mock_data = pd.DataFrame({
            'PE': [15.0, 20.0, 25.0],
            'ROE': [12.0, 18.0, 8.0]
        })
        
        data_points = {}
        insights = handler._analyze_financial_data(mock_data, data_points)
        
        assert len(insights) > 0
        assert 'avg_pe' in data_points
        assert 'avg_roe' in data_points
        assert data_points['avg_pe'] == 20.0  # (15+20+25)/3
        assert data_points['avg_roe'] == 12.67  # (12+18+8)/3
    
    def test_risk_assessment(self, handler):
        """测试风险评估"""
        # 低风险场景
        data_points = {
            'volatility': 1.0,
            'price_change_pct': 2.0,
            'rising_ratio': 60.0
        }
        risk_level = handler._assess_risk_level(None, data_points)
        assert risk_level == "低风险"
        
        # 高风险场景
        data_points = {
            'volatility': 5.0,
            'price_change_pct': 15.0,
            'rising_ratio': 20.0
        }
        risk_level = handler._assess_risk_level(None, data_points)
        assert risk_level == "高风险"
    
    def test_summary_generation(self, handler):
        """测试摘要生成"""
        # 股票分析摘要
        context = AnalysisContext(
            intent=IntentType.STOCK_ANALYSIS,
            entities={'stock_codes': ['000001']},
            confidence=0.9,
            raw_query="分析000001"
        )
        
        insights = ["股价上涨", "成交量放大"]
        data_points = {'price_change_pct': 5.0}
        
        summary = handler._generate_summary(context, insights, data_points)
        assert "000001" in summary
        assert "上涨" in summary
        assert "5.0" in summary
    
    def test_stock_recommendations(self, handler):
        """测试股票投资建议生成"""
        analysis_result = AnalysisResult(
            summary="测试摘要",
            insights=[],
            recommendations=[],
            data_points={
                'price_change_pct': 8.0,
                'volatility': 2.0,
                'volume_ratio': 1.8
            },
            charts_suggested=[],
            risk_level="中等风险",
            confidence=0.8
        )
        
        recommendations = handler._generate_stock_recommendations(analysis_result)
        
        assert len(recommendations) > 0
        assert any("涨幅" in rec for rec in recommendations)
        assert any("成交量" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, handler):
        """测试完整分析工作流程"""
        # Mock数据响应
        mock_response = PaginatedDataResponse(
            data=[
                {'日期': '2024-01-01', '收盘': 10.0, '成交量': 1000000},
                {'日期': '2024-01-02', '收盘': 10.5, '成交量': 1200000},
                {'日期': '2024-01-03', '收盘': 11.0, '成交量': 800000}
            ],
            total_records=3,
            current_page=1,
            total_pages=1
        )
        
        # Mock handle_mcp_data_request
        with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = mock_response
            
            # 执行分析
            result = await handler.analyze_query("分析000001", "test_user")
            
            # 验证结果
            assert isinstance(result, AnalysisResult)
            assert result.summary != ""
            assert len(result.insights) > 0
            assert len(result.recommendations) > 0
            assert result.risk_level in ["低风险", "中等风险", "高风险"]
            assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, handler):
        """测试错误处理"""
        # Mock抛出异常
        with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_handler:
            mock_handler.side_effect = Exception("网络错误")
            
            # 执行分析
            result = await handler.analyze_query("分析000001", "test_user")
            
            # 验证错误处理
            assert isinstance(result, AnalysisResult)
            assert "错误" in result.summary
            assert result.confidence == 0.0
    
    def test_build_params(self, handler):
        """测试参数构建"""
        context = AnalysisContext(
            intent=IntentType.STOCK_ANALYSIS,
            entities={'time_range': '最近30天'},
            confidence=0.9,
            raw_query="最近30天000001表现"
        )
        
        params = handler._build_params("stock_zh_a_hist", "000001", context)
        
        assert params['symbol'] == "000001"
        assert params['period'] == "daily"
        assert 'start_date' in params
        assert 'end_date' in params
    
    def test_template_loading(self, handler):
        """测试模板加载"""
        assert IntentType.STOCK_ANALYSIS in handler.analysis_templates
        assert IntentType.MARKET_OVERVIEW in handler.analysis_templates
        assert IntentType.FINANCIAL_METRICS in handler.analysis_templates
        
        stock_template = handler.analysis_templates[IntentType.STOCK_ANALYSIS]
        assert 'required_data' in stock_template
        assert 'analysis_points' in stock_template
        assert 'risk_factors' in stock_template
