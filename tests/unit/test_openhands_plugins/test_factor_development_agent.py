"""因子开发Agent测试"""

import pytest
import asyncio
from unittest.mock import Mock

from openhands_plugins.agents.factor_development_agent import FactorDevelopmentAgent

class TestFactorDevelopmentAgent:
    """因子开发Agent测试类"""
    
    @pytest.fixture
    def agent(self):
        """创建测试用的Agent实例"""
        return FactorDevelopmentAgent()
    
    def test_agent_initialization(self, agent):
        """测试Agent初始化"""
        
        assert agent.name == "FactorDevelopmentAgent"
        assert agent.version == "1.0.0"
        assert len(agent.capabilities) == 5
        assert len(agent.workflow_stages) == 9
        
        # 检查能力列表
        expected_capabilities = [
            "factor_research",
            "factor_testing", 
            "factor_optimization",
            "backtest_analysis",
            "risk_assessment"
        ]
        
        for capability in expected_capabilities:
            assert capability in agent.capabilities
    
    def test_get_capabilities(self, agent):
        """测试获取能力列表"""
        
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        
        # 确保返回的是副本
        capabilities.append("new_capability")
        assert len(agent.capabilities) == 5
    
    def test_get_workflow_stages(self, agent):
        """测试获取工作流阶段"""
        
        stages = agent.get_workflow_stages()
        assert isinstance(stages, list)
        assert len(stages) == 9
        
        expected_stages = [
            "idea_analysis",
            "data_preparation", 
            "factor_calculation",
            "initial_testing",
            "statistical_analysis",
            "risk_assessment",
            "optimization",
            "backtest",
            "final_evaluation"
        ]
        
        for stage in expected_stages:
            assert stage in stages
    
    @pytest.mark.asyncio
    async def test_develop_factor_success(self, agent):
        """测试成功的因子开发流程"""
        
        result = await agent.develop_factor(
            factor_idea="基于ROE的价值因子",
            target_universe="沪深300"
        )
        
        # 验证基本结构
        assert result['status'] == 'completed'
        assert result['factor_idea'] == "基于ROE的价值因子"
        assert result['target_universe'] == "沪深300"
        assert 'start_time' in result
        assert 'end_time' in result
        assert 'stages' in result
        
        # 验证所有阶段都完成
        assert len(result['stages']) == 9
        
        for stage in result['stages']:
            assert stage['status'] == 'completed'
            assert 'name' in stage
            assert 'results' in stage
            assert 'timestamp' in stage
    
    @pytest.mark.asyncio
    async def test_stage_execution(self, agent):
        """测试单个阶段执行"""
        
        context = {
            'factor_idea': '测试因子',
            'target_universe': '全市场'
        }
        
        # 测试想法分析阶段
        result = await agent._execute_stage('idea_analysis', context)
        
        assert isinstance(result, dict)
        assert 'idea_type' in result
        assert 'complexity' in result
        assert 'data_requirements' in result
        
        # 测试不存在的阶段
        result = await agent._execute_stage('non_existent_stage', context)
        assert result['status'] == 'skipped'
        assert result['reason'] == 'no_handler'
    
    @pytest.mark.asyncio
    async def test_individual_stage_handlers(self, agent):
        """测试各个阶段处理器"""
        
        context = {'factor_idea': '测试', 'target_universe': '测试'}
        
        # 测试数据准备
        result = await agent._prepare_data(context)
        assert 'data_sources' in result
        assert 'data_range' in result
        
        # 测试因子计算
        result = await agent._calculate_factor(context)
        assert 'factor_coverage' in result
        assert 'calculation_method' in result
        
        # 测试回测
        result = await agent._run_backtest(context)
        assert 'total_return' in result
        assert 'sharpe_ratio' in result
        assert 'max_drawdown' in result
