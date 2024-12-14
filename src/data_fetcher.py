from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.cryptocurrencies import CryptoCurrencies
import pandas as pd
import os
import sys
from typing import Optional, Tuple

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
        self.crypto = CryptoCurrencies(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

    def get_intraday_data(self, symbol: str, interval: str = '5min', market_type: str = 'stock') -> pd.DataFrame:
        """
        Fetch intraday data for a given symbol
        :param symbol: Stock/Crypto symbol (e.g., 'AAPL' or 'BTC')
        :param interval: Time interval between data points
        :param market_type: Type of market data to fetch ('stock' or 'crypto')
        :return: DataFrame with market data
        :raises:
            InvalidSymbolError: If the symbol is invalid
            APIError: If there's an API-related error
            DataFetcherError: For other errors
        """
        try:
            # Validate symbol format
            if not isinstance(symbol, str) or not symbol.strip():
                raise InvalidSymbolError(f"Invalid symbol format: {symbol}")

            if market_type == 'crypto':
                # For crypto, we use the regular time series with the crypto symbol
                symbol = f"{symbol.upper()}USD"
                data, _ = self.ts.get_intraday(symbol=symbol, interval=interval, outputsize='compact')

                # If the data is empty, try the daily data as fallback
                if data is None or data.empty:
                    logger.warning(f"No intraday data available for {symbol}, falling back to daily data")
                    return self.get_daily_data(symbol, market_type='crypto')
            else:
                data, _ = self.ts.get_intraday(symbol=symbol, interval=interval, outputsize='compact')

            # Validate response data
            if data is None or data.empty:
                raise DataFetcherError(f"No data returned for symbol: {symbol}")

            data.index = pd.to_datetime(data.index)
            return data

        except ValueError as e:
            if "Invalid API call" in str(e):
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")
            elif "API rate limit" in str(e):
                raise APIError("API rate limit reached. Please try again later.")
            raise APIError(f"API error: {str(e)}")

        except ConnectionError as e:
            raise APIError(f"Network error while fetching data: {str(e)}")

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise DataFetcherError(f"Error fetching data for {symbol}: {str(e)}")

    def get_daily_data(self, symbol: str, market_type: str = 'stock') -> pd.DataFrame:
        """
        Fetch daily data for a given symbol
        :param symbol: Stock/Crypto symbol (e.g., 'AAPL' or 'BTC')
        :param market_type: Type of market data to fetch ('stock' or 'crypto')
        :return: DataFrame with market data
        :raises:
            InvalidSymbolError: If the symbol is invalid
            APIError: If there's an API-related error
            DataFetcherError: For other errors
        """
        try:
            # Validate symbol format
            if not isinstance(symbol, str) or not symbol.strip():
                raise InvalidSymbolError(f"Invalid symbol format: {symbol}")

            if market_type == 'crypto':
                # For crypto, we need to append the market (e.g., USD)
                symbol = f"{symbol.upper()}"
                data, _ = self.crypto.get_digital_currency_daily(symbol=symbol, market='USD')
                # Rename columns to match stock data format
                data = data.rename(columns={
                    '4a. close (USD)': '4. close',
                    '5. volume': '5. volume'
                })
            else:
                data, _ = self.ts.get_daily(symbol=symbol, outputsize='compact')

            # Validate response data
            if data is None or data.empty:
                raise DataFetcherError(f"No data returned for symbol: {symbol}")

            data.index = pd.to_datetime(data.index)
            return data

        except ValueError as e:
            if "Invalid API call" in str(e):
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")
            elif "API rate limit" in str(e):
                raise APIError("API rate limit reached. Please try again later.")
            raise APIError(f"API error: {str(e)}")

        except ConnectionError as e:
            raise APIError(f"Network error while fetching data: {str(e)}")

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise DataFetcherError(f"Error fetching data for {symbol}: {str(e)}")

    def get_crypto_list(self) -> list:
        """
        Get a list of supported cryptocurrencies
        :return: List of cryptocurrency symbols
        """
        # Common cryptocurrencies - this could be expanded or fetched from an API
        return ['BTC', 'ETH', 'USDT', 'BNB', 'XRP', 'ADA', 'DOGE', 'SOL', 'DOT', 'MATIC']