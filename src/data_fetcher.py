from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import ALPHA_VANTAGE_API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        if not ALPHA_VANTAGE_API_KEY:
            raise ValueError("Alpha Vantage API key not found in environment variables")
        self.ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

    def get_intraday_data(self, symbol: str, interval: str = '5min') -> pd.DataFrame:
        """
        Fetch intraday data for a given symbol
        :param symbol: Stock symbol (e.g., 'AAPL')
        :param interval: Time interval between data points
        :return: DataFrame with stock data
        """
        try:
            data, _ = self.ts.get_intraday(symbol=symbol, interval=interval, outputsize='compact')
            data.index = pd.to_datetime(data.index)
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise

    def get_daily_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch daily data for a given symbol
        :param symbol: Stock symbol (e.g., 'AAPL')
        :return: DataFrame with stock data
        """
        try:
            data, _ = self.ts.get_daily(symbol=symbol, outputsize='compact')
            data.index = pd.to_datetime(data.index)
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise