import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime
import streamlit as st
from src.app import analyze_symbol, create_candlestick_chart, display_error
from src.data_fetcher import InvalidSymbolError, APIError, DataFetcherError

@pytest.fixture
def mock_data():
    """Create mock market data"""
    return pd.DataFrame({
        '1. open': [100.0],
        '2. high': [101.0],
        '3. low': [99.0],
        '4. close': [100.5],
        '5. volume': [1000]
    }, index=[datetime.now()])

@pytest.fixture
def mock_analysis_results():
    """Create mock analysis results"""
    return {
        'score': 75.0,
        'macd': 0.5,
        'ema_short': 100.0,
        'ema_long': 99.0
    }

@pytest.fixture
def mock_streamlit():
    """Mock streamlit functions"""
    with patch('streamlit.warning') as mock_warning, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.info') as mock_info:
        yield {
            'warning': mock_warning,
            'error': mock_error,
            'info': mock_info
        }

@pytest.fixture
def mock_fetcher():
    """Create a mock DataFetcher"""
    with patch('src.app.DataFetcher', autospec=True) as mock_fetcher_class:
        mock_instance = Mock()
        mock_fetcher_class.return_value = mock_instance
        yield mock_instance

def test_analyze_symbol_empty_symbol(mock_streamlit, mock_fetcher):
    """Test that analyze_symbol shows warning for empty symbol"""
    analyze_symbol('', '5min', 'stock')
    mock_streamlit['warning'].assert_called_once_with("Please enter a symbol")
    mock_fetcher.get_intraday_data.assert_not_called()

def test_analyze_symbol_invalid_symbol(mock_streamlit, mock_fetcher):
    """Test that analyze_symbol shows error for invalid symbol"""
    mock_fetcher.get_intraday_data.side_effect = InvalidSymbolError("Invalid symbol: INVALID")
    analyze_symbol('INVALID', '5min', 'stock')
    mock_streamlit['error'].assert_called_once_with("Invalid symbol: INVALID")

def test_analyze_symbol_api_error(mock_streamlit, mock_fetcher):
    """Test that analyze_symbol shows error for API errors"""
    mock_fetcher.get_intraday_data.side_effect = APIError("API rate limit reached. Please try again later.")
    analyze_symbol('AAPL', '5min', 'stock')
    mock_streamlit['error'].assert_called_once_with("API Error: API rate limit reached. Please try again later.")

def test_analyze_symbol_success(mock_data, mock_analysis_results, mock_fetcher):
    """Test successful analysis with valid data"""
    # Mock fetcher response
    mock_fetcher.get_intraday_data.return_value = mock_data

    # Mock analyzer
    with patch('src.app.TechnicalAnalyzer', autospec=True) as mock_analyzer_class:
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = mock_analysis_results
        mock_analyzer_class.return_value = mock_analyzer

        # Run analysis
        result = analyze_symbol('AAPL', '5min', 'stock')

        # Verify results
        assert result is not None
        data, analysis = result
        assert data is mock_data
        assert analysis is mock_analysis_results

        # Verify method calls
        mock_fetcher.get_intraday_data.assert_called_once_with(
            symbol='AAPL',
            interval='5min',
            market_type='stock',
            force_refresh=False
        )
        mock_analyzer_class.assert_called_once_with(mock_data)
        mock_analyzer.analyze.assert_called_once_with()

def test_analyze_symbol_empty_data(mock_streamlit, mock_fetcher):
    """Test handling of empty data response"""
    mock_fetcher.get_intraday_data.return_value = pd.DataFrame()  # Empty DataFrame
    analyze_symbol('AAPL', '5min', 'stock')
    mock_streamlit['error'].assert_called_once_with("No data available for AAPL")

def test_analyze_symbol_none_data(mock_streamlit, mock_fetcher):
    """Test handling of None data response"""
    mock_fetcher.get_intraday_data.return_value = None
    analyze_symbol('AAPL', '5min', 'stock')
    mock_streamlit['error'].assert_called_once_with("No data available for AAPL")

def test_create_candlestick_chart(mock_data):
    """Test candlestick chart creation"""
    chart = create_candlestick_chart(mock_data, "Test Chart")
    assert chart is not None
    assert chart.layout.title.text == "Test Chart"

def test_display_error():
    """Test error display with different levels"""
    with patch('streamlit.error') as mock_error, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.info') as mock_info:

        # Test error level
        display_error("Error message", "error")
        mock_error.assert_called_once_with("❌ Error message")

        # Test warning level
        display_error("Warning message", "warning")
        mock_warning.assert_called_once_with("⚠️ Warning message")

        # Test info level
        display_error("Info message", "info")
        mock_info.assert_called_once_with("ℹ️ Info message")