"""集成测试 - 验证各组件协同工作"""

import pytest
import asyncio
from unittest.mock import Mock

from openhands_plugins.agents.factor_development_agent import FactorDevelopmentAgent
from openhands_plugins.memory.market_wisdom_extension import MarketWisdomExtension, KnowledgeMicroagent
from openhands_plugins.tools.registry import QuantToolsRegistry

class TestIntegration:
    """集成测试类"""
    
    @pytest.fixture
    def complete_system(self):
        """创建完整的系统"""

        # 创建Agent
        agent = FactorDevelopmentAgent()

        # 创建Memory扩展
        mock_memory = Mock()
        mock_memory.knowledge_microagents = {}
        memory_extension = MarketWisdomExtension(memory=mock_memory)
        
        # 创建工具注册表
        tools_registry = QuantToolsRegistry()
        
        # 集成到Agent中
        agent.market_wisdom = memory_extension
        agent.quant_tools = {
            'market_analysis': tools_registry.get_tool('market_analysis'),
            'factor_calculation': tools_registry.get_tool('factor_calculation'),
            'statistical_test': tools_registry.get_tool('statistical_test')
        }
        
        return {
            'agent': agent,
            'memory': memory_extension,
            'tools': tools_registry
        }
    
    @pytest.mark.asyncio
    async def test_complete_factor_development_workflow(self, complete_system):
        """测试完整的因子开发工作流"""
        
        agent = complete_system['agent']
        
        # 执行因子开发
        result = await agent.develop_factor(
            factor_idea="基于ROE的价值因子",
            target_universe="沪深300"
        )
        
        # 验证工作流完成
        assert result['status'] == 'completed'
        assert len(result['stages']) == 9
        
        # 验证每个阶段都有结果
        for stage in result['stages']:
            assert stage['status'] == 'completed'
            assert 'results' in stage
    
    def test_memory_and_tools_integration(self, complete_system):
        """测试Memory和Tools的集成"""
        
        memory = complete_system['memory']
        tools = complete_system['tools']
        
        # 添加市场常识
        microagent = KnowledgeMicroagent(
            name='integration_test',
            content="测试相关性: 0.5",
            triggers=['测试']
        )
        memory.add_wisdom_microagent(microagent)
        
        # 使用工具分析
        market_tool = tools.get_tool('market_analysis')
        market_result = market_tool.analyze_market_regime()
        
        # 验证结果
        assert 'volatility_regime' in market_result
        
        # 验证Memory召回
        from openhands_plugins.memory.market_wisdom_extension import RecallAction
        action = RecallAction(query="测试相关性")
        observation = memory.recall_market_wisdom(action)
        
        assert observation is not None
        assert "0.5" in observation.content
    
    def test_agent_with_real_tools(self, complete_system):
        """测试Agent使用真实工具"""
        
        agent = complete_system['agent']
        
        # 测试工具是否正确集成
        assert agent.quant_tools['market_analysis'] is not None
        assert agent.quant_tools['factor_calculation'] is not None
        assert agent.quant_tools['statistical_test'] is not None
        
        # 测试工具调用
        market_tool = agent.quant_tools['market_analysis']
        result = market_tool.analyze_market_regime()
        
        assert isinstance(result, dict)
        assert 'volatility_regime' in result
