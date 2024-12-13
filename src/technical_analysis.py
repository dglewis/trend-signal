import pandas as pd
import numpy as np
from ta.trend import MACD
from ta.momentum import RSIIndicator
from config.config import TECHNICAL_SETTINGS

class TechnicalAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.scores = {}

    def calculate_macd(self) -> pd.DataFrame:
        """Calculate MACD indicator"""
        macd = MACD(
            close=self.data['4. close'],
            window_slow=TECHNICAL_SETTINGS['ema_long'],
            window_fast=TECHNICAL_SETTINGS['ema_short'],
            window_sign=TECHNICAL_SETTINGS['macd_signal']
        )
        self.data['macd'] = macd.macd()
        self.data['macd_signal'] = macd.macd_signal()
        self.data['macd_diff'] = macd.macd_diff()
        return self.data

    def calculate_ema(self) -> pd.DataFrame:
        """Calculate EMA indicators"""
        self.data['ema_short'] = self.data['4. close'].ewm(
            span=TECHNICAL_SETTINGS['ema_short'], adjust=False).mean()
        self.data['ema_long'] = self.data['4. close'].ewm(
            span=TECHNICAL_SETTINGS['ema_long'], adjust=False).mean()
        return self.data

    def calculate_score(self) -> float:
        """
        Calculate overall technical score (0-100)
        Basic scoring system for MVP:
        - MACD above signal line: +30 points
        - Short EMA above long EMA: +30 points
        - Volume increasing: +20 points
        - Price above short EMA: +20 points
        """
        score = 0
        latest = self.data.iloc[-1]

        # MACD Score
        if latest['macd'] > latest['macd_signal']:
            score += 30

        # EMA Score
        if latest['ema_short'] > latest['ema_long']:
            score += 30

        # Volume Score (compare to 5-period average)
        vol_avg = self.data['5. volume'].rolling(window=5).mean().iloc[-1]
        if latest['5. volume'] > vol_avg:
            score += 20

        # Price vs EMA Score
        if latest['4. close'] > latest['ema_short']:
            score += 20

        return score

    def analyze(self) -> dict:
        """Perform full technical analysis"""
        self.calculate_macd()
        self.calculate_ema()
        score = self.calculate_score()

        return {
            'score': score,
            'macd': self.data['macd'].iloc[-1],
            'macd_signal': self.data['macd_signal'].iloc[-1],
            'ema_short': self.data['ema_short'].iloc[-1],
            'ema_long': self.data['ema_long'].iloc[-1]
        }