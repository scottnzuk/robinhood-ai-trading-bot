import pandas as pd
import ohlcv  # from typedduck/ohlcv
from Algorithmic_Trading_Models import strategies

def detect_candles(df: pd.DataFrame):
    """
    Detect candlestick patterns using typedduck/ohlcv.
    Returns list of pattern names.
    """
    patterns = ohlcv.detect(df)
    return patterns

def generate_signals(df: pd.DataFrame):
    """
    Generate trading signals using Algorithmic_Trading_Models strategies.
    Returns DataFrame with signals.
    """
    # Example: Moving Average Cross Strategy
    strat = strategies.MovingAverageCrossStrategy(df)
    signals = strat.generate_signals()

    # Example: add RSI filter
    rsi_strat = strategies.RSIStrategy(df)
    rsi_signals = rsi_strat.generate_signals()

    # Combine signals (AND logic)
    combined = (signals['signal'] != 0) & (rsi_signals['signal'] != 0)
    df['combined_signal'] = combined.astype(int)

    return df[['combined_signal']]