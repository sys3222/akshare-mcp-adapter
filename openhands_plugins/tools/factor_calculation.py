"""因子计算工具"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from scipy import stats

class FactorCalculationTool:
    """因子计算工具
    
    提供各种因子计算和标准化功能
    """
    
    def calculate_factor(self, data: pd.DataFrame, factor_column: str, 
                        method: str = 'zscore') -> Dict[str, Any]:
        """计算因子值"""
        
        if factor_column not in data.columns:
            raise ValueError(f"Column {factor_column} not found in data")
        
        factor_values = data[factor_column].copy()
        
        # 标准化处理
        if method == 'zscore':
            normalized_values = stats.zscore(factor_values.dropna())
        elif method == 'rank':
            normalized_values = factor_values.rank(pct=True)
        elif method == 'minmax':
            min_val, max_val = factor_values.min(), factor_values.max()
            normalized_values = (factor_values - min_val) / (max_val - min_val)
        else:
            normalized_values = factor_values
        
        # 计算统计信息
        stats_info = {
            'mean': float(factor_values.mean()),
            'std': float(factor_values.std()),
            'min': float(factor_values.min()),
            'max': float(factor_values.max()),
            'missing_count': int(factor_values.isna().sum()),
            'total_count': len(factor_values)
        }
        
        return {
            'factor_values': normalized_values,
            'calculation_stats': stats_info,
            'method': method,
            'calculation_time': pd.Timestamp.now().isoformat()
        }
    
    def calculate_rolling_factor(self, data: pd.DataFrame, factor_column: str,
                               window: int = 20) -> pd.Series:
        """计算滚动因子值"""
        
        return data[factor_column].rolling(window=window).mean()
