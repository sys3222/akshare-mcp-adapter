import pytest
from fastapi.testclient import TestClient
import os
import json

# Add project root to path to allow importing 'main'
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app  # Import the FastAPI app

client = TestClient(app)

# --- Test Data ---
SAMPLE_STRATEGY_CODE = """
import backtrader as bt

class SimpleMAStrategy(bt.Strategy):
    params = (('fast_period', 10), ('slow_period', 30))
    
    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.sell()
"""

# --- API Tests ---

def test_health_check():
    """Tests the /health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_data_sources():
    """Tests the /data-sources endpoint."""
    response = client.get("/api/data-sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0
    assert "name" in data["sources"][0]
    assert "symbols" in data["sources"][0]

def test_mcp_data_request_success():
    """Tests a successful /mcp-data request."""
    # First, get a valid interface name from the /api/interfaces endpoint
    interfaces_response = client.get("/api/interfaces")
    assert interfaces_response.status_code == 200
    interfaces_data = interfaces_response.json()
    # Use a simple, reliable interface from the list
    valid_interface = interfaces_data["interfaces"]["股票数据"][1]["name"] # "stock_zh_a_spot_em"

    request_payload = {
        "interface": valid_interface,
        "params": {},
        "request_id": "mcp-test-1"
    }
    response = client.post("/api/mcp-data", json=request_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "mcp-test-1"
    assert data["status"] == 200
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0
    assert "代码" in data["data"][0] # "stock_zh_a_spot_em" should have '代码' column

def test_mcp_data_request_interface_not_found():
    """Tests an /mcp-data request with a non-existent interface."""
    request_payload = {
        "interface": "this_interface_does_not_exist",
        "params": {},
        "request_id": "mcp-test-2"
    }
    response = client.post("/api/mcp-data", json=request_payload)
    assert response.status_code == 404  # Expecting Not Found
    assert "Interface not found" in response.json()["detail"]

def test_execute_akshare_code_success():
    """Tests the /execute-akshare endpoint with valid code."""
    request_payload = {
        "code": "import pandas as pd; df = pd.DataFrame({'c': [1,2]}); df",
        "format": "json"
    }
    response = client.post("/api/execute-akshare", json=request_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["error"] is None
    assert data["result"] == [{"c": 1}, {"c": 2}]

def test_execute_akshare_code_error():
    """Tests the /execute-akshare endpoint with code that will fail."""
    request_payload = {
        "code": "1 / 0",
        "format": "json"
    }
    response = client.post("/api/execute-akshare", json=request_payload)
    # The endpoint itself should still return 200, with the error in the payload
    assert response.status_code == 200
    data = response.json()
    assert "Error executing AkShare code" in data["error"]

@pytest.mark.skip(reason="This test requires a large data download and can be slow.")
def test_backtest_with_code_only():
    """
    Tests the /backtest-code endpoint.
    This is a full integration test and may be slow.
    """
    request_payload = {
        "strategy_code": SAMPLE_STRATEGY_CODE,
        "symbol": "000300",  # Use a common index to ensure data availability
        "start_date": "2023-01-01",
        "end_date": "2023-03-31",
        "params": {"fast_period": 5, "slow_period": 10},
        "benchmark_symbol": "000300"
    }
    response = client.post("/api/backtest-code", json=request_payload)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "Total Return [%]" in data["metrics"]
    assert "Sharpe Ratio" in data["metrics"]
    assert "chart_html" in data
    assert data["chart_html"].startswith("<div")

def test_backtest_with_uploaded_files():
    """Tests the /backtest endpoint with file uploads."""
    strategy_path = os.path.join(os.path.dirname(__file__), 'sample_strategies', 'simple_ma_strategy.py')
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_data.csv')

    with open(strategy_path, 'rb') as strategy_file, open(data_path, 'rb') as data_file:
        files = {
            'strategy_file': ('simple_ma_strategy.py', strategy_file, 'text/x-python'),
            'data_file': ('sample_data.csv', data_file, 'text/csv')
        }
        response = client.post("/api/backtest", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "max_drawdown" in data["metrics"]
    assert "chart" in data
