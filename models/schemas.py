from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

# --- User Schemas ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Existing Schemas ---

class AkShareCodeRequest(BaseModel):
    """Request to execute AkShare code"""
    code: str = Field(..., description="AkShare code to execute")
    format: str = Field("json", description="Output format (json, csv, html)")

class AkShareCodeResponse(BaseModel):
    """Response from executing AkShare code"""
    result: Union[List[Dict[str, Any]], str] = Field(..., description="Result of executing the code")
    format: str = Field(..., description="Format of the result (json, csv, html)")
    error: Optional[str] = Field(None, description="Error message if execution failed")

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

class PaginatedDataResponse(BaseModel):
    """A paginated response for any list of data."""
    data: List[Dict[str, Any]] = Field(..., description="The data for the current page.")
    total_records: int = Field(..., description="Total number of records available.")
    current_page: int = Field(..., description="The current page number.")
    total_pages: int = Field(..., description="Total number of pages.")
    request_id: Optional[str] = Field(None, description="Optional request identifier.")
    error: Optional[str] = Field(None, description="Error message if the request failed.")

# --- LLM Analysis Schemas ---

class LLMAnalysisRequest(BaseModel):
    """Request for LLM intelligent analysis"""
    query: str = Field(..., description="User's natural language query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")

class LLMAnalysisResponse(BaseModel):
    """Response from LLM intelligent analysis"""
    summary: str = Field(..., description="Analysis summary")
    insights: List[str] = Field(..., description="Key insights from the analysis")
    recommendations: List[str] = Field(..., description="Investment recommendations")
    data_points: Dict[str, Any] = Field(..., description="Key data points")
    charts_suggested: List[str] = Field(..., description="Suggested chart types")
    risk_level: str = Field(..., description="Risk assessment level")
    confidence: float = Field(..., description="Analysis confidence score")
    intent_detected: str = Field(..., description="Detected user intent")
    entities_extracted: Dict[str, Any] = Field(..., description="Extracted entities")