from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.config import DATABASE_URL

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

class DatabaseManager:
    def __init__(self):
        Base.metadata.create_all(engine)
        self.session = Session()

    def save_analysis(self, symbol: str, analysis_data: dict) -> None:
        """Save technical analysis results to database"""
        analysis = StockAnalysis(
            symbol=symbol,
            score=analysis_data['score'],
            macd=analysis_data['macd'],
            macd_signal=analysis_data['macd_signal'],
            ema_short=analysis_data['ema_short'],
            ema_long=analysis_data['ema_long']
        )
        self.session.add(analysis)
        self.session.commit()

    def get_latest_analysis(self, symbol: str) -> StockAnalysis:
        """Get the most recent analysis for a symbol"""
        return self.session.query(StockAnalysis)\
            .filter_by(symbol=symbol)\
            .order_by(StockAnalysis.timestamp.desc())\
            .first()

    def close(self):
        """Close the database session"""
        self.session.close()