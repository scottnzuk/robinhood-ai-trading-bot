"""
MACD (Moving Average Convergence Divergence) trading strategy implementation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any

from src.strategy_framework import TechnicalStrategy, Signal, SignalType


class MACDStrategy(TechnicalStrategy):
    """
    MACD (Moving Average Convergence Divergence) trading strategy.
    
    Generates buy signals when the MACD line crosses above the signal line
    and sell signals when the MACD line crosses below the signal line.
    The confidence of the signal is based on the strength of the crossover
    and the histogram value.
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        Initialize the MACD strategy.
        
        Args:
            fast_period: The period for the fast EMA (default: 12)
            slow_period: The period for the slow EMA (default: 26)
            signal_period: The period for the signal line EMA (default: 9)
        """
        super().__init__({
            "fast_period": fast_period, 
            "slow_period": slow_period, 
            "signal_period": signal_period
        })
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def generate_signals(self, data: Dict[str, Any]) -> List[Signal]:
        """
        Generate trading signals based on MACD crossovers.
        
        Args:
            data: Dictionary mapping symbols to their price data
            
        Returns:
            List of trading signals
        """
        signals = []
        
        for symbol, df in data.items():
            if not isinstance(df, pd.DataFrame):
                continue
            
            # Calculate MACD components
            df = df.copy()
            
            # Calculate EMAs
            df['ema_fast'] = df['close'].ewm(span=self.fast_period, adjust=False).mean()
            df['ema_slow'] = df['close'].ewm(span=self.slow_period, adjust=False).mean()
            
            # Calculate MACD line and signal line
            df['macd'] = df['ema_fast'] - df['ema_slow']
            df['signal_line'] = df['macd'].ewm(span=self.signal_period, adjust=False).mean()
            
            # Calculate histogram
            df['histogram'] = df['macd'] - df['signal_line']
            
            # Skip if we don't have enough data
            if df.iloc[-1]['signal_line'] is np.nan:
                continue
            
            # Get the last two rows to check for crossovers
            if len(df) < 2:
                continue
                
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            # Signal generation logic
            signal_type = SignalType.HOLD
            confidence = 0.5
            
            # MACD line crossing above signal line (buy signal)
            if prev_row['macd'] <= prev_row['signal_line'] and last_row['macd'] > last_row['signal_line']:
                signal_type = SignalType.BUY
                
                # Calculate confidence based on:
                # 1. Strength of crossover (difference between MACD and signal)
                # 2. Direction of histogram (increasing histogram is stronger signal)
                # 3. Absolute value of MACD (higher absolute value means stronger trend)
                
                crossover_strength = abs(last_row['macd'] - last_row['signal_line']) / abs(last_row['signal_line']) if last_row['signal_line'] != 0 else 0
                histogram_direction = 1 if last_row['histogram'] > prev_row['histogram'] else 0.5
                macd_strength = min(1.0, abs(last_row['macd']) / 2)
                
                # Combine factors for final confidence
                confidence = min(0.9, 0.5 + (crossover_strength * 0.2 + histogram_direction * 0.2 + macd_strength * 0.1))
            
            # MACD line crossing below signal line (sell signal)
            elif prev_row['macd'] >= prev_row['signal_line'] and last_row['macd'] < last_row['signal_line']:
                signal_type = SignalType.SELL
                
                # Similar confidence calculation as for buy
                crossover_strength = abs(last_row['macd'] - last_row['signal_line']) / abs(last_row['signal_line']) if last_row['signal_line'] != 0 else 0
                histogram_direction = 1 if last_row['histogram'] < prev_row['histogram'] else 0.5
                macd_strength = min(1.0, abs(last_row['macd']) / 2)
                
                confidence = min(0.9, 0.5 + (crossover_strength * 0.2 + histogram_direction * 0.2 + macd_strength * 0.1))
            
            # Create signal
            if signal_type != SignalType.HOLD:
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    source=self.name,
                    metadata={
                        "macd": last_row['macd'],
                        "signal_line": last_row['signal_line'],
                        "histogram": last_row['histogram'],
                        "fast_ema": last_row['ema_fast'],
                        "slow_ema": last_row['ema_slow']
                    }
                ))
        
        return signals
    
    def get_required_data(self) -> List[str]:
        """List of required data fields"""
        return ["symbol", "close"]
