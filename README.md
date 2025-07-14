# MCP Backtest Service

A microservice that allows users to upload backtesting files, run them on Backtrader, and return various backtesting metrics.

## Features

- Upload strategy files (Python) and data files (CSV)
- Run backtests using Backtrader
- Get comprehensive metrics (total return, Sharpe ratio, drawdown, etc.)
- Visualize performance with charts

## Requirements

- Python 3.9+
- FastAPI
- Backtrader
- Pandas
- Matplotlib

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

## Web Interface

A simple web interface is available at the root URL (/) for uploading files and viewing backtest results.

## Creating Strategy Files

Strategy files should contain a class that inherits from `bt.Strategy`. Example:

```python
import backtrader as bt

class MyStrategy(bt.Strategy):
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
    def next(self):
        if self.crossover > 0:
            self.buy()
        elif self.crossover < 0:
            self.sell()
```

## Data File Format

Data files should be in CSV format with at least the following columns:
- Date/Time
- Open
- High
- Low
- Close

Optional columns:
- Volume
- OpenInterest

Example:
```
Date,Open,High,Low,Close,Volume
2020-01-01,100.0,102.5,99.5,101.2,10000
2020-01-02,101.3,103.0,100.8,102.7,12000
...
```

## License

[MIT License](LICENSE)