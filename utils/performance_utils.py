import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import base64
import tempfile
import os

def analyze_performance(strategy_nav, benchmark_nav=None):
    """
    Analyze strategy performance and return metrics
    
    Args:
        strategy_nav: Series of strategy NAV values
        benchmark_nav: Series of benchmark NAV values (optional)
        
    Returns:
        dict: Performance metrics
    """
    strategy_nav = pd.Series(strategy_nav)
    
    # Calculate returns
    strategy_ret = strategy_nav.pct_change().dropna()
    
    # Calculate benchmark metrics if provided
    if benchmark_nav is not None:
        benchmark_nav = pd.Series(benchmark_nav).reindex(strategy_nav.index).fillna(method='ffill')
        benchmark_ret = benchmark_nav.pct_change().dropna()
        benchmark_ret.name = 'benchmark'
        benchmark_ret = benchmark_ret.reindex(strategy_ret.index).fillna(0)
        excess_ret = strategy_ret - benchmark_ret
        
        # Calculate alpha and beta
        X = sm.add_constant(benchmark_ret)
        model = sm.OLS(strategy_ret, X).fit()
        alpha = model.params['const'] * 252
        beta = model.params[benchmark_ret.name]
        
        # Calculate information ratio
        info_ratio = excess_ret.mean() / excess_ret.std() * np.sqrt(252) if excess_ret.std() != 0 else np.nan
    else:
        alpha = np.nan
        beta = np.nan
        info_ratio = np.nan
    
    # Calculate basic metrics
    days = len(strategy_ret)
    total_return = strategy_nav.iloc[-1] / strategy_nav.iloc[0] - 1
    annual_return = (strategy_nav.iloc[-1] / strategy_nav.iloc[0]) ** (252 / days) - 1 if days > 0 else 0
    
    # Calculate risk metrics
    sharpe_ratio = strategy_ret.mean() / strategy_ret.std() * np.sqrt(252) if strategy_ret.std() != 0 else 0
    
    # Calculate drawdown
    roll_max = strategy_nav.cummax()
    drawdown = (strategy_nav - roll_max) / roll_max
    max_dd = drawdown.min()
    
    # Calculate Sortino ratio
    neg_ret = strategy_ret[strategy_ret < 0]
    downside_std = np.sqrt(np.mean(neg_ret ** 2)) if len(neg_ret) > 0 else 0
    sortino_ratio = strategy_ret.mean() / downside_std * np.sqrt(252) if downside_std != 0 else 0
    
    # Return metrics as dictionary
    return {
        'total_return': total_return * 100,  # Convert to percentage
        'annual_return': annual_return * 100,  # Convert to percentage
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'max_drawdown': max_dd * 100,  # Convert to percentage
        'alpha': alpha * 100 if not np.isnan(alpha) else None,  # Convert to percentage
        'beta': beta if not np.isnan(beta) else None,
        'information_ratio': info_ratio if not np.isnan(info_ratio) else None
    }

def generate_performance_chart(strategy_nav, benchmark_nav=None, title='Strategy Performance'):
    """
    Generate a performance chart comparing strategy and benchmark
    
    Args:
        strategy_nav: Series of strategy NAV values
        benchmark_nav: Series of benchmark NAV values (optional)
        title: Chart title
        
    Returns:
        str: Base64 encoded chart image
    """
    strategy_nav = pd.Series(strategy_nav)
    
    plt.figure(figsize=(10, 6))
    
    # Plot strategy NAV
    (strategy_nav / strategy_nav.iloc[0]).plot(label='Strategy')
    
    # Plot benchmark NAV if provided
    if benchmark_nav is not None:
        benchmark_nav = pd.Series(benchmark_nav).reindex(strategy_nav.index).fillna(method='ffill')
        (benchmark_nav / benchmark_nav.iloc[0]).plot(label='Benchmark', linestyle='--')
    
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Normalized NAV')
    plt.grid(True)
    plt.legend()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        plt.savefig(tmp.name)
        plt.close()
        
        # Read the file and encode to base64
        with open(tmp.name, 'rb') as f:
            img_data = f.read()
        
        # Clean up
        os.unlink(tmp.name)
    
    # Encode to base64
    encoded = base64.b64encode(img_data).decode('utf-8')
    return encoded