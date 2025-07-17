"""统计检验工具"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from scipy import stats

class StatisticalTestTool:
    """统计检验工具
    
    提供各种统计检验和显著性测试功能
    """
    
    def calculate_ic(self, factor_values: np.ndarray, returns: np.ndarray) -> Dict[str, Any]:
        """计算信息系数(IC)"""
        
        # 移除NaN值
        mask = ~(np.isnan(factor_values) | np.isnan(returns))
        clean_factor = factor_values[mask]
        clean_returns = returns[mask]
        
        if len(clean_factor) < 10:
            return {
                'ic': np.nan,
                'rank_ic': np.nan,
                'p_value': np.nan,
                'is_significant': False,
                'sample_size': len(clean_factor)
            }
        
        # 计算Pearson相关系数
        ic, p_value = stats.pearsonr(clean_factor, clean_returns)
        
        # 计算Spearman相关系数(Rank IC)
        rank_ic, _ = stats.spearmanr(clean_factor, clean_returns)
        
        # 判断显著性(p < 0.05)
        is_significant = p_value < 0.05
        
        return {
            'ic': float(ic),
            'rank_ic': float(rank_ic),
            'p_value': float(p_value),
            'is_significant': bool(is_significant),
            'sample_size': len(clean_factor)
        }
    
    def test_normality(self, data: np.ndarray) -> Dict[str, Any]:
        """正态性检验"""
        
        # Shapiro-Wilk检验
        statistic, p_value = stats.shapiro(data)
        
        return {
            'test_name': 'shapiro_wilk',
            'statistic': float(statistic),
            'p_value': float(p_value),
            'is_normal': bool(p_value > 0.05)
        }
    
    def calculate_factor_metrics(self, factor_values: np.ndarray, 
                               returns: np.ndarray) -> Dict[str, Any]:
        """计算因子综合指标"""
        
        ic_result = self.calculate_ic(factor_values, returns)
        
        # 计算IC的稳定性
        ic_std = np.std([ic_result['ic']])  # 简化版本
        ic_ir = ic_result['ic'] / ic_std if ic_std > 0 else 0
        
        return {
            'ic_mean': ic_result['ic'],
            'ic_std': float(ic_std),
            'ic_ir': float(ic_ir),
            'rank_ic': ic_result['rank_ic'],
            'significance': ic_result['is_significant'],
            'sample_size': ic_result['sample_size']
        }
