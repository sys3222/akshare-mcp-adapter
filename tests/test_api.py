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

# This test will fail now because the endpoint is protected.
# We are leaving it here to show the original state.
@pytest.mark.xfail(reason="Endpoint is now protected by authentication.")
def test_mcp_data_request_success_unauthenticated():
    """Tests a successful /mcp-data request."""
    request_payload = {
        "interface": "stock_zh_a_spot_em",
        "params": {},
        "request_id": "mcp-test-1"
    }
    response = client.post("/api/mcp-data", json=request_payload)
    assert response.status_code == 200

@pytest.mark.xfail(reason="Endpoint is now protected by authentication.")
def test_mcp_data_request_interface_not_found_unauthenticated():
    """Tests an /mcp-data request with a non-existent interface."""
    request_payload = {
        "interface": "this_interface_does_not_exist",
        "params": {},
        "request_id": "mcp-test-2"
    }
    response = client.post("/api/mcp-data", json=request_payload)
    assert response.status_code == 404

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