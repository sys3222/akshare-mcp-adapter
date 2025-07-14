from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class BacktestMetrics(BaseModel):
    """Metrics from a backtest run"""
    total_return: float = Field(..., description="Total return percentage")
    annual_return: float = Field(..., description="Annualized return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    total_trades: int = Field(..., description="Total number of trades")
    win_rate: float = Field(..., description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor (gross profit / gross loss)")
    avg_trade_duration: float = Field(..., description="Average trade duration in bars")
    alpha: Optional[float] = Field(None, description="Alpha (annualized, vs benchmark)")
    beta: Optional[float] = Field(None, description="Beta (vs benchmark)")
    information_ratio: Optional[float] = Field(None, description="Information ratio (vs benchmark)")

class BacktestResult(BaseModel):
    """Result of a backtest run"""
    metrics: BacktestMetrics = Field(..., description="Backtest metrics")
    chart: str = Field(..., description="Base64 encoded chart image")
    nav_data: Optional[List[float]] = Field(None, description="Strategy NAV values")
    benchmark_data: Optional[List[float]] = Field(None, description="Benchmark NAV values")
    dates: Optional[List[str]] = Field(None, description="Dates for NAV values")
    
class DataSourceInfo(BaseModel):
    """Information about available data sources"""
    name: str = Field(..., description="Data source name")
    description: str = Field(..., description="Data source description")
    symbols: Dict[str, str] = Field(..., description="Available symbols (symbol: description)")
    
class DataSourceList(BaseModel):
    """List of available data sources"""
    sources: List[DataSourceInfo] = Field(..., description="Available data sources")