from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import os
import sys
from typing import Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import ALPHA_VANTAGE_API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcherError(Exception):
    """Base exception class for DataFetcher errors"""
    pass

class InvalidSymbolError(DataFetcherError):
    """Raised when an invalid stock symbol is provided"""
    pass

class APIError(DataFetcherError):
    """Raised when there's an API-related error"""
    pass

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
        :raises:
            InvalidSymbolError: If the symbol is invalid
            APIError: If there's an API-related error
            DataFetcherError: For other errors
        """
        try:
            # Validate symbol format
            if not isinstance(symbol, str) or not symbol.isalnum():
                raise InvalidSymbolError(f"Invalid symbol format: {symbol}")

            data, _ = self.ts.get_intraday(symbol=symbol, interval=interval, outputsize='compact')

            # Validate response data
            if data is None or data.empty:
                raise DataFetcherError(f"No data returned for symbol: {symbol}")

            data.index = pd.to_datetime(data.index)
            return data

        except ValueError as e:
            if "Invalid API call" in str(e):
                raise InvalidSymbolError(f"Invalid stock symbol: {symbol}")
            elif "API rate limit" in str(e):
                raise APIError("API rate limit reached. Please try again later.")
            raise APIError(f"API error: {str(e)}")

        except ConnectionError as e:
            raise APIError(f"Network error while fetching data: {str(e)}")

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise DataFetcherError(f"Error fetching data for {symbol}: {str(e)}")

    def get_daily_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch daily data for a given symbol
        :param symbol: Stock symbol (e.g., 'AAPL')
        :return: DataFrame with stock data
        :raises:
            InvalidSymbolError: If the symbol is invalid
            APIError: If there's an API-related error
            DataFetcherError: For other errors
        """
        try:
            # Validate symbol format
            if not isinstance(symbol, str) or not symbol.isalnum():
                raise InvalidSymbolError(f"Invalid symbol format: {symbol}")

            data, _ = self.ts.get_daily(symbol=symbol, outputsize='compact')

            # Validate response data
            if data is None or data.empty:
                raise DataFetcherError(f"No data returned for symbol: {symbol}")

            data.index = pd.to_datetime(data.index)
            return data

        except ValueError as e:
            if "Invalid API call" in str(e):
                raise InvalidSymbolError(f"Invalid stock symbol: {symbol}")
            elif "API rate limit" in str(e):
                raise APIError("API rate limit reached. Please try again later.")
            raise APIError(f"API error: {str(e)}")

        except ConnectionError as e:
            raise APIError(f"Network error while fetching data: {str(e)}")

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise DataFetcherError(f"Error fetching data for {symbol}: {str(e)}")