import pytest
import pandas as pd
from unittest.mock import Mock, patch, call, MagicMock
from src.data_fetcher import DataFetcher, APIError, DataFetcherError, InvalidSymbolError
from datetime import datetime, timedelta
import numpy as np
import json
import requests

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

@pytest.fixture
def mock_requests():
    with patch('src.data_fetcher.requests') as mock_req:
        # Create a mock response that mimics Alpha Vantage crypto response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Meta Data": {
                "1. Information": "Daily Prices and Volumes for Digital Currency",
                "2. Digital Currency Code": "BTC",
                "3. Digital Currency Name": "Bitcoin",
                "4. Market Code": "USD",
                "5. Market Name": "United States Dollar",
                "6. Last Refreshed": "2023-12-01 00:00:00",
                "7. Time Zone": "UTC"
            },
            "Time Series (Digital Currency Daily)": {
                "2023-12-01": {
                    "1a. open (USD)": "50000.00000",
                    "1b. open (USD)": "50000.00000",
                    "2a. high (USD)": "50100.00000",
                    "2b. high (USD)": "50100.00000",
                    "3a. low (USD)": "49900.00000",
                    "3b. low (USD)": "49900.00000",
                    "4a. close (USD)": "50050.00000",
                    "4b. close (USD)": "50050.00000",
                    "5. volume": "100.00000",
                    "6. market cap (USD)": "5005000.00000"
                },
                "2023-11-30": {
                    "1a. open (USD)": "49900.00000",
                    "1b. open (USD)": "49900.00000",
                    "2a. high (USD)": "50000.00000",
                    "2b. high (USD)": "50000.00000",
                    "3a. low (USD)": "49800.00000",
                    "3b. low (USD)": "49800.00000",
                    "4a. close (USD)": "50000.00000",
                    "4b. close (USD)": "50000.00000",
                    "5. volume": "90.00000",
                    "6. market cap (USD)": "4500000.00000"
                }
            }
        }
        mock_req.get.return_value = mock_response
        yield mock_req

@pytest.fixture
def mock_database():
    with patch('src.data_fetcher.DatabaseManager') as mock_db:
        mock_instance = Mock()
        mock_instance.get_cached_data.return_value = None
        mock_instance.save_analysis.return_value = None
        mock_db.return_value = mock_instance
        yield mock_instance

def test_data_fetcher_initialization(mock_alpha_vantage_api_key):
    """Test that DataFetcher initializes correctly with API key"""
    fetcher = DataFetcher()
    assert fetcher is not None

def test_data_fetcher_initialization_no_api_key():
    """Test that DataFetcher raises error when no API key is provided"""
    with patch('src.data_fetcher.ALPHA_VANTAGE_API_KEY', None):
        with pytest.raises(ValueError, match="Alpha Vantage API key not found"):
            DataFetcher()

def test_get_crypto_data(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test fetching cryptocurrency data"""
    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('BTC', market_type='crypto')

    # Verify the API was called correctly
    mock_requests.get.assert_called_once_with(
        'https://www.alphavantage.co/query',
        params={
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': 'BTC',
            'market': 'USD',
            'apikey': 'dummy_key'
        }
    )

    # Verify data was transformed correctly
    assert isinstance(data, pd.DataFrame)
    assert all(col in data.columns for col in ['1. open', '2. high', '3. low', '4. close', '5. volume'])
    assert len(data) == 2
    assert isinstance(data.index, pd.DatetimeIndex)

def test_get_crypto_data_with_cache(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test that cached crypto data is returned when available"""
    # Setup mock cached data
    cached_data = {
        '1. open': {'2023-12-01': 50000.0},
        '2. high': {'2023-12-01': 50100.0},
        '3. low': {'2023-12-01': 49900.0},
        '4. close': {'2023-12-01': 50050.0},
        '5. volume': {'2023-12-01': 100.0}
    }
    mock_database.get_cached_data.return_value = cached_data

    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('BTC', market_type='crypto', force_refresh=False)

    # Verify cache was used
    mock_database.get_cached_data.assert_called_once_with('BTC', max_age_minutes=5)
    mock_requests.get.assert_not_called()
    assert isinstance(data, pd.DataFrame)
    assert not data.empty

def test_get_crypto_data_force_refresh(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test that force_refresh bypasses cache for crypto data"""
    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('BTC', market_type='crypto', force_refresh=True)

    # Verify cache was not used
    mock_database.get_cached_data.assert_not_called()
    mock_requests.get.assert_called_once()
    assert isinstance(data, pd.DataFrame)
    assert not data.empty

def test_get_crypto_data_invalid_symbol(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test error handling for invalid crypto symbol"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Error Message": "Invalid API call"}
    mock_requests.get.return_value = mock_response

    fetcher = DataFetcher()
    with pytest.raises(InvalidSymbolError, match="Invalid symbol: INVALID"):
        fetcher.get_intraday_data('INVALID', market_type='crypto')

    # Verify the API was called correctly
    mock_requests.get.assert_called_once_with(
        'https://www.alphavantage.co/query',
        params={
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': 'INVALID',
            'market': 'USD',
            'apikey': 'dummy_key'
        }
    )

def test_get_crypto_data_rate_limit(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test rate limit handling for crypto data"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Note": "API call frequency exceeded"}
    mock_requests.get.return_value = mock_response

    # Setup mock cached data for fallback
    cached_data = {
        '1. open': {'2023-12-01': 50000.0},
        '2. high': {'2023-12-01': 50100.0},
        '3. low': {'2023-12-01': 49900.0},
        '4. close': {'2023-12-01': 50050.0},
        '5. volume': {'2023-12-01': 100.0}
    }
    mock_database.get_cached_data.side_effect = [None, cached_data]  # First call returns None, second call returns data

    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('BTC', market_type='crypto')

    # Verify fallback behavior
    assert mock_database.get_cached_data.call_count == 2
    assert isinstance(data, pd.DataFrame)
    assert not data.empty

def test_get_crypto_data_api_error(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test handling of API errors"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_requests.get.return_value = mock_response

    fetcher = DataFetcher()
    with pytest.raises(APIError, match="API request failed with status code 500"):
        fetcher.get_intraday_data('BTC', market_type='crypto')

def test_get_crypto_data_malformed_response(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test handling of malformed API response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"unexpected": "format"}
    mock_requests.get.return_value = mock_response

    fetcher = DataFetcher()
    with pytest.raises(DataFetcherError, match="Unexpected API response format for BTC"):
        fetcher.get_intraday_data('BTC', market_type='crypto')

def test_cache_hit(mock_alpha_vantage_api_key, mock_time_series, mock_database):
    """Test that cached data is returned when available"""
    # Setup mock cached data
    cached_data = {
        '1. open': {'2023-12-01 10:00:00': 100.0},
        '2. high': {'2023-12-01 10:00:00': 102.0},
        '3. low': {'2023-12-01 10:00:00': 98.0},
        '4. close': {'2023-12-01 10:00:00': 101.0},
        '5. volume': {'2023-12-01 10:00:00': 1000}
    }
    mock_database.get_cached_data.return_value = cached_data

    # Test
    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('AAPL', force_refresh=False)

    # Verify cache was used
    mock_database.get_cached_data.assert_called_once_with('AAPL', max_age_minutes=5)
    mock_time_series.return_value.get_intraday.assert_not_called()
    assert isinstance(data, pd.DataFrame)
    assert not data.empty

def test_force_refresh_bypass_cache(mock_alpha_vantage_api_key, mock_time_series, mock_database):
    """Test that force_refresh bypasses cache"""
    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('AAPL', force_refresh=True)

    # Verify cache was not used
    mock_database.get_cached_data.assert_not_called()
    mock_time_series.return_value.get_intraday.assert_called_once()
    assert isinstance(data, pd.DataFrame)
    assert not data.empty

def test_rate_limit_fallback_to_cache(mock_alpha_vantage_api_key, mock_time_series, mock_database):
    """Test fallback to cache when rate limit is hit"""
    # Setup mock to raise rate limit error
    mock_time_series.return_value.get_intraday.side_effect = ValueError("API rate limit reached")

    # Setup mock cached data
    cached_data = {
        '1. open': {'2023-12-01 10:00:00': 100.0},
        '2. high': {'2023-12-01 10:00:00': 102.0},
        '3. low': {'2023-12-01 10:00:00': 98.0},
        '4. close': {'2023-12-01 10:00:00': 101.0},
        '5. volume': {'2023-12-01 10:00:00': 1000}
    }
    mock_database.get_cached_data.side_effect = [None, cached_data]  # First call returns None, second call returns data

    # Test
    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('AAPL')

    # Verify fallback behavior
    assert mock_database.get_cached_data.call_count == 2
    assert mock_database.get_cached_data.call_args_list[0] == call('AAPL', max_age_minutes=5)
    assert mock_database.get_cached_data.call_args_list[1] == call('AAPL', max_age_minutes=15)
    assert isinstance(data, pd.DataFrame)
    assert not data.empty

def test_rate_limit_no_cache_available(mock_alpha_vantage_api_key, mock_time_series, mock_database):
    """Test rate limit error when no cache is available"""
    # Setup mock to raise rate limit error
    mock_time_series.return_value.get_intraday.side_effect = ValueError("API rate limit reached")
    mock_database.get_cached_data.return_value = None

    # Test
    fetcher = DataFetcher()
    with pytest.raises(APIError, match="API rate limit reached"):
        fetcher.get_intraday_data('AAPL')

def test_get_intraday_data(mock_alpha_vantage_api_key, mock_time_series, mock_database):
    """Test fetching intraday data"""
    fetcher = DataFetcher()
    data = fetcher.get_intraday_data('AAPL')

    assert isinstance(data, pd.DataFrame)
    assert len(data) == 2
    assert all(col in data.columns for col in ['1. open', '2. high', '3. low', '4. close', '5. volume'])
    assert isinstance(data.index, pd.DatetimeIndex)

def test_get_intraday_data_error_handling(mock_alpha_vantage_api_key, mock_time_series, mock_database):
    """Test error handling when fetching intraday data fails"""
    # Setup mock to raise API error
    mock_time_series.return_value.get_intraday.side_effect = Exception("API Error")

    fetcher = DataFetcher()
    with pytest.raises(DataFetcherError, match="Error fetching data for AAPL: API Error"):
        fetcher.get_intraday_data('AAPL')

def test_get_daily_crypto_data(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test fetching daily cryptocurrency data"""
    fetcher = DataFetcher()
    data = fetcher.get_daily_data('BTC', market_type='crypto')

    # Verify the API was called correctly
    mock_requests.get.assert_called_once_with(
        'https://www.alphavantage.co/query',
        params={
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': 'BTC',
            'market': 'USD',
            'apikey': 'dummy_key'
        }
    )

    # Verify data was transformed correctly
    assert isinstance(data, pd.DataFrame)
    assert all(col in data.columns for col in ['1. open', '2. high', '3. low', '4. close', '5. volume'])
    assert len(data) == 2
    assert isinstance(data.index, pd.DatetimeIndex)

def test_get_daily_crypto_data_invalid_symbol(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test error handling for invalid crypto symbol in daily data"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Error Message": "Invalid API call"}
    mock_requests.get.return_value = mock_response

    fetcher = DataFetcher()
    with pytest.raises(InvalidSymbolError, match="Invalid symbol: INVALID"):
        fetcher.get_daily_data('INVALID', market_type='crypto')

    # Verify the API was called correctly
    mock_requests.get.assert_called_once_with(
        'https://www.alphavantage.co/query',
        params={
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': 'INVALID',
            'market': 'USD',
            'apikey': 'dummy_key'
        }
    )

def test_get_daily_crypto_data_rate_limit(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test rate limit handling for daily crypto data"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Note": "API call frequency exceeded"}
    mock_requests.get.return_value = mock_response

    fetcher = DataFetcher()
    with pytest.raises(APIError, match="API rate limit reached"):
        fetcher.get_daily_data('BTC', market_type='crypto')

def test_get_daily_crypto_data_api_error(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test handling of API errors in daily crypto data"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_requests.get.return_value = mock_response

    fetcher = DataFetcher()
    with pytest.raises(APIError, match="API request failed with status code 500"):
        fetcher.get_daily_data('BTC', market_type='crypto')

def test_get_daily_crypto_data_malformed_response(mock_alpha_vantage_api_key, mock_requests, mock_database):
    """Test handling of malformed API response in daily crypto data"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"unexpected": "format"}
    mock_requests.get.return_value = mock_response

    fetcher = DataFetcher()
    with pytest.raises(DataFetcherError, match="Unexpected API response format for BTC"):
        fetcher.get_daily_data('BTC', market_type='crypto')

def test_get_top_gainers_losers():
    with patch('src.data_fetcher.requests.get') as mock_get:
        # Mock response data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "top_gainers": [
                {
                    "ticker": "AAPL",
                    "price": "150.0",
                    "change_amount": "10.0",
                    "change_percentage": "7.14"
                }
            ],
            "top_losers": [
                {
                    "ticker": "MSFT",
                    "price": "300.0",
                    "change_amount": "-20.0",
                    "change_percentage": "-6.25"
                }
            ]
        }
        mock_get.return_value = mock_response

        data_fetcher = DataFetcher()
        gainers, losers = data_fetcher.get_top_gainers_losers()

        # Verify the structure and content of the returned data
        assert isinstance(gainers, list)
        assert isinstance(losers, list)
        assert len(gainers) > 0
        assert len(losers) > 0

        # Verify the first gainer's data structure
        first_gainer = gainers[0]
        assert "ticker" in first_gainer
        assert "price" in first_gainer
        assert "change_amount" in first_gainer
        assert "change_percentage" in first_gainer

        # Verify the first loser's data structure
        first_loser = losers[0]
        assert "ticker" in first_loser
        assert "price" in first_loser
        assert "change_amount" in first_loser
        assert "change_percentage" in first_loser

def test_get_top_gainers_losers_api_error():
    with patch('src.data_fetcher.requests.get') as mock_get:
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 429  # Too Many Requests
        mock_get.return_value = mock_response

        data_fetcher = DataFetcher()
        with pytest.raises(APIError):
            data_fetcher.get_top_gainers_losers()

def test_get_top_gainers_losers_empty_response():
    with patch('src.data_fetcher.requests.get') as mock_get:
        # Mock empty response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "top_gainers": [],
            "top_losers": []
        }
        mock_get.return_value = mock_response

        data_fetcher = DataFetcher()
        gainers, losers = data_fetcher.get_top_gainers_losers()

        assert isinstance(gainers, list)
        assert isinstance(losers, list)
        assert len(gainers) == 0
        assert len(losers) == 0
