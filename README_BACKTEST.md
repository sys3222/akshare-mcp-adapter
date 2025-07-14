# MCP Backtest Service

A comprehensive microservice that allows users to upload backtesting files, run them on Backtrader, and return various backtesting metrics. This service integrates both file upload capabilities and AkShare data sources for Chinese market data.

## Features

### 🚀 Core Features
- Upload strategy files (Python) and data files (CSV)
- Run backtests using Backtrader
- AkShare data source integration for Chinese market data
- Get comprehensive metrics (total return, Sharpe ratio, drawdown, etc.)
- Visualize performance with charts
- Web interface and RESTful API

### 📊 Data Sources
- **File Upload**: CSV files with OHLC data
- **AkShare Integration**: Chinese ETF and index data

### 🎯 Performance Metrics
- Return metrics (total, annual, monthly)
- Risk metrics (Sharpe, Sortino, max drawdown)
- Trade statistics (win rate, profit factor)
- Benchmark comparison (Alpha, Beta, Information Ratio)

## Requirements

- Python 3.9+
- FastAPI
- Backtrader
- Pandas
- Matplotlib
- AkShare

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp_backtest_service
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the service

For development:
```bash
./run_service.sh
```

For production:
```bash
./run_production.sh
```

The service will be available at:
- Web interface: http://localhost:12000
- API documentation: http://localhost:12000/docs

### Using Docker

1. Build the Docker image:
```bash
docker build -t mcp-backtest-service .
```

2. Run the container:
```bash
docker run -p 12000:12000 mcp-backtest-service
```

## API Endpoints

### POST /api/backtest

Upload strategy and data files to run a backtest.

**Request:**
- Form data:
  - `strategy_file`: Python file containing a Backtrader strategy class
  - `data_file`: CSV file with price data (must have Open, High, Low, Close columns)
  - `params` (optional): JSON string with strategy parameters

**Response:**
```json
{
  "metrics": {
    "total_return": 15.7,
    "sharpe_ratio": 1.2,
    "max_drawdown": 5.3,
    "total_trades": 42,
    "win_rate": 65.2,
    "profit_factor": 2.1,
    "avg_trade_duration": 4.5
  },
  "chart": "base64_encoded_image_data"
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

### GET /api/data-sources

Get available data sources.

**Response:**
```json
{
  "akshare": {
    "etf": ["黄金ETF", "纳指100", ...],
    "index": ["上证指数", "沪深300", ...]
  }
}
```

## Sample Strategies

The service includes sample strategies in the `tests/` directory:

1. **Simple Moving Average Strategy** (`sample_strategy.py`):
   - Uses 20-day and 50-day moving averages
   - Buy when short MA crosses above long MA
   - Sell when short MA crosses below long MA

2. **ETF Momentum Strategy** (`etf_momentum_strategy.py`):
   - Momentum-based strategy for ETF trading
   - Uses RSI and moving averages for signals

## Data Sources

### File Upload
- CSV files with OHLC data
- Required columns: Date, Open, High, Low, Close
- Optional: Volume

### AkShare Integration
The service integrates with AkShare to provide Chinese market data:

**ETF Data:**
- 黄金ETF (518880)
- 纳指100 (513100)
- 创业板100 (159915)
- 上证180 (510180)
- 沪深300ETF (510300)

**Index Data:**
- 上证指数 (000001)
- 沪深300 (000300)
- 中证500 (000905)
- 深证成指 (399001)
- 创业板指 (399006)

## Performance Metrics

The service calculates comprehensive performance metrics:

- **Return Metrics**: Total return, annual return, monthly returns
- **Risk Metrics**: Sharpe ratio, Sortino ratio, maximum drawdown
- **Trade Statistics**: Total trades, win rate, profit factor
- **Benchmark Comparison**: Alpha, beta, information ratio

## Web Interface

The web interface provides:
- File upload for strategy and data files
- AkShare data source selection
- Real-time backtest execution
- Results visualization
- Performance metrics display

## Development

### Project Structure
```
├── api/                  # API endpoints
├── core/                 # Core backtesting functionality
├── models/               # Data models and schemas
├── static/               # Web interface files
├── tests/                # Test files and sample strategies
├── utils/                # Utility functions
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Strategies
1. Create a new Python file in the `tests/` directory
2. Define a class that inherits from `bt.Strategy`
3. Implement the required methods (`__init__`, `next`)
4. Upload through the web interface or API

## License

[MIT License](LICENSE)