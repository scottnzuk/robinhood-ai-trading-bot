"""
Bollinger Bands trading strategy implementation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any

from src.strategy_framework import TechnicalStrategy, Signal, SignalType


class BollingerBandsStrategy(TechnicalStrategy):
    """
    Bollinger Bands trading strategy.
    
    Generates buy signals when price crosses below the lower band and sell signals
    when price crosses above the upper band. The confidence of the signal is based
    on the distance between the price and the middle band (normalized by the band width).
    """
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        """
        Initialize the Bollinger Bands strategy.
        
        Args:
            window: The window size for the moving average (default: 20)
            num_std: The number of standard deviations for the bands (default: 2.0)
        """
        super().__init__({"window": window, "num_std": num_std})
        self.window = window
        self.num_std = num_std
    
    def generate_signals(self, data: Dict[str, Any]) -> List[Signal]:
        """
        Generate trading signals based on Bollinger Bands.
        
        Args:
            data: Dictionary mapping symbols to their price data
            
        Returns:
            List of trading signals
        """
        signals = []
        
        for symbol, df in data.items():
            if not isinstance(df, pd.DataFrame):
                continue
            
            # Calculate Bollinger Bands
            df = df.copy()
            df['middle_band'] = df['close'].rolling(window=self.window).mean()
            df['std'] = df['close'].rolling(window=self.window).std()
            df['upper_band'] = df['middle_band'] + (df['std'] * self.num_std)
            df['lower_band'] = df['middle_band'] - (df['std'] * self.num_std)
            
            # Calculate %B (percent bandwidth) - where price is relative to the bands
            df['percent_b'] = (df['close'] - df['lower_band']) / (df['upper_band'] - df['lower_band'])
            
            # Skip if we don't have enough data
            if df.iloc[-1]['middle_band'] is np.nan:
                continue
            
            # Get the last two rows to check for crossovers
            if len(df) < 2:
                continue
                
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            # Calculate band width as percentage of price
            band_width = (last_row['upper_band'] - last_row['lower_band']) / last_row['middle_band']
            
            # Signal generation logic
            signal_type = SignalType.HOLD
            confidence = 0.5
            
            # Price crossing below lower band (buy signal)
            if prev_row['close'] >= prev_row['lower_band'] and last_row['close'] < last_row['lower_band']:
                signal_type = SignalType.BUY
                # Confidence based on band width (wider bands = higher volatility = lower confidence)
                # and distance from middle band (further = higher confidence)
                distance_factor = abs(last_row['close'] - last_row['middle_band']) / last_row['middle_band']
                confidence = min(0.9, 0.5 + distance_factor * (1.0 / band_width))
            
            # Price crossing above upper band (sell signal)
            elif prev_row['close'] <= prev_row['upper_band'] and last_row['close'] > last_row['upper_band']:
                signal_type = SignalType.SELL
                # Similar confidence calculation as for buy
                distance_factor = abs(last_row['close'] - last_row['middle_band']) / last_row['middle_band']
                confidence = min(0.9, 0.5 + distance_factor * (1.0 / band_width))
            
            # Extreme readings in %B can also generate signals
            elif last_row['percent_b'] < 0:  # Price below lower band
                signal_type = SignalType.BUY
                confidence = min(0.8, 0.5 + abs(last_row['percent_b']) * 0.5)
            elif last_row['percent_b'] > 1:  # Price above upper band
                signal_type = SignalType.SELL
                confidence = min(0.8, 0.5 + (last_row['percent_b'] - 1) * 0.5)
            
            # Create signal
            if signal_type != SignalType.HOLD:
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    source=self.name,
                    metadata={
                        "middle_band": last_row['middle_band'],
                        "upper_band": last_row['upper_band'],
                        "lower_band": last_row['lower_band'],
                        "percent_b": last_row['percent_b'],
                        "band_width": band_width
                    }
                ))
        
        return signals
    
    def get_required_data(self) -> List[str]:
        """List of required data fields"""
        return ["symbol", "close", "high", "low", "open"]
