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

@patch('src.data_fetcher.CryptoCurrencies')
def test_crypto_daily_data_fetch(mock_crypto):
    """Test fetching daily data for a major cryptocurrency"""
    # Create sample data with descending dates (newest first)
    dates = pd.date_range(end='2023-12-31', periods=100, freq='D')[::-1]
    sample_data = pd.DataFrame({
        '4a. close (USD)': np.random.uniform(30000, 40000, 100),
        '5. volume': np.random.uniform(1000000, 2000000, 100)
    }, index=dates)

    # Setup mock
    mock_instance = MagicMock()
    mock_instance.get_digital_currency_daily.return_value = (sample_data, None)
    mock_crypto.return_value = mock_instance

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

@patch('src.data_fetcher.TimeSeries')
def test_crypto_intraday_data_fetch(mock_ts):
    """Test fetching intraday data for a major cryptocurrency"""
    # Create sample data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='5min')
    sample_data = pd.DataFrame({
        '1. open': np.random.uniform(30000, 40000, 100),
        '2. high': np.random.uniform(30000, 40000, 100),
        '3. low': np.random.uniform(30000, 40000, 100),
        '4. close': np.random.uniform(30000, 40000, 100),
        '5. volume': np.random.uniform(1000000, 2000000, 100)
    }, index=dates)

    # Setup mock
    mock_instance = MagicMock()
    mock_instance.get_intraday.return_value = (sample_data, None)
    mock_ts.return_value = mock_instance

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

@patch('src.data_fetcher.CryptoCurrencies')
def test_invalid_crypto_symbol(mock_crypto):
    """Test handling of invalid cryptocurrency symbols"""
    # Setup mock to raise ValueError for invalid symbol
    mock_instance = MagicMock()
    mock_instance.get_digital_currency_daily.side_effect = ValueError("Invalid API call")
    mock_crypto.return_value = mock_instance

    # Test
    fetcher = DataFetcher()
    with pytest.raises(InvalidSymbolError):
        fetcher.get_daily_data('INVALID_CRYPTO', market_type='crypto')

@patch('src.data_fetcher.CryptoCurrencies')
def test_api_rate_limit_handling(mock_crypto):
    """Test handling of API rate limit errors"""
    # Setup mock to raise ValueError for rate limit
    mock_instance = MagicMock()
    mock_instance.get_digital_currency_daily.side_effect = ValueError("API rate limit reached")
    mock_crypto.return_value = mock_instance

    # Test
    fetcher = DataFetcher()
    with pytest.raises(APIError) as exc_info:
        fetcher.get_daily_data('BTC', market_type='crypto')
    assert "API rate limit" in str(exc_info.value)

@patch('src.data_fetcher.CryptoCurrencies')
def test_crypto_data_structure(mock_crypto):
    """Test the structure and format of cryptocurrency data"""
    # Create sample data with specific structure
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    sample_data = pd.DataFrame({
        '4a. close (USD)': np.random.uniform(30000, 40000, 100),
        '5. volume': np.random.uniform(1000000, 2000000, 100)
    }, index=dates)

    # Sort index in descending order to match API behavior
    sample_data = sample_data.sort_index(ascending=False)

    # Setup mock
    mock_instance = MagicMock()
    mock_instance.get_digital_currency_daily.return_value = (sample_data, None)
    mock_crypto.return_value = mock_instance

    # Test
    fetcher = DataFetcher()
    data = fetcher.get_daily_data('ETH', market_type='crypto')

    # Verify structure
    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert data.index.is_monotonic_decreasing  # Most recent data first

    # Verify columns and data types
    required_columns = ['4. close', '5. volume']
    for col in required_columns:
        assert col in data.columns
        assert not data[col].isna().all()

    # Verify value ranges
    assert (data['4. close'] >= 0).all()
    assert (data['5. volume'] >= 0).all()