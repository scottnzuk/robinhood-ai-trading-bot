"""
Custom feature transformers for multi-modal AI trading system.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class MarketFeatureExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        X: pd.DataFrame with OHLCV columns
        """
        df = pd.DataFrame(X)
        df['return'] = df['close'].pct_change().fillna(0)
        df['volatility'] = df['close'].rolling(10).std().fillna(0)
        df['sma_10'] = df['close'].rolling(10).mean().fillna(0)
        df['ema_10'] = df['close'].ewm(span=10).mean().fillna(0)
        df['rsi'] = self.compute_rsi(df['close'])
        features = df[['return', 'volatility', 'sma_10', 'ema_10', 'rsi']].values
        return features

    def compute_rsi(self, series, period=14):
        delta = series.diff().fillna(0)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-6)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(0)

class SentimentFeatureExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        X: list of dicts with 'sentiment_score' and 'timestamp'
        """
        df = pd.DataFrame(X)
        df['sentiment_ma'] = df['sentiment_score'].rolling(5).mean().fillna(0)
        features = df[['sentiment_score', 'sentiment_ma']].values
        return features

class OnChainFeatureExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        X: list of dicts with on-chain metrics
        """
        df = pd.DataFrame(X)
        df['active_norm'] = (df['active_addresses'] - df['active_addresses'].mean()) / (df['active_addresses'].std() + 1e-6)
        df['tx_volume_norm'] = (df['tx_volume'] - df['tx_volume'].mean()) / (df['tx_volume'].std() + 1e-6)
        features = df[['active_norm', 'tx_volume_norm']].values
        return features