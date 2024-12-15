from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from config.config import DATABASE_URL, BASE_DIR
from typing import Optional
import os
import logging

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
                    data_str = str(raw_data)
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

    def get_cached_data(self, symbol: str, max_age_minutes: int = 5) -> Optional[dict]:
        """
        Get cached data for a symbol if it exists and is not older than max_age_minutes

        Args:
            symbol: The stock/crypto symbol
            max_age_minutes: Maximum age of cached data in minutes

        Returns:
            dict: The cached data if available and fresh, None otherwise
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
            logger.info(f"Looking for cache for {symbol} newer than {cutoff_time}")

            latest = self.session.query(StockAnalysis)\
                .filter_by(symbol=symbol)\
                .filter(StockAnalysis.timestamp >= cutoff_time)\
                .order_by(StockAnalysis.timestamp.desc())\
                .first()

            if latest:
                logger.info(f"Found cache entry for {symbol} from {latest.timestamp}")
                if latest.data_json:
                    try:
                        data = eval(latest.data_json)  # Convert string back to dict
                        if not isinstance(data, dict):
                            logger.error(f"Cached data for {symbol} is not a dictionary")
                            return None
                        return data
                    except Exception as e:
                        logger.error(f"Error parsing cached data for {symbol}: {str(e)}", exc_info=True)
                        return None
                else:
                    logger.info(f"No raw data in cache for {symbol}")
            else:
                logger.info(f"No recent cache entry found for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error getting cached data for {symbol}: {str(e)}", exc_info=True)
            return None

    def close(self):
        """Close the database session"""
        try:
            self.session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")