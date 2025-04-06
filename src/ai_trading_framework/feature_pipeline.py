"""
Unified Feature Engineering Pipeline for AI Trading System
"""

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import StandardScaler
from src.ai_trading_framework.custom_transformers import (
    MarketFeatureExtractor,
    SentimentFeatureExtractor,
    OnChainFeatureExtractor
)

def build_feature_pipeline():
    market_pipe = Pipeline([
        ('extract', MarketFeatureExtractor()),
        ('scale', StandardScaler())
    ])

    sentiment_pipe = Pipeline([
        ('extract', SentimentFeatureExtractor()),
        ('scale', StandardScaler())
    ])

    onchain_pipe = Pipeline([
        ('extract', OnChainFeatureExtractor()),
        ('scale', StandardScaler())
    ])

    full_pipeline = FeatureUnion([
        ('market', market_pipe),
        ('sentiment', sentiment_pipe),
        ('onchain', onchain_pipe)
    ])

    return full_pipeline