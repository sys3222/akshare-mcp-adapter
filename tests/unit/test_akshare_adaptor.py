import asyncio
import pandas as pd
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from adaptors.akshare import AKShareAdaptor

# Use pytest's tmp_path fixture for a temporary cache directory
@pytest.fixture
def temp_cache_dir(tmp_path):
    return tmp_path / "test_cache"

@pytest.fixture
def adaptor(temp_cache_dir):
    """Fixture to create an AKShareAdaptor with a temporary cache directory."""
    return AKShareAdaptor(cache_dir=str(temp_cache_dir))

@pytest.mark.asyncio
async def test_cache_miss_and_creation(adaptor: AKShareAdaptor, temp_cache_dir: Path):
    """
    Test case for a cache miss: ensures data is fetched and a cache file is created.
    """
    method = "test_method"
    params = {"symbol": "000001"}
    mock_data = pd.DataFrame({"price": [10, 11, 12]})
    
    # Mock the actual akshare function
    mock_ak_func = MagicMock(return_value=mock_data)
    
    with patch(f"akshare.{method}", mock_ak_func, create=True):
        # First call - should be a cache miss
        result = await adaptor.call(method, **params)
        
        # Assertions
        mock_ak_func.assert_called_once_with(**params)
        pd.testing.assert_frame_equal(result, mock_data)
        
        # Check if cache file was created
        cache_key = adaptor._get_cache_key(method, params)
        cache_file = temp_cache_dir / f"{cache_key}.parquet"
        assert cache_file.exists()

@pytest.mark.asyncio
async def test_cache_hit(adaptor: AKShareAdaptor, temp_cache_dir: Path):
    """
    Test case for a cache hit: ensures data is read from cache and the real function is not called again.
    """
    method = "test_method_hit"
    params = {"symbol": "000002"}
    mock_data = pd.DataFrame({"value": [100, 200]})
    
    mock_ak_func = MagicMock(return_value=mock_data)
    
    with patch(f"akshare.{method}", mock_ak_func, create=True):
        # First call to populate cache
        await adaptor.call(method, **params)
        
        # Second call - should be a cache hit
        mock_ak_func.reset_mock() # Reset the mock to check if it's called again
        result = await adaptor.call(method, **params)
        
        # Assertions
        mock_ak_func.assert_not_called() # The real function should NOT be called
        pd.testing.assert_frame_equal(result, mock_data)

@pytest.mark.asyncio
@patch('adaptors.akshare.datetime')
async def test_cache_ttl_historical(mock_datetime, adaptor: AKShareAdaptor):
    """
    Test that historical data (end_date in the past) gets a 30-day TTL.
    """
    # Mock datetime.now() to control the flow of time
    mock_datetime.now.return_value = datetime(2023, 1, 31)
    # Ensure other datetime methods (like strptime) remain real
    mock_datetime.strptime = datetime.strptime
    
    params_historical = {"end_date": "20230115"} # Date is in the past
    ttl = adaptor._get_cache_ttl(params_historical)
    assert ttl == timedelta(days=30)

@pytest.mark.asyncio
@patch('adaptors.akshare.datetime')
async def test_cache_ttl_recent(mock_datetime, adaptor: AKShareAdaptor):
    """
    Test that recent data (no end_date or recent end_date) gets a 1-day TTL.
    """
    mock_datetime.now.return_value = datetime(2023, 1, 31)
    # Ensure other datetime methods (like strptime) remain real
    mock_datetime.strptime = datetime.strptime
    
    # Case 1: No date specified
    params_no_date = {"symbol": "any"}
    ttl_no_date = adaptor._get_cache_ttl(params_no_date)
    assert ttl_no_date == timedelta(days=1)
    
    # Case 2: End date is today
    params_today = {"end_date": "20230131"}
    ttl_today = adaptor._get_cache_ttl(params_today)
    assert ttl_today == timedelta(days=1)

@pytest.mark.asyncio
async def test_cache_expiration(adaptor: AKShareAdaptor, temp_cache_dir: Path):
    """
    Test that an expired cache is ignored and fresh data is fetched.
    """
    method = "test_method_expired"
    params = {"symbol": "000003"}
    mock_data_old = pd.DataFrame({'data': ['old']})
    mock_data_new = pd.DataFrame({'data': ['new']})

    # 1. Populate cache
    with patch(f"akshare.{method}", MagicMock(return_value=mock_data_old), create=True):
        await adaptor.call(method, **params)

    # 2. Manually "age" the cache file by setting its modification time to be in the past
    cache_key = adaptor._get_cache_key(method, params)
    cache_file = temp_cache_dir / f"{cache_key}.parquet"
    expired_time = (datetime.now() - timedelta(days=2)).timestamp()
    import os
    os.utime(cache_file, (expired_time, expired_time))

    # 3. Call again with a new mock return value
    mock_ak_func_new = MagicMock(return_value=mock_data_new)
    with patch(f"akshare.{method}", mock_ak_func_new, create=True):
        result = await adaptor.call(method, **params)

        # Assertions
        mock_ak_func_new.assert_called_once() # Should fetch fresh data
        pd.testing.assert_frame_equal(result, mock_data_new)

@pytest.mark.asyncio
async def test_non_dataframe_return_is_not_cached(adaptor: AKShareAdaptor, temp_cache_dir: Path):
    """
    Test that non-DataFrame results are returned correctly but not cached.
    """
    method = "test_non_df"
    params = {"param": "value"}
    mock_return = {"a": 1, "b": 2} # A dictionary, not a DataFrame
    
    mock_ak_func = MagicMock(return_value=mock_return)
    
    with patch(f"akshare.{method}", mock_ak_func, create=True):
        result = await adaptor.call(method, **params)
        
        # Assertions
        assert result == mock_return
        
        # Check that NO cache file was created
        cache_key = adaptor._get_cache_key(method, params)
        cache_file = temp_cache_dir / f"{cache_key}.parquet"
        assert not cache_file.exists()
