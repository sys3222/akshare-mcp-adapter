"""市场分析工具"""

import numpy as np
import pandas as pd
from typing import Dict, Any

class MarketAnalysisTool:
    """市场分析工具
    
    提供市场环境诊断和分析功能
    """
    
    def analyze_market_regime(self, data: pd.DataFrame = None) -> Dict[str, Any]:
        """分析市场状态"""
        
        # 如果没有提供数据，使用模拟数据
        if data is None:
            data = self._generate_mock_data()
        
        # 计算波动率
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        
        # 判断波动率状态
        if volatility < 0.15:
            volatility_regime = 'low'
        elif volatility < 0.25:
            volatility_regime = 'medium'
        else:
            volatility_regime = 'high'
        
        # 判断趋势方向
        recent_return = (data['close'].iloc[-1] / data['close'].iloc[-20] - 1)
        if recent_return > 0.05:
            trend_direction = 'up'
        elif recent_return < -0.05:
            trend_direction = 'down'
        else:
            trend_direction = 'sideways'
        
        return {
            'volatility_regime': volatility_regime,
            'trend_direction': trend_direction,
            'volatility_value': volatility,
            'recent_return': recent_return,
            'analysis_date': pd.Timestamp.now().isoformat()
        }
    
    def _generate_mock_data(self) -> pd.DataFrame:
        """生成模拟市场数据"""
        
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        prices = 100 + np.random.randn(100).cumsum()
        
        return pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 100)
        })
