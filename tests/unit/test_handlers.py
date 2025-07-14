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

def test_handle_execute_akshare_code_success_csv():
    """
    Tests successful execution of AkShare code returning a DataFrame, formatted as CSV.
    """
    # Arrange
    code = "import pandas as pd; df = pd.DataFrame({'col1': [1], 'col2': ['A']}); df"
    request = AkShareCodeRequest(code=code, format="csv")
    
    # Act
    response = handle_execute_akshare_code(request)
    
    # Assert
    assert response.error is None
    assert response.format == "csv"
    assert "col1,col2" in response.result
    assert "1,A" in response.result

def test_handle_execute_akshare_code_no_result():
    """
    Tests execution of code that does not produce a recognized result variable.
    """
    # Arrange
    code = "a = 1; b = 2; c = a + b"
    request = AkShareCodeRequest(code=code, format="json")
    
    # Act
    response = handle_execute_akshare_code(request)
    
    # Assert
    assert response.error == "No result found"
    assert "No DataFrame, list, or dict found" in response.result

def test_handle_execute_akshare_code_execution_error():
    """
    Tests execution of code that raises an exception.
    """
    # Arrange
    code = "1 / 0"
    request = AkShareCodeRequest(code=code, format="json")
    
    # Act
    response = handle_execute_akshare_code(request)
    
    # Assert
    assert response.format == "json"
    assert "Error executing AkShare code" in response.error
    assert "division by zero" in response.error

# --- Unit Tests for mcp_handler ---

@pytest.mark.asyncio
@patch('handlers.mcp_handler.akshare_adaptor.call')
async def test_handle_mcp_data_request_success(mock_ak_call):
    """
    Tests a successful MCP data request.
    """
    # Arrange
    mock_df = pd.DataFrame({'data': [1, 2]})
    mock_ak_call.return_value = mock_df
    request = MCPRequest(interface="test_interface", params={"p1": "v1"}, request_id="test1")
    
    # Act
    response = await handle_mcp_data_request(request)
    
    # Assert
    mock_ak_call.assert_called_once_with("test_interface", p1="v1")
    assert response.status == 200
    assert response.request_id == "test1"
    assert response.error is None
    assert response.data == [{'data': 1}, {'data': 2}]

@pytest.mark.asyncio
@patch('handlers.mcp_handler.akshare_adaptor.call')
async def test_handle_mcp_data_request_interface_not_found(mock_ak_call):
    """
    Tests an MCP request for an interface that does not exist.
    """
    # Arrange
    mock_ak_call.side_effect = AttributeError("Function not found")
    request = MCPRequest(interface="non_existent_interface", params={}, request_id="test2")
    
    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await handle_mcp_data_request(request)
    assert "Interface not found" in str(excinfo.value)

@pytest.mark.asyncio
@patch('handlers.mcp_handler.akshare_adaptor.call')
async def test_handle_mcp_data_request_internal_error(mock_ak_call):
    """
    Tests how the handler deals with an unexpected internal error.
    """
    # Arrange
    mock_ak_call.side_effect = ValueError("Internal processing error")
    request = MCPRequest(interface="test_interface", params={}, request_id="test3")
    
    # Act
    response = await handle_mcp_data_request(request)
    
    # Assert
    assert response.status == 500
    assert response.request_id == "test3"
    assert "An internal error occurred" in response.error
    assert "Internal processing error" in response.error
