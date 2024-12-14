import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.data_fetcher import DataFetcher, InvalidSymbolError, APIError, DataFetcherError

def test_crypto_symbol_list():
    """Test that crypto list contains expected symbols"""
    fetcher = DataFetcher()
    crypto_list = fetcher.get_crypto_list()
    assert isinstance(crypto_list, list)
    assert len(crypto_list) > 0
    assert 'BTC' in crypto_list
    assert 'ETH' in crypto_list

@patch('src.data_fetcher.requests')
def test_crypto_daily_data_fetch(mock_requests):
    """Test fetching daily data for a major cryptocurrency"""
    # Create sample data with descending dates (newest first)
    dates = pd.date_range(end='2023-12-31', periods=100, freq='D')[::-1]
    sample_data = {
        "Time Series (Digital Currency Daily)": {
            date.strftime('%Y-%m-%d'): {
                "1a. open (USD)": "35000.00",
                "2a. high (USD)": "36000.00",
                "3a. low (USD)": "34000.00",
                "4a. close (USD)": "35500.00",
                "5. volume": "1000000.00"
            } for date in dates
        }
    }

    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_data
    mock_requests.get.return_value = mock_response

    # Test
    fetcher = DataFetcher()
    data = fetcher.get_daily_data('BTC', market_type='crypto')

    # Verify
    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert '4. close' in data.columns
    assert '5. volume' in data.columns
    assert pd.api.types.is_datetime64_any_dtype(data.index)
    assert pd.api.types.is_float_dtype(data['4. close'])
    assert data.index.is_monotonic_decreasing

@patch('src.data_fetcher.requests')
def test_crypto_intraday_data_fetch(mock_requests):
    """Test fetching intraday data for a major cryptocurrency"""
    # Create sample data with descending dates (newest first)
    dates = pd.date_range(end='2023-12-31', periods=100, freq='5min')[::-1]
    sample_data = {
        "Time Series (Digital Currency Daily)": {
            date.strftime('%Y-%m-%d'): {
                "1a. open (USD)": "35000.00",
                "2a. high (USD)": "36000.00",
                "3a. low (USD)": "34000.00",
                "4a. close (USD)": "35500.00",
                "5. volume": "1000000.00"
            } for date in dates
        }
    }

    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_data
    mock_requests.get.return_value = mock_response

    # Test
    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('BTC', interval='5min', market_type='crypto')

    # Verify
    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert '4. close' in data.columns
    assert '5. volume' in data.columns
    assert pd.api.types.is_datetime64_any_dtype(data.index)
    assert pd.api.types.is_float_dtype(data['4. close'])

@patch('src.data_fetcher.requests')
def test_invalid_crypto_symbol(mock_requests):
    """Test handling of invalid cryptocurrency symbols"""
    # Setup mock response for invalid symbol
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Error Message": "Invalid API call"}
    mock_requests.get.return_value = mock_response

    # Test
    fetcher = DataFetcher()
    with pytest.raises(InvalidSymbolError):
        fetcher.get_daily_data('INVALID_CRYPTO', market_type='crypto')

@patch('src.data_fetcher.requests')
def test_api_rate_limit_handling(mock_requests):
    """Test handling of API rate limit errors"""
    # Setup mock response for rate limit
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Note": "API call frequency exceeded"}
    mock_requests.get.return_value = mock_response

    # Test
    fetcher = DataFetcher()
    with pytest.raises(APIError) as exc_info:
        fetcher.get_daily_data('BTC', market_type='crypto')
    assert "API rate limit" in str(exc_info.value)

@patch('src.data_fetcher.requests')
def test_crypto_data_structure(mock_requests):
    """Test the structure and format of cryptocurrency data"""
    # Create sample data with specific structure
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    sample_data = {
        "Time Series (Digital Currency Daily)": {
            date.strftime('%Y-%m-%d'): {
                "1a. open (USD)": "35000.00",
                "2a. high (USD)": "36000.00",
                "3a. low (USD)": "34000.00",
                "4a. close (USD)": "35500.00",
                "5. volume": "1000000.00"
            } for date in dates
        }
    }

    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_data
    mock_requests.get.return_value = mock_response

    # Test
    fetcher = DataFetcher()
    data = fetcher.get_daily_data('ETH', market_type='crypto')

    # Verify structure
    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert data.index.is_monotonic_decreasing  # Most recent data first

    # Verify columns and data types
    required_columns = ['1. open', '2. high', '3. low', '4. close', '5. volume']
    for col in required_columns:
        assert col in data.columns
        assert not data[col].isna().all()
        assert pd.api.types.is_float_dtype(data[col])

    # Verify value ranges
    assert (data['4. close'] >= 0).all()
    assert (data['5. volume'] >= 0).all()