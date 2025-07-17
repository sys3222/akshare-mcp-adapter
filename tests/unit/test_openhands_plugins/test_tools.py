"""量化工具测试"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

from openhands_plugins.tools import QuantToolsRegistry

class TestQuantToolsRegistry:
    """量化工具注册表测试"""
    
    @pytest.fixture
    def registry(self):
        """创建工具注册表"""
        return QuantToolsRegistry()
    
    def test_registry_initialization(self, registry):
        """测试注册表初始化"""
        
        assert hasattr(registry, 'tools')
        assert isinstance(registry.tools, dict)
        
        # 检查基础工具是否注册
        expected_tools = [
            'market_analysis',
            'factor_calculation', 
            'statistical_test',
            'backtest',
            'data_quality'
        ]
        
        for tool_name in expected_tools:
            assert tool_name in registry.tools
    
    def test_market_analysis_tool(self, registry):
        """测试市场分析工具"""
        
        tool = registry.get_tool('market_analysis')
        assert tool is not None
        
        # 测试市场分析
        result = tool.analyze_market_regime()
        
        assert 'volatility_regime' in result
        assert 'trend_direction' in result
        assert result['volatility_regime'] in ['low', 'medium', 'high']
        assert result['trend_direction'] in ['up', 'down', 'sideways']
    
    def test_factor_calculation_tool(self, registry):
        """测试因子计算工具"""
        
        tool = registry.get_tool('factor_calculation')
        assert tool is not None
        
        # 创建测试数据
        test_data = pd.DataFrame({
            'stock_code': ['000001', '000002', '000003'] * 10,
            'date': pd.date_range('2024-01-01', periods=30),
            'close': np.random.randn(30) + 100,
            'pe_ratio': np.random.randn(30) + 15
        })
        
        # 测试因子计算
        result = tool.calculate_factor(test_data, 'pe_ratio', method='zscore')
        
        assert 'factor_values' in result
        assert 'calculation_stats' in result
        assert len(result['factor_values']) == len(test_data)
    
    def test_statistical_test_tool(self, registry):
        """测试统计检验工具"""
        
        tool = registry.get_tool('statistical_test')
        assert tool is not None
        
        # 创建测试数据
        factor_values = np.random.randn(1000)
        returns = np.random.randn(1000) * 0.02
        
        # 测试IC计算
        result = tool.calculate_ic(factor_values, returns)
        
        assert 'ic' in result
        assert 'rank_ic' in result
        assert 'p_value' in result
        assert 'is_significant' in result
        assert isinstance(result['ic'], float)
        assert -1 <= result['ic'] <= 1
