"""市场常识Memory扩展单元测试"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta

from openhands_plugins.memory.market_wisdom_extension import (
    MarketWisdomExtension,
    RecallAction,
    RecallObservation,
    KnowledgeMicroagent
)

class TestMarketWisdomExtension:
    """市场常识扩展测试类"""
    
    @pytest.fixture
    def extension(self):
        """创建测试用的扩展实例"""
        mock_memory = Mock()
        mock_memory.knowledge_microagents = {}
        return MarketWisdomExtension(memory=mock_memory)
    
    @pytest.fixture
    def sample_microagent(self):
        """创建示例microagent"""
        content = """
# 市场相关性测试

## 美股与黄金
- 相关性: -0.30
- 机制: 风险偏好驱动

## VIX与标普500
- 相关性: -0.75
- 机制: 恐慌指数反映
        """

        return KnowledgeMicroagent(
            name='test_correlations',
            content=content,
            triggers=['美股', '黄金', 'correlation']
        )
    
    def test_extension_initialization(self, extension):
        """测试扩展初始化"""
        
        assert extension.memory is not None
        assert isinstance(extension.wisdom_cache, dict)
        assert extension.last_update_check is None
        assert len(extension.wisdom_triggers) == 5
        
        # 检查触发器配置
        assert 'correlations' in extension.wisdom_triggers
        assert 'macro_indicators' in extension.wisdom_triggers
        assert 'sector_rotation' in extension.wisdom_triggers
        assert 'risk_sentiment' in extension.wisdom_triggers
        assert 'market_regime' in extension.wisdom_triggers
    
    def test_identify_wisdom_type(self, extension):
        """测试智慧类型识别"""
        
        test_cases = [
            ("美股和黄金的相关性如何", "correlations"),
            ("当前宏观经济指标", "macro_indicators"),
            ("板块轮动规律", "sector_rotation"),
            ("市场风险偏好", "risk_sentiment"),
            ("当前是牛市还是熊市", "market_regime"),
            ("无关查询", None)
        ]
        
        for query, expected_type in test_cases:
            result = extension._identify_wisdom_type(query.lower())
            assert result == expected_type
    
    def test_recall_market_wisdom_success(self, extension, sample_microagent):
        """测试成功的市场常识召回"""
        
        # 添加示例microagent
        extension.add_wisdom_microagent(sample_microagent)
        
        # 创建召回请求
        action = RecallAction(query="美股与黄金的相关性", recall_type="market_wisdom")
        
        # 执行召回
        observation = extension.recall_market_wisdom(action)
        
        # 验证结果
        assert observation is not None
        assert isinstance(observation, RecallObservation)
        assert observation.recall_type == "market_wisdom"
        assert "相关性" in observation.content
        
        # 验证元数据
        assert observation.metadata['wisdom_type'] == 'correlations'
        assert observation.metadata['query'] == "美股与黄金的相关性"
        assert observation.metadata['source'] == 'market_wisdom_extension'
    
    def test_get_correlation_wisdom(self, sample_microagent):
        """测试获取特定资产相关性"""

        # 创建一个没有内置数据的扩展
        mock_memory = Mock()
        mock_memory.knowledge_microagents = {}

        # 创建扩展但跳过初始化
        extension = MarketWisdomExtension.__new__(MarketWisdomExtension)
        extension.memory = mock_memory
        extension.wisdom_cache = {}
        extension.last_update_check = None
        extension.wisdom_triggers = {
            'correlations': ['相关性', 'correlation', '关联', '联动'],
            'macro_indicators': ['宏观', 'macro', '经济指标', '利率', '通胀'],
            'sector_rotation': ['板块', 'sector', '轮动', 'rotation', '行业'],
            'risk_sentiment': ['风险', 'risk', '情绪', 'sentiment', 'vix'],
            'market_regime': ['市场', 'regime', '牛市', '熊市', '震荡']
        }
        extension._local_microagents = {}

        # 只添加我们的测试微代理
        extension.add_wisdom_microagent(sample_microagent)

        result = extension.get_correlation_wisdom("美股", "黄金")

        assert result['assets'] == ["美股", "黄金"]
        assert result['correlation'] == -0.30  # 使用测试数据中的值
        assert result['source'] == 'market_wisdom'
        assert result['confidence'] == 'high'
    
    def test_get_wisdom_statistics(self, extension):
        """测试获取统计信息"""
        
        stats = extension.get_wisdom_statistics()
        
        assert 'total_microagents' in stats
        assert 'wisdom_types' in stats
        assert 'cache_size' in stats
        assert 'microagent_names' in stats
        
        # 应该包含示例数据
        assert stats['total_microagents'] >= 2  # 至少有示例的两个
        assert len(stats['wisdom_types']) == 5
