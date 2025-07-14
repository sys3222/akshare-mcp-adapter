import backtrader as bt
import pandas as pd
import json
import os
from typing import Dict, Any, Type, Optional, List, Tuple
import tempfile
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime

from models.schemas import BacktestResult, BacktestMetrics
from utils.performance_utils import analyze_performance, generate_performance_chart
from utils.akshare_utils import get_akshare_etf_data, get_index_nav

class MetricsAnalyzer(bt.Analyzer):
    """Analyzer to collect various trading metrics"""
    
    def get_analysis(self):
        return {
            "total_return": self.strategy.broker.getvalue() / self.strategy.broker.startingcash - 1.0,
            "ending_value": self.strategy.broker.getvalue(),
            "starting_value": self.strategy.broker.startingcash,
            "total_trades": self.strategy._tradeid if hasattr(self.strategy, '_tradeid') else 0
        }

def run_backtest(
    strategy_class: Type[bt.Strategy], 
    data_path: str, 
    params_str: Optional[str] = None,
    benchmark_symbol: Optional[str] = None
) -> BacktestResult:
    """
    Run a backtest using the provided strategy and data
    
    Args:
        strategy_class: The backtrader Strategy class
        data_path: Path to the data file or AkShare symbol (e.g., 'akshare:518880')
        params_str: JSON string of strategy parameters
        benchmark_symbol: Symbol for benchmark index (e.g., '000300' for CSI 300)
    
    Returns:
        BacktestResult object with metrics and charts
    """
    # Parse parameters if provided
    params = {}
    if params_str:
        try:
            params = json.loads(params_str)
        except json.JSONDecodeError:
            pass
    
    # Initialize cerebro engine
    cerebro = bt.Cerebro()
    
    # Add strategy
    cerebro.addstrategy(strategy_class, **params)
    
    # Load data and get date range
    data_feed, start_date, end_date = load_data(data_path)
    
    # Add data feed to cerebro
    cerebro.adddata(data_feed)
    
    # Set broker parameters
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Add analyzers
    cerebro.addanalyzer(MetricsAnalyzer, _name='metrics')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Run the backtest
    results = cerebro.run()
    strat = results[0]
    
    # Extract metrics
    metrics_analysis = strat.analyzers.metrics.get_analysis()
    sharpe_analysis = strat.analyzers.sharpe.get_analysis()
    drawdown_analysis = strat.analyzers.drawdown.get_analysis()
    trades_analysis = strat.analyzers.trades.get_analysis()
    
    # Extract NAV values
    length = data_feed.buflen()
    dates = [data_feed.datetime.date(-i).isoformat() for i in range(length)]
    dates.reverse()
    
    # Get strategy NAV
    if hasattr(strat, 'navs') and strat.navs:
        nav_values = strat.navs
    else:
        # Calculate NAV from broker value
        initial_value = cerebro.broker.startingcash
        final_value = cerebro.broker.getvalue()
        # Create a simple linear interpolation for NAV
        nav_values = [initial_value + (final_value - initial_value) * i / (length - 1) for i in range(length)]
    
    # Get benchmark data if specified
    benchmark_values = None
    if benchmark_symbol:
        try:
            benchmark_values = get_index_nav(benchmark_symbol, start_date, end_date)
            benchmark_values = benchmark_values.reindex(pd.DatetimeIndex(dates)).fillna(method='ffill').tolist()
        except Exception as e:
            print(f"Error getting benchmark data: {str(e)}")
    
    # Calculate performance metrics
    perf_metrics = analyze_performance(nav_values, benchmark_values)
    
    # Generate performance chart
    chart_data = generate_performance_chart(nav_values, benchmark_values, 'Strategy Performance')
    
    # Safely extract metrics
    def safe_get(obj, *keys, default=0.0):
        """Safely get a nested value from an object"""
        try:
            for key in keys:
                if hasattr(obj, 'get'):
                    obj = obj.get(key, {})
                elif hasattr(obj, key):
                    obj = getattr(obj, key)
                else:
                    return default
            return obj if obj is not None else default
        except (AttributeError, KeyError, TypeError):
            return default
    
    # Calculate win rate safely
    total_trades = safe_get(trades_analysis, 'total', 'total', default=0)
    won_trades = safe_get(trades_analysis, 'won', 'total', default=0)
    win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0.0
    
    # Calculate profit factor safely
    try:
        won_pnl = safe_get(trades_analysis, 'won', 'pnl', default=0.0)
        if isinstance(won_pnl, dict) or hasattr(won_pnl, 'get'):
            won_pnl = 0.0
            
        lost_pnl = safe_get(trades_analysis, 'lost', 'pnl', default=0.0)
        if isinstance(lost_pnl, dict) or hasattr(lost_pnl, 'get'):
            lost_pnl = 0.0
            
        profit_factor = won_pnl / abs(float(lost_pnl)) if lost_pnl != 0 else 1.0
    except Exception as e:
        print(f"Error calculating profit factor: {str(e)}")
        profit_factor = 1.0
    
    # Get average trade duration safely
    try:
        avg_duration = safe_get(trades_analysis, 'len', 'avg', default=0.0)
        if isinstance(avg_duration, dict) or hasattr(avg_duration, 'get'):
            avg_duration = 0.0
    except Exception as e:
        print(f"Error getting avg_trade_duration: {str(e)}")
        avg_duration = 0.0
    
    # Compile metrics
    metrics = BacktestMetrics(
        total_return=perf_metrics['total_return'],
        annual_return=perf_metrics['annual_return'],
        sharpe_ratio=perf_metrics['sharpe_ratio'],
        sortino_ratio=perf_metrics['sortino_ratio'],
        max_drawdown=perf_metrics['max_drawdown'],
        total_trades=total_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
        avg_trade_duration=float(avg_duration),
        alpha=perf_metrics.get('alpha'),
        beta=perf_metrics.get('beta'),
        information_ratio=perf_metrics.get('information_ratio')
    )
    
    # Return results
    return BacktestResult(
        metrics=metrics,
        chart=chart_data,
        nav_data=nav_values,
        benchmark_data=benchmark_values,
        dates=dates
    )

def load_data(data_path: str) -> Tuple[bt.feeds.DataBase, str, str]:
    """
    Load data from file or AkShare
    
    Args:
        data_path: Path to the data file or AkShare symbol (e.g., 'akshare:518880')
        
    Returns:
        Tuple of (data_feed, start_date, end_date)
    """
    # Check if it's an AkShare symbol
    if data_path.startswith('akshare:'):
        symbol = data_path.split(':')[1]
        # Use default date range if not specified
        start_date = '2020-01-01'
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Get data from AkShare
        data_feed = get_akshare_etf_data(symbol, start_date, end_date)
        return data_feed, start_date, end_date
    
    # Load from file
    if data_path.endswith('.csv'):
        # Determine format based on column names
        df = pd.read_csv(data_path)
        
        # Convert date column to datetime if it exists
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                df[col] = pd.to_datetime(df[col])
                date_col = col
                break
        
        # Get date range
        if date_col:
            start_date = df[date_col].min().strftime('%Y-%m-%d')
            end_date = df[date_col].max().strftime('%Y-%m-%d')
        else:
            start_date = '2020-01-01'  # Default
            end_date = datetime.now().strftime('%Y-%m-%d')  # Default
        
        # Check if it's a standard OHLCV format
        required_cols = ['open', 'high', 'low', 'close']
        has_required = all(col.lower() in map(str.lower, df.columns) for col in required_cols)
        
        if has_required:
            # Convert column names to lowercase for easier matching
            df.columns = [col.lower() for col in df.columns]
            
            # Create data feed
            if date_col:
                data_feed = bt.feeds.PandasData(
                    dataname=df,
                    datetime=date_col.lower(),
                    open='open',
                    high='high',
                    low='low',
                    close='close',
                    volume='volume' if 'volume' in df.columns else None,
                    openinterest=None
                )
            else:
                # Use index as datetime
                data_feed = bt.feeds.PandasData(
                    dataname=df,
                    open='open',
                    high='high',
                    low='low',
                    close='close',
                    volume='volume' if 'volume' in df.columns else None,
                    openinterest=None
                )
        else:
            # Generic CSV format
            data_feed = bt.feeds.GenericCSVData(
                dataname=data_path,
                dtformat='%Y-%m-%d',
                datetime=0,
                open=1,
                high=2,
                low=3,
                close=4,
                volume=5,
                openinterest=-1
            )
    else:
        # Unsupported format
        raise ValueError(f"Unsupported data file format: {data_path}")
    
    return data_feed, start_date, end_date

def get_available_data_sources() -> Dict[str, Dict[str, Any]]:
    """
    Get information about available data sources
    
    Returns:
        Dict of data sources
    """
    return {
        "akshare_etf": {
            "name": "AkShare ETF",
            "description": "Chinese ETF data from AkShare",
            "symbols": {
                "518880": "黄金ETF",
                "513100": "纳指100",
                "159915": "创业板100",
                "510180": "上证180",
                "510300": "沪深300ETF",
                "510500": "中证500ETF",
                "512100": "中证1000ETF"
            }
        },
        "akshare_index": {
            "name": "AkShare Index",
            "description": "Chinese index data from AkShare",
            "symbols": {
                "000001": "上证指数",
                "000300": "沪深300",
                "000905": "中证500",
                "399001": "深证成指",
                "399006": "创业板指"
            }
        }
    }