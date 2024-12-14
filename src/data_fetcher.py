import requests
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.cryptocurrencies import CryptoCurrencies
import pandas as pd
import os
import sys
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import ALPHA_VANTAGE_API_KEY
from src.database import DatabaseManager
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
        self.db = DatabaseManager()
        self.base_url = "https://www.alphavantage.co/query"

    def get_intraday_data(self, symbol: str, interval: str = '5min', market_type: str = 'stock', force_refresh: bool = False) -> pd.DataFrame:
        """
        Get intraday trading data for a symbol

        Args:
            symbol: The stock/crypto symbol
            interval: Time interval between data points
            market_type: Either 'stock' or 'crypto'
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            pd.DataFrame: DataFrame containing the trading data
        """
        logger.info(f"Fetching {market_type} data for {symbol}")

        # Check cache first unless force_refresh is True
        if not force_refresh:
            cached_data = self.db.get_cached_data(symbol, max_age_minutes=5)
            if cached_data is not None:
                logger.info(f"Using cached data for {symbol}")
                return pd.DataFrame.from_dict(cached_data)

        try:
            if market_type == 'crypto':
                # For crypto, we use the daily endpoint since intraday is premium-only
                params = {
                    'function': 'DIGITAL_CURRENCY_DAILY',
                    'symbol': symbol,
                    'market': 'USD',
                    'apikey': ALPHA_VANTAGE_API_KEY
                }
                response = requests.get(self.base_url, params=params)
                if response.status_code != 200:
                    raise APIError(f"API request failed with status code {response.status_code}")

                data = response.json()

                # Check for various error conditions in the response
                if 'Error Message' in data or ('Information' in data and 'Invalid API call' in data['Information']):
                    raise InvalidSymbolError(f"Invalid symbol: {symbol}")
                if 'Note' in data and 'API call frequency' in data['Note']:
                    # If we hit rate limit, try to use slightly older cached data
                    cached_data = self.db.get_cached_data(symbol, max_age_minutes=15)
                    if cached_data is not None:
                        logger.warning("Using older cached data due to rate limit")
                        return pd.DataFrame.from_dict(cached_data)
                    raise APIError("API rate limit reached. Please try again later.")

                # Convert the JSON response to a DataFrame
                time_series_key = "Time Series (Digital Currency Daily)"
                if time_series_key not in data:
                    if 'Information' in data:
                        raise InvalidSymbolError(f"Invalid symbol: {symbol}")
                    raise DataFetcherError(f"Unexpected API response format for {symbol}")

                try:
                    df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
                    df.index = pd.to_datetime(df.index)
                    df = df.astype(float)

                    # Rename columns to match stock data format
                    df = df.rename(columns={
                        '1a. open (USD)': '1. open',
                        '2a. high (USD)': '2. high',
                        '3a. low (USD)': '3. low',
                        '4a. close (USD)': '4. close',
                        '5. volume': '5. volume'
                    })

                    # Select only the columns we need
                    df = df[['1. open', '2. high', '3. low', '4. close', '5. volume']]
                    df = df.astype(float)

                    # Sort by date descending to get most recent first
                    df = df.sort_index(ascending=False)

                    # Only keep the most recent data points to match intraday-like behavior
                    df = df.head(100)  # Keep last 100 data points
                except (KeyError, ValueError) as e:
                    raise DataFetcherError(f"Error processing data for {symbol}: {str(e)}")
            else:
                df, _ = self.ts.get_intraday(
                    symbol=symbol,
                    interval=interval,
                    outputsize='compact'
                )

                # Check for None or empty DataFrame before proceeding
                if df is None or df.empty:
                    raise DataFetcherError(f"No data returned for symbol: {symbol}")

            # Store in cache
            self.db.save_analysis(
                symbol=symbol,
                analysis_data={
                    'score': 0.0,  # Placeholder until analysis is done
                    'macd': 0.0,
                    'macd_signal': 0.0,
                    'ema_short': 0.0,
                    'ema_long': 0.0
                },
                raw_data=df.to_dict()
            )

            return df

        except ValueError as e:
            if "Invalid API call" in str(e):
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")
            elif "API rate limit" in str(e):
                # If we hit rate limit, try to use slightly older cached data
                cached_data = self.db.get_cached_data(symbol, max_age_minutes=15)
                if cached_data is not None:
                    logger.warning("Using older cached data due to rate limit")
                    return pd.DataFrame.from_dict(cached_data)
                raise APIError("API rate limit reached. Please try again later.")
            raise APIError(f"API error: {str(e)}")

        except ConnectionError as e:
            raise APIError(f"Network error while fetching data: {str(e)}")

        except (InvalidSymbolError, APIError) as e:
            # Re-raise these exceptions without wrapping
            raise

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
                # Use raw API endpoint for crypto data
                params = {
                    'function': 'DIGITAL_CURRENCY_DAILY',
                    'symbol': symbol.upper(),
                    'market': 'USD',
                    'apikey': ALPHA_VANTAGE_API_KEY
                }
                response = requests.get(self.base_url, params=params)
                if response.status_code != 200:
                    raise APIError(f"API request failed with status code {response.status_code}")

                data = response.json()

                # Check for various error conditions in the response
                if 'Error Message' in data or ('Information' in data and 'Invalid API call' in data['Information']):
                    raise InvalidSymbolError(f"Invalid symbol: {symbol}")
                if 'Note' in data and 'API call frequency' in data['Note']:
                    raise APIError("API rate limit reached. Please try again later.")

                # Convert the JSON response to a DataFrame
                time_series_key = "Time Series (Digital Currency Daily)"
                if time_series_key not in data:
                    if 'Information' in data:
                        raise InvalidSymbolError(f"Invalid symbol: {symbol}")
                    raise DataFetcherError(f"Unexpected API response format for {symbol}")

                try:
                    df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
                    df.index = pd.to_datetime(df.index)

                    # Rename columns to match stock data format and select USD values
                    df = df.rename(columns={
                        '1a. open (USD)': '1. open',
                        '2a. high (USD)': '2. high',
                        '3a. low (USD)': '3. low',
                        '4a. close (USD)': '4. close',
                        '5. volume': '5. volume'
                    })

                    # Select only the columns we need
                    df = df[['1. open', '2. high', '3. low', '4. close', '5. volume']]
                    df = df.astype(float)

                    # Sort by date descending to get most recent first
                    df = df.sort_index(ascending=False)
                except (KeyError, ValueError) as e:
                    raise DataFetcherError(f"Error processing data for {symbol}: {str(e)}")
            else:
                df, _ = self.ts.get_daily(symbol=symbol, outputsize='compact')

            # Validate response data
            if df is None or df.empty:
                raise DataFetcherError(f"No data returned for symbol: {symbol}")

            df.index = pd.to_datetime(df.index)
            # Sort by date descending to get most recent first
            df = df.sort_index(ascending=False)
            return df

        except ValueError as e:
            if "Invalid API call" in str(e):
                raise InvalidSymbolError(f"Invalid symbol: {symbol}")
            elif "API rate limit" in str(e):
                raise APIError("API rate limit reached. Please try again later.")
            raise APIError(f"API error: {str(e)}")

        except ConnectionError as e:
            raise APIError(f"Network error while fetching data: {str(e)}")

        except (InvalidSymbolError, APIError) as e:
            # Re-raise these exceptions without wrapping
            raise

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

    def close(self):
        """Close the database connection"""
        self.db.close()

    def get_top_gainers_losers(self) -> Tuple[list, list]:
        """
        Fetch the top gainers and losers from the market

        Returns:
            Tuple[list, list]: A tuple containing two lists:
                - First list contains dictionaries of top gainers
                - Second list contains dictionaries of top losers
                Each dictionary contains: ticker, price, change_amount, change_percentage

        Raises:
            APIError: If there's an error with the API request
        """
        try:
            params = {
                'function': 'TOP_GAINERS_LOSERS',
                'apikey': ALPHA_VANTAGE_API_KEY
            }

            response = requests.get(self.base_url, params=params)

            if response.status_code != 200:
                if response.status_code == 429:
                    raise APIError("API rate limit reached. Please try again later.")
                raise APIError(f"API request failed with status code {response.status_code}")

            data = response.json()

            # Check for API errors
            if 'Error Message' in data:
                raise APIError(f"API error: {data['Error Message']}")
            if 'Note' in data and 'API call frequency' in data['Note']:
                raise APIError("API rate limit reached. Please try again later.")

            # Extract gainers and losers lists
            gainers = data.get('top_gainers', [])
            losers = data.get('top_losers', [])

            return gainers, losers

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error while fetching data: {str(e)}")
        except APIError:
            raise
        except Exception as e:
            raise DataFetcherError(f"Error fetching top gainers/losers: {str(e)}")