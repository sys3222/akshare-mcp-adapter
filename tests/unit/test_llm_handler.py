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

    def test_llm_mode_initialization(self, handler):
        """测试LLM模式初始化"""
        assert hasattr(handler, 'use_llm')
        if handler.use_llm:
            assert hasattr(handler, 'akshare_tool')
            assert hasattr(handler, 'model_name')

    def test_dual_mode_analysis(self, handler):
        """测试双模式分析选择"""
        llm_handler = LLMAnalysisHandler(use_llm=True)
        rule_handler = LLMAnalysisHandler(use_llm=False)
        assert llm_handler.use_llm != rule_handler.use_llm

    def test_parse_llm_response(self, handler):
        """测试LLM响应解析"""
        llm_text = """分析结果：股价上涨。建议：适量买入。风险等级：中等风险"""
        result = handler._parse_llm_response(llm_text, "分析000001")
        assert isinstance(result, AnalysisResult)
        assert result.confidence == 0.9

    def test_chart_suggestions(self, handler):
        """测试图表建议"""
        context = AnalysisContext(
            intent=IntentType.STOCK_ANALYSIS,
            entities={'stock_codes': ['000001']},
            confidence=0.9,
            raw_query="分析000001"
        )
        charts = handler._suggest_charts(context, {})
        assert "价格走势图" in charts

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, handler):
        """测试并发分析"""
        queries = ["分析000001", "分析000002"]
        mock_response = PaginatedDataResponse(
            data=[{'日期': '2024-01-01', '收盘': 10.0}],
            total_records=1, current_page=1, total_pages=1
        )

        with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = mock_response
            tasks = [handler.analyze_query(query, "test_user") for query in queries]
            results = await asyncio.gather(*tasks)
            assert len(results) == len(queries)
            for result in results:
                assert isinstance(result, AnalysisResult)

    def test_llm_mode_initialization(self, handler):
        """测试LLM模式初始化"""
        # 测试LLM可用性检查
        assert hasattr(handler, 'use_llm')

        # 如果LLM可用，检查相关配置
        if handler.use_llm:
            assert hasattr(handler, 'akshare_tool')
            assert hasattr(handler, 'model_name')
            assert handler.model_name == "gemini-1.5-pro-latest"

    def test_dual_mode_analysis(self, handler):
        """测试双模式分析选择"""
        # 创建LLM和规则模式的处理器
        llm_handler = LLMAnalysisHandler(use_llm=True)
        rule_handler = LLMAnalysisHandler(use_llm=False)

        assert llm_handler.use_llm != rule_handler.use_llm

    def test_parse_llm_response(self, handler):
        """测试LLM响应解析"""
        llm_text = """
        分析结果显示：
        - 股价呈现上涨趋势
        - 成交量有所放大

        投资建议：
        - 可以考虑适量买入
        - 注意控制风险

        风险等级：中等风险
        """

        result = handler._parse_llm_response(llm_text, "分析000001")

        assert isinstance(result, AnalysisResult)
        assert len(result.insights) > 0
        assert len(result.recommendations) > 0
        assert result.risk_level == "中等风险"
        assert result.confidence == 0.9

    def test_chart_suggestions(self, handler):
        """测试图表建议"""
        # 股票分析应该建议价格走势图
        context = AnalysisContext(
            intent=IntentType.STOCK_ANALYSIS,
            entities={'stock_codes': ['000001']},
            confidence=0.9,
            raw_query="分析000001"
        )

        charts = handler._suggest_charts(context, {})
        assert "价格走势图" in charts
        assert "成交量图" in charts

        # 市场概览应该建议市场热力图
        context.intent = IntentType.MARKET_OVERVIEW
        charts = handler._suggest_charts(context, {})
        assert "市场热力图" in charts

    def test_confidence_calculation(self, handler):
        """测试置信度计算"""
        # 高置信度场景
        context = AnalysisContext(
            intent=IntentType.STOCK_ANALYSIS,
            entities={'stock_codes': ['000001']},
            confidence=0.95,
            raw_query="分析000001"
        )

        confidence = handler._calculate_confidence(context, True, 100)
        assert confidence >= 0.8

        # 低置信度场景
        context.confidence = 0.3
        confidence = handler._calculate_confidence(context, False, 10)
        assert confidence <= 0.5

    def test_entity_normalization(self, handler):
        """测试实体标准化"""
        # 测试股票代码标准化
        entities = {'entity_0': '平安银行', 'entity_1': '000001'}
        normalized = handler._normalize_entities(entities)

        assert 'stock_codes' in normalized
        assert '000001' in normalized['stock_codes']

    def test_time_range_parsing(self, handler):
        """测试时间范围解析"""
        # 测试相对时间
        start_date, end_date = handler._parse_time_range("最近30天")
        assert start_date is not None
        assert end_date is not None

        # 测试绝对时间
        start_date, end_date = handler._parse_time_range("2024年1月")
        assert start_date == "20240101"
        assert end_date == "20240131"

    def test_data_validation(self, handler):
        """测试数据验证"""
        # 有效数据
        valid_data = pd.DataFrame({
            '日期': ['2024-01-01', '2024-01-02'],
            '收盘': [10.0, 10.5]
        })
        assert handler._validate_data(valid_data) == True

        # 无效数据（空数据）
        empty_data = pd.DataFrame()
        assert handler._validate_data(empty_data) == False

        # 无效数据（缺少关键列）
        invalid_data = pd.DataFrame({'其他列': [1, 2]})
        assert handler._validate_data(invalid_data) == False

    def test_performance_metrics(self, handler):
        """测试性能指标计算"""
        # 创建价格数据
        prices = [10.0, 10.5, 11.0, 10.8, 11.2]

        # 计算波动率
        volatility = handler._calculate_volatility(prices)
        assert volatility > 0

        # 计算收益率
        returns = handler._calculate_returns(prices)
        assert len(returns) == len(prices) - 1

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, handler):
        """测试并发分析"""
        # 模拟多个并发请求
        queries = [
            "分析000001",
            "分析000002",
            "市场概况"
        ]

        # Mock数据响应
        mock_response = PaginatedDataResponse(
            data=[{'日期': '2024-01-01', '收盘': 10.0}],
            total_records=1,
            current_page=1,
            total_pages=1
        )

        with patch('handlers.llm_handler.handle_mcp_data_request', new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = mock_response

            # 并发执行分析
            tasks = [handler.analyze_query(query, "test_user") for query in queries]
            results = await asyncio.gather(*tasks)

            # 验证所有结果
            assert len(results) == len(queries)
            for result in results:
                assert isinstance(result, AnalysisResult)
                assert result.summary != ""
