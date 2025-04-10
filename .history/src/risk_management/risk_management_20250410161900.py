"""
Risk management system for trading operations.
"""
import math
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from src.strategy_framework import Signal, SignalType


@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_size: float = 0.05  # Maximum position size as % of portfolio
    max_portfolio_risk: float = 0.02  # Maximum portfolio risk per day
    max_symbol_risk: float = 0.01  # Maximum risk per symbol
    max_sector_risk: float = 0.20  # Maximum exposure to any sector
    max_correlation_risk: float = 0.30  # Maximum exposure to correlated assets
    volatility_scaling: bool = True  # Scale position size by volatility
    max_drawdown_pct: float = 0.05  # Maximum daily drawdown allowed
    stop_loss_pct: float = 0.05  # Default stop loss percentage
    take_profit_pct: float = 0.10  # Default take profit percentage


@dataclass
class PositionSizing:
    """Position sizing calculation result"""
    symbol: str
    quantity: float
    notional_value: float
    percentage_of_portfolio: float
    risk_contribution: float
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None


class RiskManager:
    """Risk management system for trading operations"""
    
    def __init__(self, parameters: Optional[RiskParameters] = None):
        self.parameters = parameters or RiskParameters()
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.portfolio_value: float = 0.0
        self.cash_balance: float = 0.0
        self.daily_realized_pnl: float = 0.0
        self.max_drawdown_reached: bool = False
        self.sector_exposure: Dict[str, float] = {}
        self.trade_history: List[Dict[str, Any]] = []
    
    def update_portfolio(self, portfolio_data: Dict[str, Any]) -> None:
        """Update portfolio information"""
        self.portfolio_value = portfolio_data.get('portfolio_value', 0.0)
        self.cash_balance = portfolio_data.get('cash', 0.0)
        self.positions = portfolio_data.get('positions', {})
        
        # Calculate sector exposure
        self.sector_exposure = {}
        for symbol, position in self.positions.items():
            sector = position.get('sector', 'Unknown')
            value = position.get('market_value', 0.0)
            if sector not in self.sector_exposure:
                self.sector_exposure[sector] = 0.0
            self.sector_exposure[sector] += value
        
        # Convert to percentages
        if self.portfolio_value > 0:
            self.sector_exposure = {
                sector: value / self.portfolio_value 
                for sector, value in self.sector_exposure.items()
            }
    
    def calculate_position_size(
        self, 
        signal: Signal, 
        price: float, 
        volatility: float,
        market_data: Dict[str, Any]
    ) -> PositionSizing:
        """Calculate appropriate position size based on signal and risk parameters"""
        # Base position size as percentage of portfolio
        base_position_pct = self.parameters.max_position_size * signal.confidence
        
        # Adjust for volatility if enabled
        if self.parameters.volatility_scaling and volatility > 0:
            # Normalize volatility (assuming average is around 0.20 or 20%)
            normalized_volatility = volatility / 0.20
            # Inverse relationship: higher volatility = smaller position
            volatility_factor = 1.0 / normalized_volatility
            # Limit the adjustment factor to a reasonable range
            volatility_factor = max(0.25, min(2.0, volatility_factor))
            base_position_pct *= volatility_factor
        
        # Check if we already have a position in this symbol
        current_position = self.positions.get(signal.symbol, {})
        current_quantity = current_position.get('quantity', 0.0)
        current_value = current_position.get('market_value', 0.0)
        current_pct = current_value / self.portfolio_value if self.portfolio_value > 0 else 0.0
        
        # Adjust for existing position
        if signal.is_buy and current_quantity > 0:
            # If adding to position, consider current exposure
            available_pct = max(0, base_position_pct - current_pct)
            position_pct = available_pct
        elif signal.is_sell and current_quantity > 0:
            # If reducing position, use current position size
            position_pct = current_pct
        else:
            position_pct = base_position_pct
        
        # Calculate notional value
        notional_value = self.portfolio_value * position_pct
        
        # Calculate quantity
        quantity = notional_value / price if price > 0 else 0.0
        
        # For sell signals, limit to current quantity
        if signal.is_sell:
            quantity = min(quantity, current_quantity)
        
        # Calculate risk contribution
        risk_amount = notional_value * self.parameters.stop_loss_pct
        risk_contribution = risk_amount / self.portfolio_value if self.portfolio_value > 0 else 0.0
        
        # Calculate stop loss and take profit prices
        stop_loss_price = None
        take_profit_price = None
        
        if signal.is_buy:
            stop_loss_price = price * (1 - self.parameters.stop_loss_pct)
            take_profit_price = price * (1 + self.parameters.take_profit_pct)
        elif signal.is_sell:
            # For short positions, stop loss is above entry price
            stop_loss_price = price * (1 + self.parameters.stop_loss_pct)
            take_profit_price = price * (1 - self.parameters.take_profit_pct)
        
        return PositionSizing(
            symbol=signal.symbol,
            quantity=quantity,
            notional_value=notional_value,
            percentage_of_portfolio=position_pct,
            risk_contribution=risk_contribution,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )
    
    def validate_trade(
        self, 
        signal: Signal, 
        position_sizing: PositionSizing,
        market_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate if a trade meets risk management criteria"""
        if position_sizing.quantity <= 0:
            return False, "Invalid position size"
        
        # Check if maximum drawdown has been reached
        if self.max_drawdown_reached:
            return False, "Maximum daily drawdown reached"
        
        # Check portfolio risk limit
        total_risk = sum(pos.get('risk_contribution', 0.0) for pos in self.positions.values())
        new_total_risk = total_risk + position_sizing.risk_contribution
        
        if new_total_risk > self.parameters.max_portfolio_risk:
            return False, f"Portfolio risk limit exceeded: {new_total_risk:.2%} > {self.parameters.max_portfolio_risk:.2%}"
        
        # Check symbol risk limit
        if position_sizing.risk_contribution > self.parameters.max_symbol_risk:
            return False, f"Symbol risk limit exceeded: {position_sizing.risk_contribution:.2%} > {self.parameters.max_symbol_risk:.2%}"
        
        # Check sector risk limit
        symbol_data = market_data.get(signal.symbol, {})
        sector = symbol_data.get('sector', 'Unknown')
        current_sector_exposure = self.sector_exposure.get(sector, 0.0)
        new_sector_exposure = current_sector_exposure + position_sizing.percentage_of_portfolio
        
        if new_sector_exposure > self.parameters.max_sector_risk:
            return False, f"Sector risk limit exceeded for {sector}: {new_sector_exposure:.2%} > {self.parameters.max_sector_risk:.2%}"
        
        # Check correlation risk (simplified)
        # In a real implementation, you would calculate correlations between assets
        
        return True, "Trade validated"
    
    def calculate_volatility(self, symbol: str, market_data: Dict[str, Any]) -> float:
        """Calculate historical volatility for a symbol"""
        symbol_data = market_data.get(symbol, {})
        prices = symbol_data.get('historical_prices', [])
        
        if not prices or len(prices) < 10:
            return 0.20  # Default volatility if not enough data
        
        # Calculate daily returns
        prices_series = pd.Series(prices)
        returns = prices_series.pct_change().dropna()
        
        # Calculate annualized volatility
        daily_volatility = returns.std()
        annualized_volatility = daily_volatility * math.sqrt(252)  # Assuming 252 trading days
        
        return annualized_volatility
    
    def update_drawdown(self, current_portfolio_value: float) -> None:
        """Update drawdown tracking"""
        # Track daily high water mark
        if not hasattr(self, 'daily_high_value'):
            self.daily_high_value = current_portfolio_value
        
        if current_portfolio_value > self.daily_high_value:
            self.daily_high_value = current_portfolio_value
        
        # Calculate current drawdown
        if self.daily_high_value > 0:
            current_drawdown = (self.daily_high_value - current_portfolio_value) / self.daily_high_value
            
            # Check if max drawdown reached
            if current_drawdown > self.parameters.max_drawdown_pct:
                self.max_drawdown_reached = True
    
    def record_trade(self, signal: Signal, position_sizing: PositionSizing, execution_price: float) -> None:
        """Record a trade in the history"""
        trade = {
            'timestamp': datetime.now(timezone.utc),
            'symbol': signal.symbol,
            'action': signal.signal_type.name,
            'quantity': position_sizing.quantity,
            'price': execution_price,
            'notional_value': position_sizing.quantity * execution_price,
            'confidence': signal.confidence,
            'stop_loss': position_sizing.stop_loss_price,
            'take_profit': position_sizing.take_profit_price
        }
        
        self.trade_history.append(trade)
    
    def reset_daily_metrics(self) -> None:
        """Reset daily tracking metrics"""
        self.daily_realized_pnl = 0.0
        self.max_drawdown_reached = False
        self.daily_high_value = self.portfolio_value
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Generate a risk report"""
        return {
            'timestamp': datetime.now(timezone.utc),
            'portfolio_value': self.portfolio_value,
            'cash_balance': self.cash_balance,
            'daily_pnl': self.daily_realized_pnl,
            'max_drawdown_reached': self.max_drawdown_reached,
            'sector_exposure': self.sector_exposure,
            'position_count': len(self.positions),
            'risk_parameters': vars(self.parameters)
        }
