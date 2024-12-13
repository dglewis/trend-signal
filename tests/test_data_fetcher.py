import pytest
import pandas as pd
from unittest.mock import Mock, patch
from src.data_fetcher import DataFetcher
from datetime import datetime

@pytest.fixture
def mock_alpha_vantage_api_key():
    with patch('src.data_fetcher.ALPHA_VANTAGE_API_KEY', 'dummy_key'):
        yield 'dummy_key'

@pytest.fixture
def mock_time_series():
    with patch('src.data_fetcher.TimeSeries') as mock_ts:
        # Create a mock DataFrame that mimics Alpha Vantage response
        mock_data = pd.DataFrame(
            {
                '1. open': [100.0, 101.0],
                '2. high': [102.0, 103.0],
                '3. low': [98.0, 99.0],
                '4. close': [101.0, 102.0],
                '5. volume': [1000, 1100]
            },
            index=[datetime(2023, 12, 1, 10, 0), datetime(2023, 12, 1, 10, 5)]
        )
        mock_ts.return_value.get_intraday.return_value = (mock_data, None)
        mock_ts.return_value.get_daily.return_value = (mock_data, None)
        yield mock_ts

def test_data_fetcher_initialization(mock_alpha_vantage_api_key):
    """Test that DataFetcher initializes correctly with API key"""
    fetcher = DataFetcher()
    assert fetcher is not None

def test_data_fetcher_initialization_no_api_key():
    """Test that DataFetcher raises error when no API key is provided"""
    with patch('src.data_fetcher.ALPHA_VANTAGE_API_KEY', None):
        with pytest.raises(ValueError, match="Alpha Vantage API key not found"):
            DataFetcher()

def test_get_intraday_data(mock_time_series, mock_alpha_vantage_api_key):
    """Test fetching intraday data"""
    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('AAPL')

    assert isinstance(data, pd.DataFrame)
    assert len(data) == 2
    assert all(col in data.columns for col in ['1. open', '2. high', '3. low', '4. close', '5. volume'])
    assert isinstance(data.index, pd.DatetimeIndex)

def test_get_daily_data(mock_time_series, mock_alpha_vantage_api_key):
    """Test fetching daily data"""
    fetcher = DataFetcher()
    data = fetcher.get_daily_data('AAPL')

    assert isinstance(data, pd.DataFrame)
    assert len(data) == 2
    assert all(col in data.columns for col in ['1. open', '2. high', '3. low', '4. close', '5. volume'])
    assert isinstance(data.index, pd.DatetimeIndex)

def test_get_intraday_data_error_handling(mock_time_series, mock_alpha_vantage_api_key):
    """Test error handling when fetching intraday data fails"""
    mock_time_series.return_value.get_intraday.side_effect = Exception("API Error")

    fetcher = DataFetcher()
    with pytest.raises(Exception, match="API Error"):
        fetcher.get_intraday_data('AAPL')