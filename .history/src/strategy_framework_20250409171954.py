"""
Unified strategy framework for combining technical and AI-based trading strategies.
"""
import abc
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone


class SignalType(Enum):
    """Types of trading signals"""
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class Signal:
    """Trading signal with metadata"""
    symbol: str
    signal_type: SignalType
    confidence: float
    timestamp: datetime = datetime.now(timezone.utc)
    source: str = "unknown"
    metadata: Dict[str, Any] = None
    
    @property
    def is_buy(self) -> bool:
        return self.signal_type == SignalType.BUY
    
    @property
    def is_sell(self) -> bool:
        return self.signal_type == SignalType.SELL
    
    @property
    def is_hold(self) -> bool:
        return self.signal_type == SignalType.HOLD


class Strategy(abc.ABC):
    """Base strategy interface"""
    
    @property
    def name(self) -> str:
        """Strategy name"""
        return self.__class__.__name__
    
    @abc.abstractmethod
    def generate_signals(self, data: Dict[str, Any]) -> List[Signal]:
        """Generate trading signals from data"""
        pass
    
    def get_required_data(self) -> List[str]:
        """List of required data fields"""
        return ["symbol", "close"]


class TechnicalStrategy(Strategy):
    """Base class for technical indicator-based strategies"""
    
    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators on dataframe"""
        return df


class AIStrategy(Strategy):
    """Base class for AI-based strategies"""
    
    def __init__(self, ai_provider: str = "openai", params: Dict[str, Any] = None):
        self.ai_provider = ai_provider
        self.params = params or {}
    
    def get_required_data(self) -> List[str]:
        """AI strategies typically need more context"""
        return ["symbol", "close", "open", "high", "low", "volume", "market_data", "portfolio"]


class StrategyRegistry:
    """Registry for managing and combining multiple strategies"""
    
    def __init__(self):
        self._strategies: Dict[str, Strategy] = {}
        self._weights: Dict[str, float] = {}
    
    def register(self, strategy: Strategy, weight: float = 1.0) -> None:
        """Register a strategy with a weight"""
        self._strategies[strategy.name] = strategy
        self._weights[strategy.name] = weight
    
    def unregister(self, strategy_name: str) -> None:
        """Remove a strategy from the registry"""
        if strategy_name in self._strategies:
            del self._strategies[strategy_name]
            del self._weights[strategy_name]
    
    def get_strategy(self, strategy_name: str) -> Optional[Strategy]:
        """Get a strategy by name"""
        return self._strategies.get(strategy_name)
    
    def list_strategies(self) -> List[str]:
        """List all registered strategies"""
        return list(self._strategies.keys())
    
    def get_combined_signals(self, data: Dict[str, Any]) -> Dict[str, Signal]:
        """Generate signals from all strategies and combine them"""
        all_signals: Dict[str, List[Tuple[Signal, float]]] = {}
        
        # Collect signals from all strategies
        for name, strategy in self._strategies.items():
            weight = self._weights[name]
            try:
                signals = strategy.generate_signals(data)
                for signal in signals:
                    if signal.symbol not in all_signals:
                        all_signals[signal.symbol] = []
                    all_signals[signal.symbol].append((signal, weight))
            except Exception as e:
                print(f"Error in strategy {name}: {str(e)}")
        
        # Combine signals for each symbol
        combined_signals: Dict[str, Signal] = {}
        for symbol, signals in all_signals.items():
            if not signals:
                continue
                
            # Calculate weighted signal type
            total_weight = sum(weight for _, weight in signals)
            if total_weight == 0:
                continue
                
            weighted_signal = sum(signal.signal_type.value * weight for signal, weight in signals) / total_weight
            
            # Determine final signal type
            if weighted_signal > 0.3:
                signal_type = SignalType.BUY
            elif weighted_signal < -0.3:
                signal_type = SignalType.SELL
            else:
                signal_type = SignalType.HOLD
            
            # Calculate average confidence
            avg_confidence = sum(signal.confidence * weight for signal, weight in signals) / total_weight
            
            # Create combined signal
            combined_signals[symbol] = Signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=avg_confidence,
                source="combined",
                metadata={
                    "weighted_value": weighted_signal,
                    "component_signals": len(signals),
                    "strategy_sources": [signal.source for signal, _ in signals]
                }
            )
        
        return combined_signals


# Example technical strategies
class MovingAverageCrossStrategy(TechnicalStrategy):
    """Moving average crossover strategy"""
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        super().__init__({"short_window": short_window, "long_window": long_window})
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, data: Dict[str, Any]) -> List[Signal]:
        signals = []
        for symbol, df in data.items():
            if not isinstance(df, pd.DataFrame):
                continue
                
            # Calculate indicators
            df = df.copy()
            df['short_ma'] = df['close'].rolling(window=self.short_window, min_periods=1).mean()
            df['long_ma'] = df['close'].rolling(window=self.long_window, min_periods=1).mean()
            
            # Generate signal based on last row
            last_row = df.iloc[-1]
            
            if last_row['short_ma'] > last_row['long_ma']:
                signal_type = SignalType.BUY
                # Calculate confidence based on distance between MAs
                confidence = min(0.9, (last_row['short_ma'] / last_row['long_ma'] - 1) * 10)
            elif last_row['short_ma'] < last_row['long_ma']:
                signal_type = SignalType.SELL
                # Calculate confidence based on distance between MAs
                confidence = min(0.9, (last_row['long_ma'] / last_row['short_ma'] - 1) * 10)
            else:
                signal_type = SignalType.HOLD
                confidence = 0.5
            
            signals.append(Signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                source=self.name,
                metadata={
                    "short_ma": last_row['short_ma'],
                    "long_ma": last_row['long_ma']
                }
            ))
        
        return signals


class RSIStrategy(TechnicalStrategy):
    """Relative Strength Index strategy"""
    
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        super().__init__({"period": period, "overbought": overbought, "oversold": oversold})
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def generate_signals(self, data: Dict[str, Any]) -> List[Signal]:
        signals = []
        for symbol, df in data.items():
            if not isinstance(df, pd.DataFrame):
                continue
                
            # Calculate RSI
            df = df.copy()
            delta = df['close'].diff()
            gain = delta.clip(lower=0).rolling(window=self.period, min_periods=1).mean()
            loss = -delta.clip(upper=0).rolling(window=self.period, min_periods=1).mean()
            rs = gain / (loss + 1e-9)  # Add small value to avoid division by zero
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Generate signal based on last row
            last_row = df.iloc[-1]
            rsi = last_row['rsi']
            
            if rsi < self.oversold:
                signal_type = SignalType.BUY
                # Higher confidence the lower the RSI
                confidence = min(0.9, (self.oversold - rsi) / self.oversold)
            elif rsi > self.overbought:
                signal_type = SignalType.SELL
                # Higher confidence the higher the RSI
                confidence = min(0.9, (rsi - self.overbought) / (100 - self.overbought))
            else:
                signal_type = SignalType.HOLD
                # Lower confidence in the middle range
                mid_point = (self.overbought + self.oversold) / 2
                distance = abs(rsi - mid_point)
                range_half = (self.overbought - self.oversold) / 2
                confidence = 0.3 + (0.4 * (1 - (distance / range_half)))
            
            signals.append(Signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                source=self.name,
                metadata={"rsi": rsi}
            ))
        
        return signals
