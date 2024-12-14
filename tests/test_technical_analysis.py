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
    analyzer.calculate_rsi()
    score = analyzer.calculate_score()

    # Score should be between 0 and 100
    assert 0 <= score <= 100

    # With our sample rising data, score should be at least 40
    # (we expect at least MACD and EMA signals to be positive in a rising trend)
    assert score >= 40, "Score should be at least 40 for rising price trend"

    # Test individual components
    latest = analyzer.data.iloc[-1]
    component_scores = 0

    # MACD component (25 points)
    if latest['macd'] > latest['macd_signal']:
        component_scores += 25

    # EMA component (25 points)
    if latest['ema_short'] > latest['ema_long']:
        component_scores += 25

    # Volume component (20 points)
    vol_avg = analyzer.data['5. volume'].rolling(window=5).mean().iloc[-1]
    if latest['5. volume'] > vol_avg:
        component_scores += 20

    # Price vs EMA component (15 points)
    if latest['4. close'] > latest['ema_short']:
        component_scores += 15

    # RSI component (15 points)
    if 40 <= latest['rsi'] <= 60:
        component_scores += 15

    # Verify total score matches component calculation
    assert score == component_scores, "Total score should match sum of component scores"

def test_full_analysis(sample_data):
    """Test complete technical analysis"""
    analyzer = TechnicalAnalyzer(sample_data.copy())
    result = analyzer.analyze()

    # Check if all expected keys are present
    expected_keys = {'score', 'macd', 'macd_signal', 'ema_short', 'ema_long'}
    assert all(key in result for key in expected_keys)

    # Check if values are numeric
    assert all(isinstance(value, (int, float)) for value in result.values())

def test_rsi_calculation(sample_data):
    """Test RSI indicator calculation"""
    analyzer = TechnicalAnalyzer(sample_data.copy())
    result = analyzer.calculate_rsi()

    # Check if RSI column is created
    assert 'rsi' in result.columns

    # Check if values are calculated (not NaN)
    assert not result['rsi'].isna().all()

    # Verify RSI is within valid range (0-100)
    assert result['rsi'].min() >= 0
    assert result['rsi'].max() <= 100

    # With our sample rising data, RSI should indicate strong momentum
    last_rsi = result['rsi'].iloc[-1]
    assert isinstance(last_rsi, float), "RSI should be a float"
    assert last_rsi > 50, "RSI should be above 50 for rising price trends"