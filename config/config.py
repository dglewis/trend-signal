from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Database
DATABASE_URL = f"sqlite:///{BASE_DIR}/data/trendsignal.db"

# API Configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Technical Analysis Settings
TECHNICAL_SETTINGS = {
    'ema_short': 12,
    'ema_long': 26,
    'macd_signal': 9,
    'rsi_period': 14,  # Standard RSI period
    'score_threshold': 70  # Minimum score to trigger alert
}

# Alert Settings
ALERT_SETTINGS = {
    'check_interval': 300,  # 5 minutes in seconds
    'score_threshold': 70,
}