import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from handlers.data_source_handler import handle_get_data_sources
from handlers.akshare_handler import handle_execute_akshare_code
from handlers.mcp_handler import handle_mcp_data_request
from models.schemas import AkShareCodeRequest, AkShareCodeResponse
from core.mcp_protocol import MCPRequest

# --- Unit Tests for data_source_handler ---

@patch('handlers.data_source_handler.get_available_data_sources')
def test_handle_get_data_sources(mock_get_sources):
    """
    Tests if the data source handler correctly formats the output from the core function.
    """
    # Arrange: Mock the data returned by the core function
    mock_get_sources.return_value = {
        "etf": {"name": "ETFs", "description": "Exchange Traded Funds", "symbols": {"510300": "沪深300ETF", "518880": "黄金ETF"}},
        "index": {"name": "Indices", "description": "Stock Market Indices", "symbols": {"000300": "沪深300", "000905": "中证500"}}
    }
    
    # Act: Call the handler
    result = handle_get_data_sources()
    
    # Assert: Check if the output is correctly transformed into Pydantic models
    assert len(result.sources) == 2
    assert result.sources[0].name == "ETFs"
    assert result.sources[0].symbols == {"510300": "沪深300ETF", "518880": "黄金ETF"}
    assert result.sources[1].description == "Stock Market Indices"

# --- Unit Tests for akshare_handler ---

def test_handle_execute_akshare_code_success_json():
    """
    Tests successful execution of AkShare code returning a DataFrame, formatted as JSON.
    """
    # Arrange
    code = "import pandas as pd; df = pd.DataFrame({'col1': [1, 2], 'col2': ['A', 'B']}); df"
    request = AkShareCodeRequest(code=code, format="json")
    
    # Act
    response = handle_execute_akshare_code(request)
    
    # Assert
    assert response.error is None
    assert response.format == "json"
    assert response.result == [{"col1": 1, "col2": "A"}, {"col1": 2, "col2": "B"}]
