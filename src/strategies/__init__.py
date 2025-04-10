"""
Trading strategies package.
"""
from src.strategy_framework import MovingAverageCrossStrategy, RSIStrategy
from src.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from src.strategies.macd_strategy import MACDStrategy

__all__ = [
    'MovingAverageCrossStrategy',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'MACDStrategy',
]
