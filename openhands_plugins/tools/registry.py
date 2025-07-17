"""量化工具注册表"""

from typing import Dict, Any, Optional
from openhands_plugins.tools.market_analysis import MarketAnalysisTool
from openhands_plugins.tools.factor_calculation import FactorCalculationTool
from openhands_plugins.tools.statistical_test import StatisticalTestTool

class QuantToolsRegistry:
    """量化工具注册表
    
    管理所有量化分析工具的注册和访问
    """
    
    def __init__(self):
        self.tools = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        
        self.tools['market_analysis'] = MarketAnalysisTool()
        self.tools['factor_calculation'] = FactorCalculationTool()
        self.tools['statistical_test'] = StatisticalTestTool()
        self.tools['backtest'] = MockBacktestTool()
        self.tools['data_quality'] = MockDataQualityTool()
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """获取工具实例"""
        return self.tools.get(tool_name)
    
    def register_tool(self, name: str, tool: Any):
        """注册新工具"""
        self.tools[name] = tool
    
    def list_tools(self) -> list:
        """列出所有工具"""
        return list(self.tools.keys())

class MockBacktestTool:
    """模拟回测工具"""
    
    def run_backtest(self, factor_data, **kwargs):
        return {
            'total_return': 0.15,
            'sharpe_ratio': 0.8,
            'max_drawdown': -0.05
        }

class MockDataQualityTool:
    """模拟数据质量工具"""
    
    def check_quality(self, data, **kwargs):
        return {
            'missing_rate': 0.02,
            'outlier_rate': 0.01,
            'quality_score': 0.95
        }
