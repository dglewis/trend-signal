from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from config.config import DATABASE_URL
from typing import Optional

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
        analysis = StockAnalysis(
            symbol=symbol,
            score=analysis_data['score'],
            macd=analysis_data['macd'],
            macd_signal=analysis_data['macd_signal'],
            ema_short=analysis_data['ema_short'],
            ema_long=analysis_data['ema_long'],
            data_json=str(raw_data) if raw_data else None
        )
        self.session.add(analysis)
        self.session.commit()

    def get_latest_analysis(self, symbol: str) -> StockAnalysis:
        """Get the most recent analysis for a symbol"""
        return self.session.query(StockAnalysis)\
            .filter_by(symbol=symbol)\
            .order_by(StockAnalysis.timestamp.desc())\
            .first()

    def get_cached_data(self, symbol: str, max_age_minutes: int = 5) -> Optional[dict]:
        """
        Get cached data for a symbol if it exists and is not older than max_age_minutes

        Args:
            symbol: The stock/crypto symbol
            max_age_minutes: Maximum age of cached data in minutes

        Returns:
            dict: The cached data if available and fresh, None otherwise
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        latest = self.session.query(StockAnalysis)\
            .filter_by(symbol=symbol)\
            .filter(StockAnalysis.timestamp >= cutoff_time)\
            .order_by(StockAnalysis.timestamp.desc())\
            .first()

        if latest and latest.data_json:
            try:
                return eval(latest.data_json)  # Convert string back to dict
            except:
                return None
        return None

    def close(self):
        """Close the database session"""
        self.session.close()