from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from config.config import DATABASE_URL, BASE_DIR
from typing import Optional, Dict
import os
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure data directory exists
data_dir = BASE_DIR / 'data'
data_dir.mkdir(exist_ok=True)
logger.info(f"Using database at: {DATABASE_URL}")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class StockAnalysis(Base):
    __tablename__ = 'stock_analysis'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    score = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    ema_short = Column(Float)
    ema_long = Column(Float)
    alert_triggered = Column(Boolean, default=False)
    data_json = Column(String)  # Store the raw data as JSON

class DatabaseManager:
    def __init__(self):
        Base.metadata.create_all(engine)
        self.session = Session()

    def save_analysis(self, symbol: str, analysis_data: dict, raw_data: dict = None) -> None:
        """Save technical analysis results and raw data to database"""
        try:
            # Validate input data
            required_fields = ['score', 'macd', 'macd_signal', 'ema_short', 'ema_long']
            missing_fields = [field for field in required_fields if field not in analysis_data]
            if missing_fields:
                raise ValueError(f"Missing required fields in analysis_data: {missing_fields}")

            # Convert raw_data to string safely
            if raw_data is not None:
                try:
                    # Convert any Timestamp objects to strings
                    processed_data = {}
                    for col, values in raw_data.items():
                        processed_data[col] = {
                            str(k): v for k, v in values.items()
                        }
                    data_str = str(processed_data)
                    if len(data_str) > 1000000:  # Basic size check
                        logger.warning(f"Large raw_data for {symbol} ({len(data_str)} chars)")
                except Exception as e:
                    logger.error(f"Error converting raw_data to string: {str(e)}")
                    data_str = None
            else:
                data_str = None

            analysis = StockAnalysis(
                symbol=symbol,
                score=float(analysis_data['score']),
                macd=float(analysis_data['macd']),
                macd_signal=float(analysis_data['macd_signal']),
                ema_short=float(analysis_data['ema_short']),
                ema_long=float(analysis_data['ema_long']),
                data_json=data_str
            )
            self.session.add(analysis)
            self.session.commit()
            logger.info(f"Saved analysis for {symbol}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving analysis for {symbol}: {str(e)}", exc_info=True)
            raise

    def get_latest_analysis(self, symbol: str) -> Optional[StockAnalysis]:
        """Get the most recent analysis for a symbol"""
        try:
            return self.session.query(StockAnalysis)\
                .filter_by(symbol=symbol)\
                .order_by(StockAnalysis.timestamp.desc())\
                .first()
        except Exception as e:
            logger.error(f"Error getting latest analysis for {symbol}: {str(e)}")
            return None

    def get_cached_data(self, symbol: str, max_age_minutes: int = 5) -> Optional[Dict]:
        """Get cached data for a symbol if it exists and is not too old"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            logger.info(f"Looking for cache for {symbol} newer than {cutoff_time}")

            latest = self.session.query(StockAnalysis)\
                .filter(StockAnalysis.symbol == symbol)\
                .filter(StockAnalysis.timestamp > cutoff_time)\
                .order_by(StockAnalysis.timestamp.desc())\
                .first()

            if latest and latest.data_json:
                logger.info(f"Found cache entry for {symbol} from {latest.timestamp}")
                try:
                    # Convert string representation to dict safely
                    data_dict = eval(latest.data_json)
                    if not isinstance(data_dict, dict):
                        logger.error(f"Cached data for {symbol} is not a dictionary")
                        return None

                    # Ensure all values are dictionaries
                    for col in data_dict:
                        if not isinstance(data_dict[col], dict):
                            logger.error(f"Column {col} data is not a dictionary")
                            return None

                    return data_dict

                except Exception as e:
                    logger.error(f"Error parsing cached data for {symbol}: {str(e)}")
                    return None

            logger.info(f"No recent cache entry found for {symbol}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving cache for {symbol}: {str(e)}")
            return None

    def close(self):
        """Close the database session"""
        try:
            self.session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")