import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from pathlib import Path
from io import BytesIO
from fastapi import HTTPException, UploadFile
import backtrader as bt
import json

from handlers.data_source_handler import handle_get_data_sources
from handlers.akshare_handler import handle_execute_akshare_code
from handlers.mcp_handler import handle_mcp_data_request
from handlers.file_management_handler import (
    get_user_cache_dir,
    list_user_files,
    delete_user_file,
    save_uploaded_file,
)
from handlers.data_exploration_handler import handle_explore_data_from_file
from handlers.backtest_handler import (
    _load_strategy_class,
    handle_run_backtest_from_files,
    handle_backtest_with_code_only,
)
from models.schemas import AkShareCodeRequest, BacktestRequest
from core.mcp_protocol import MCPRequest

# --- Unit Tests for data_source_handler ---

@patch('handlers.data_source_handler.get_available_data_sources')
def test_handle_get_data_sources(mock_get_sources):
    """
    Tests if the data source handler correctly formats the output from the core function.
    """
    # Arrange
    mock_get_sources.return_value = {
        "etf": {"name": "ETFs", "description": "Exchange Traded Funds", "symbols": {"510300": "沪深300ETF", "518880": "黄金ETF"}},
        "index": {"name": "Indices", "description": "Stock Market Indices", "symbols": {"000300": "沪深300", "000905": "中证500"}}
    }
    
    # Act
    result = handle_get_data_sources()
    
    # Assert
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
    code = "import pandas as pd; result_df = pd.DataFrame({'A': [1], 'B': [2]})"
    request = AkShareCodeRequest(code=code, format="csv")
    
    # Act
    response = handle_execute_akshare_code(request)
    
    # Assert
    assert response.error is None
    assert response.format == "csv"
    expected_csv = "A,B\n1,2\n"
    assert response.result.replace('\r\n', '\n') == expected_csv


def test_handle_execute_akshare_code_no_result():
    """
    Tests execution of code that does not produce a recognized result variable.
    """
    # Arrange
    code = "x = 1; y = 2; z = x + y"
    request = AkShareCodeRequest(code=code, format="json")
    
    # Act
    response = handle_execute_akshare_code(request)
    
    # Assert
    assert response.error == "No result found"
    assert "No DataFrame, list, or dict found" in response.result


def test_handle_execute_akshare_code_execution_error():
    """
    Tests handling of code that raises an exception during execution.
    """
    # Arrange
    code = "import pandas as pd; df = pd.DataFrame({'A': [1]}); non_existent_function()"
    request = AkShareCodeRequest(code=code, format="json")
    
    # Act
    response = handle_execute_akshare_code(request)
    
    # Assert
    assert response.error is not None
    assert "Error executing AkShare code" in response.error
    assert "non_existent_function" in response.error


# --- Unit Tests for mcp_handler ---

@pytest.mark.asyncio
@patch('handlers.mcp_handler.akshare_adaptor.call')
async def test_handle_mcp_data_request_success(mock_akshare_call):
    """
    Tests a successful data request through the MCP handler.
    """
    # Arrange
    mock_df = pd.DataFrame({'date': pd.to_datetime(['2023-01-01']), 'value': [100]})
    mock_akshare_call.return_value = mock_df
    
    request = MCPRequest(interface="test_interface", params={"symbol": "123"}, request_id="test1")
    
    # Act
    response = await handle_mcp_data_request(request)
    
    # Assert
    assert response.error is None
    assert response.request_id == "test1"
    assert response.total_records == 1
    assert response.data == [{'date': '2023-01-01 00:00:00', 'value': 100}]
    mock_akshare_call.assert_called_once_with("test_interface", symbol="123")


@pytest.mark.asyncio
@patch('handlers.mcp_handler.akshare_adaptor.call')
async def test_handle_mcp_data_request_pagination(mock_akshare_call):
    """
    Tests if pagination is correctly applied to the data.
    """
    # Arrange
    mock_df = pd.DataFrame({'id': range(50)})
    mock_akshare_call.return_value = mock_df
    
    request = MCPRequest(interface="test_interface", params={}, request_id="test2")
    
    # Act
    response = await handle_mcp_data_request(request, page=2, page_size=20)
    
    # Assert
    assert response.total_records == 50
    assert response.current_page == 2
    assert response.total_pages == 3
    assert len(response.data) == 20
    assert response.data[0]['id'] == 20
    assert response.data[-1]['id'] == 39


@pytest.mark.asyncio
@patch('handlers.mcp_handler.akshare_adaptor.call')
async def test_handle_mcp_data_request_unsupported_interface(mock_akshare_call):
    """
    Tests the handler's response for an unsupported (non-existent) interface.
    """
    # Arrange
    mock_akshare_call.side_effect = AttributeError("module 'akshare' has no attribute 'non_existent_interface'")
    request = MCPRequest(interface="non_existent_interface", params={}, request_id="test4")
    
    # Act/Assert
    with pytest.raises(HTTPException) as excinfo:
        await handle_mcp_data_request(request)
    
    assert "Interface not found" in str(excinfo.value.detail)
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
@patch('handlers.mcp_handler.akshare_adaptor.call')
async def test_fetch_akshare_data_with_retry_logic(mock_akshare_call):
    """
    Tests the retry logic by simulating failures then success.
    """
    # Arrange
    final_result = pd.DataFrame({'data': ['success']})
    mock_akshare_call.side_effect = [
        ValueError("Attempt 1 failed"),
        ValueError("Attempt 2 failed"),
        final_result
    ]
    
    request = MCPRequest(interface="retry_test", params={}, request_id="test_retry")

    # Act
    response = await handle_mcp_data_request(request)

    # Assert
    assert mock_akshare_call.call_count == 3
    assert response.error is None
    assert response.data == [{'data': 'success'}]

@pytest.mark.asyncio
@patch('handlers.mcp_handler.akshare_adaptor.call')
async def test_fetch_akshare_data_retry_fails_permanently(mock_akshare_call):
    """
    Tests the retry logic when all attempts fail.
    """
    # Arrange
    mock_akshare_call.side_effect = ValueError("Permanent failure")
    request = MCPRequest(interface="retry_fail_test", params={}, request_id="test_retry_fail")

    # Act
    response = await handle_mcp_data_request(request)

    # Assert
    assert mock_akshare_call.call_count == 3
    assert response.error is not None
    assert "Permanent failure" in response.error

@pytest.mark.asyncio
@patch('handlers.mcp_handler._get_and_normalize_akshare_data')
async def test_handle_mcp_data_request_data_size_exceeded(mock_get_data):
    """
    Tests that a DataSizeExceededError is converted to an HTTPException.
    """
    from handlers.mcp_handler import DataSizeExceededError
    # Arrange
    error_message = "Data size limit exceeded"
    mock_get_data.side_effect = DataSizeExceededError(error_message)
    request = MCPRequest(interface="large_data_test", params={}, request_id="test_large_data")

    # Act / Assert
    with pytest.raises(HTTPException) as excinfo:
        await handle_mcp_data_request(request)
    
    assert excinfo.value.status_code == 413
    assert error_message in excinfo.value.detail


# --- Unit Tests for file_management_handler ---

@pytest.fixture
def temp_user_cache(tmp_path):
    """Fixture to create a temporary cache structure for file management tests."""
    base_dir = tmp_path / "static" / "cache"
    user_dir = base_dir / "testuser"
    user_dir.mkdir(parents=True, exist_ok=True)
    
    (user_dir / "test_file.txt").write_text("hello")
    
    with patch('handlers.file_management_handler.CACHE_BASE_DIR', base_dir):
        yield base_dir

def test_get_user_cache_dir(temp_user_cache):
    """Tests the creation and retrieval of a user's cache directory."""
    user_dir = get_user_cache_dir("testuser")
    assert user_dir.exists()
    assert user_dir.name == "testuser"
    assert "testuser" in str(user_dir)

def test_list_user_files(temp_user_cache):
    """Tests listing files in a user's directory."""
    files = list_user_files("testuser")
    assert files == ["test_file.txt"]

def test_delete_user_file(temp_user_cache):
    """Tests deleting a file from a user's directory."""
    assert "test_file.txt" in list_user_files("testuser")
    
    result = delete_user_file("test_file.txt", "testuser")
    assert result["detail"] == "File deleted successfully."
    
    assert "test_file.txt" not in list_user_files("testuser")

def test_delete_non_existent_file(temp_user_cache):
    """Tests attempting to delete a file that does not exist."""
    with pytest.raises(HTTPException) as excinfo:
        delete_user_file("non_existent.txt", "testuser")
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_save_uploaded_file(temp_user_cache):
    """Tests saving an uploaded file."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "new_upload.csv"
    mock_file.file = BytesIO(b"col1,col2\n1,2")

    result = await save_uploaded_file(mock_file, "testuser")
    assert result["filename"] == "new_upload.csv"
    
    files = list_user_files("testuser")
    assert "new_upload.csv" in files
    
    user_dir = get_user_cache_dir("testuser")
    content = (user_dir / "new_upload.csv").read_text()
    assert content == "col1,col2\n1,2"


# --- Unit Tests for data_exploration_handler ---

@pytest.fixture
def temp_csv_file(tmp_path):
    """Fixture to create a temporary CSV file for data exploration tests."""
    d = tmp_path / "data"
    d.mkdir()
    p = d / "test_data.csv"
    df = pd.DataFrame({'A': range(100), 'B': [f"text_{i}" for i in range(100)]})
    df.to_csv(p, index=False)
    return p

@pytest.mark.asyncio
async def test_handle_explore_data_from_file(temp_csv_file):
    """Tests reading and paginating data from a CSV file."""
    result = await handle_explore_data_from_file(temp_csv_file, page=1, page_size=20)
    assert result["current_page"] == 1
    assert result["total_pages"] == 5
    assert result["total_records"] == 100
    assert len(result["data"]) == 20
    assert result["data"][0]['A'] == 0

    result_last_page = await handle_explore_data_from_file(temp_csv_file, page=5, page_size=20)
    assert result_last_page["current_page"] == 5
    assert len(result_last_page["data"]) == 20
    assert result_last_page["data"][-1]['A'] == 99

@pytest.mark.asyncio
async def test_handle_explore_data_file_not_found(tmp_path):
    """Tests handling of a non-existent file."""
    non_existent_path = tmp_path / "non_existent.csv"
    with pytest.raises(HTTPException) as excinfo:
        await handle_explore_data_from_file(non_existent_path, page=1, page_size=10)
    assert excinfo.value.status_code == 400
    assert "Failed to process file" in excinfo.value.detail

# --- Unit Tests for backtest_handler ---

# A simple backtrader strategy for testing
STRATEGY_CODE = """
import backtrader as bt

class TestStrategy(bt.Strategy):
    params = (('exitbars', 5),)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.dataclose[0] > self.dataclose[-1]:
                self.order = self.buy()
        else:
            if len(self) >= (self.p.exitbars + self.bar_executed):
                self.order = self.sell()
"""

class MockStrategy(bt.Strategy):
    pass

@pytest.fixture
def temp_strategy_file(tmp_path):
    """Fixture to create a temporary strategy file."""
    p = tmp_path / "strategy.py"
    p.write_text(STRATEGY_CODE)
    return str(p)

def test_load_strategy_class(temp_strategy_file):
    """Tests dynamically loading a strategy class from a file."""
    strategy_class = _load_strategy_class(temp_strategy_file)
    assert strategy_class is not None
    assert strategy_class.__name__ == "TestStrategy"
    assert issubclass(strategy_class, bt.Strategy)

def test_load_strategy_class_no_strategy_found(tmp_path):
    """Tests loading a file that does not contain a valid strategy."""
    p = tmp_path / "no_strategy.py"
    p.write_text("print('hello')")
    with pytest.raises(ValueError) as excinfo:
        _load_strategy_class(str(p))
    assert "No Backtrader strategy class found" in str(excinfo.value)

@pytest.mark.asyncio
@patch('handlers.backtest_handler.run_backtest')
@patch('handlers.backtest_handler._load_strategy_class')
@patch('handlers.backtest_handler.get_user_file_path')
async def test_handle_run_backtest_from_files(mock_get_path, mock_load_class, mock_run_backtest):
    """Tests running a backtest from user-uploaded files."""
    # Arrange
    mock_get_path.return_value = MagicMock(spec=Path, exists=lambda: True)
    mock_load_class.return_value = MockStrategy
    mock_run_backtest.return_value = {"result": "success"}
    
    request = BacktestRequest(
        strategy_file="strategy.py",
        data_file="data.csv",
        cash=10000,
        commission=0.001,
        params={"exitbars": 10}
    )
    
    # Act
    result = await handle_run_backtest_from_files(request, "testuser")
    
    # Assert
    assert result == {"result": "success"}
    mock_get_path.assert_any_call("strategy.py", "testuser")
    mock_get_path.assert_any_call("data.csv", "testuser")
    mock_load_class.assert_called_once()
    mock_run_backtest.assert_called_once_with(
        strategy_class=MockStrategy,
        data_path=str(mock_get_path.return_value),
        cash=10000,
        commission=0.001,
        params_str=json.dumps({"exitbars": 10})
    )

@pytest.mark.asyncio
@patch('handlers.backtest_handler.run_backtest')
@patch('handlers.backtest_handler._load_strategy_class')
async def test_handle_backtest_with_code_only(mock_load_class, mock_run_backtest):
    """Tests running a backtest from raw strategy code."""
    # Arrange
    mock_load_class.return_value = MockStrategy
    mock_run_backtest.return_value = {"result": "code_success"}
    
    # Act
    result = await handle_backtest_with_code_only(
        strategy_code=STRATEGY_CODE,
        symbol="000001",
        start_date="20230101",
        end_date="20231231",
        params={"exitbars": 20},
        benchmark_symbol="000300"
    )
    
    # Assert
    assert result == {"result": "code_success"}
    mock_load_class.assert_called_once()
    mock_run_backtest.assert_called_once_with(
        strategy_class=MockStrategy,
        data_path="akshare:000001:20230101:20231231",
        params_str=json.dumps({"exitbars": 20}),
        benchmark_symbol="000300"
    )
