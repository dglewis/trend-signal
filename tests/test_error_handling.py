import pytest
from unittest.mock import patch, Mock
from src.data_fetcher import DataFetcher, InvalidSymbolError, APIError, DataFetcherError
from alpha_vantage.timeseries import TimeSeries

def test_invalid_symbol():
    """Test that invalid stock symbols raise an appropriate error"""
    with patch('src.data_fetcher.ALPHA_VANTAGE_API_KEY', 'dummy_key'):
        with patch('src.data_fetcher.TimeSeries') as mock_ts:
            # Mock the Alpha Vantage API to raise an error for invalid symbol
            mock_ts.return_value.get_intraday.side_effect = ValueError("Invalid API call")

            fetcher = DataFetcher()
            with pytest.raises(InvalidSymbolError) as exc_info:
                fetcher.get_intraday_data('INVALID1', force_refresh=True)

            assert "Invalid symbol: INVALID1" in str(exc_info.value)

def test_api_rate_limit():
    """Test handling of API rate limit errors"""
    with patch('src.data_fetcher.ALPHA_VANTAGE_API_KEY', 'dummy_key'):
        with patch('src.data_fetcher.TimeSeries') as mock_ts:
            # Mock the Alpha Vantage API to raise a rate limit error
            mock_ts.return_value.get_intraday.side_effect = ValueError("API rate limit reached")

            fetcher = DataFetcher()
            with pytest.raises(APIError) as exc_info:
                fetcher.get_intraday_data('AAPL', force_refresh=True)

            assert "API rate limit" in str(exc_info.value)

def test_network_error():
    """Test handling of network connectivity errors"""
    with patch('src.data_fetcher.ALPHA_VANTAGE_API_KEY', 'dummy_key'):
        with patch('src.data_fetcher.TimeSeries') as mock_ts:
            # Mock a network error
            mock_ts.return_value.get_intraday.side_effect = ConnectionError("Network error")

            fetcher = DataFetcher()
            with pytest.raises(APIError) as exc_info:
                fetcher.get_intraday_data('AAPL', force_refresh=True)

            assert "Network error" in str(exc_info.value)

def test_malformed_response():
    """Test handling of malformed API responses"""
    with patch('src.data_fetcher.ALPHA_VANTAGE_API_KEY', 'dummy_key'):
        with patch('src.data_fetcher.TimeSeries') as mock_ts:
            # Mock a malformed response
            mock_ts.return_value.get_intraday.return_value = (None, None)

            fetcher = DataFetcher()
            with pytest.raises(DataFetcherError) as exc_info:
                fetcher.get_intraday_data('AAPL', force_refresh=True)

            assert "No data returned for symbol" in str(exc_info.value)