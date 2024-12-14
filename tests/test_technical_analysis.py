import pytest
import pandas as pd
import numpy as np
from src.technical_analysis import TechnicalAnalyzer
from config.config import TECHNICAL_SETTINGS

@pytest.fixture
def sample_data():
    """Create sample stock data for testing"""
    # Using 50 days of data to ensure enough history for MACD calculation
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    # Generate sample prices with an upward trend and some volatility
    base_price = 100
    price_changes = np.random.normal(0.2, 0.5, 50).cumsum()  # Cumulative random walk with upward bias
    prices = base_price + price_changes
    volumes = np.random.randint(1000, 2000, 50)  # Random volume between 1000 and 2000

    data = {
        '4. close': prices,
        '5. volume': volumes
    }
    df = pd.DataFrame(data, index=dates)
    return df

def test_macd_calculation(sample_data):
    """Test MACD indicator calculation"""
    analyzer = TechnicalAnalyzer(sample_data.copy())
    result = analyzer.calculate_macd()

    # Check if MACD columns are created
    assert 'macd' in result.columns
    assert 'macd_signal' in result.columns
    assert 'macd_diff' in result.columns

    # Check if we have some valid values (not all NaN)
    # We expect some initial NaN values due to the nature of MACD calculation
    assert not result['macd'].tail(10).isna().all(), "MACD should have valid values in recent data"
    assert not result['macd_signal'].tail(10).isna().all(), "MACD signal should have valid values in recent data"
    assert not result['macd_diff'].tail(10).isna().all(), "MACD difference should have valid values in recent data"

    # Verify MACD calculation logic
    # MACD = 12-day EMA - 26-day EMA
    last_values = result.tail(1).iloc[0]
    assert isinstance(last_values['macd'], float), "MACD should be a float"
    assert isinstance(last_values['macd_signal'], float), "MACD signal should be a float"
    assert isinstance(last_values['macd_diff'], float), "MACD difference should be a float"

def test_ema_calculation(sample_data):
    """Test EMA calculation"""
    analyzer = TechnicalAnalyzer(sample_data.copy())
    result = analyzer.calculate_ema()

    # Check if EMA columns are created
    assert 'ema_short' in result.columns
    assert 'ema_long' in result.columns

    # Check if values are calculated (not NaN)
    assert not result['ema_short'].isna().all()
    assert not result['ema_long'].isna().all()

    # Verify EMA calculation logic
    assert result['ema_short'].iloc[-1] > result['ema_long'].iloc[-1], \
        "With rising prices, short EMA should be above long EMA"

def test_score_calculation(sample_data):
    """Test technical score calculation"""
    analyzer = TechnicalAnalyzer(sample_data.copy())
    analyzer.calculate_macd()
    analyzer.calculate_ema()
    score = analyzer.calculate_score()

    # Score should be between 0 and 100
    assert 0 <= score <= 100

    # With our sample rising data, score should be relatively high
    assert score >= 50, "Score should be high for rising price trend"

def test_full_analysis(sample_data):
    """Test complete technical analysis"""
    analyzer = TechnicalAnalyzer(sample_data.copy())
    result = analyzer.analyze()

    # Check if all expected keys are present
    expected_keys = {'score', 'macd', 'macd_signal', 'ema_short', 'ema_long'}
    assert all(key in result for key in expected_keys)

    # Check if values are numeric
    assert all(isinstance(value, (int, float)) for value in result.values())