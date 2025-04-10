"""
Backtesting framework for trading strategies.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
import os
import json
from dataclasses import dataclass, field

from src.strategy_framework import Strategy, Signal, SignalType, StrategyRegistry
from src.risk_management import RiskManager, RiskParameters, PositionSizing


@dataclass
class BacktestParameters:
    """Parameters for backtest configuration"""
    initial_capital: float = 100000.0
    commission_pct: float = 0.001  # 0.1% commission
    slippage_pct: float = 0.001  # 0.1% slippage
    enable_short_selling: bool = True
    max_positions: int = 10
    risk_free_rate: float = 0.02  # 2% annual risk-free rate
    data_frequency: str = "daily"  # daily, hourly, minute
    rebalance_frequency: str = "daily"  # daily, weekly, monthly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class BacktestPosition:
    """Position in a backtest"""
    symbol: str
    quantity: float
    entry_price: float
    entry_date: datetime
    direction: str  # long or short
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    pnl: float = 0.0
    return_pct: float = 0.0
    status: str = "open"  # open, closed, stopped, target_reached


@dataclass
class BacktestResults:
    """Results of a backtest"""
    equity_curve: List[float] = field(default_factory=list)
    dates: List[datetime] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    drawdowns: List[float] = field(default_factory=list)
    positions_history: List[Dict[str, Any]] = field(default_factory=list)
    signals_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not self.equity_curve or len(self.equity_curve) < 2:
            return {}
        
        # Basic metrics
        initial_equity = self.equity_curve[0]
        final_equity = self.equity_curve[-1]
        total_return = (final_equity / initial_equity) - 1
        
        # Trading metrics
        total_trades = len(self.trades)
        if total_trades == 0:
            return {
                "total_return": total_return,
                "total_trades": 0
            }
        
        winning_trades = sum(1 for trade in self.trades if trade["pnl"] > 0)
        losing_trades = sum(1 for trade in self.trades if trade["pnl"] < 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Calculate returns
        returns = [
            (self.equity_curve[i] / self.equity_curve[i-1]) - 1 
            for i in range(1, len(self.equity_curve))
        ]
        
        # Annualized metrics
        trading_days = len(returns)
        if trading_days > 0:
            annual_factor = 252 / trading_days  # Assuming 252 trading days per year
            annualized_return = (1 + total_return) ** annual_factor - 1
            
            # Volatility and Sharpe ratio
            daily_volatility = np.std(returns)
            annualized_volatility = daily_volatility * np.sqrt(252)
            
            risk_free_daily = 0.02 / 252  # Assuming 2% annual risk-free rate
            excess_returns = [r - risk_free_daily for r in returns]
            sharpe_ratio = (np.mean(excess_returns) / daily_volatility) * np.sqrt(252) if daily_volatility > 0 else 0
            
            # Maximum drawdown
            max_drawdown = max(self.drawdowns) if self.drawdowns else 0
            
            # Profit factor
            total_profit = sum(trade["pnl"] for trade in self.trades if trade["pnl"] > 0)
            total_loss = sum(abs(trade["pnl"]) for trade in self.trades if trade["pnl"] < 0)
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # Average trade metrics
            avg_profit = total_profit / winning_trades if winning_trades > 0 else 0
            avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
            avg_trade = sum(trade["pnl"] for trade in self.trades) / total_trades
            
            return {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "annualized_volatility": annualized_volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "avg_profit": avg_profit,
                "avg_loss": avg_loss,
                "avg_trade": avg_trade
            }
        
        return {"total_return": total_return, "total_trades": total_trades}
    
    def plot_equity_curve(self, save_path: Optional[str] = None) -> None:
        """Plot equity curve and drawdowns"""
        if not self.equity_curve or len(self.equity_curve) < 2:
            print("Not enough data to plot equity curve")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Convert dates to pandas datetime if they're not already
        dates = pd.to_datetime(self.dates)
        
        # Plot equity curve
        plt.subplot(2, 1, 1)
        plt.plot(dates, self.equity_curve, label='Equity Curve')
        plt.title('Backtest Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Equity')
        plt.grid(True)
        plt.legend()
        
        # Plot drawdowns
        plt.subplot(2, 1, 2)
        plt.fill_between(dates, 0, self.drawdowns, color='red', alpha=0.3)
        plt.title('Drawdowns')
        plt.xlabel('Date')
        plt.ylabel('Drawdown %')
        plt.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    
    def save_results(self, file_path: str) -> None:
        """Save backtest results to a file"""
        # Convert datetime objects to strings for JSON serialization
        results_dict = {
            "equity_curve": self.equity_curve,
            "dates": [date.isoformat() if isinstance(date, datetime) else date for date in self.dates],
            "trades": self.trades,
            "metrics": self.metrics,
            "drawdowns": self.drawdowns,
            "positions_history": self.positions_history,
            "signals_history": [{**s, "date": s["date"].isoformat() if isinstance(s["date"], datetime) else s["date"]} for s in self.signals_history]
        }
        
        with open(file_path, 'w') as f:
            json.dump(results_dict, f, indent=2)


class BacktestEngine:
    """Engine for backtesting trading strategies"""
    
    def __init__(
        self, 
        strategy_registry: StrategyRegistry,
        parameters: Optional[BacktestParameters] = None,
        risk_parameters: Optional[RiskParameters] = None
    ):
        self.strategy_registry = strategy_registry
        self.parameters = parameters or BacktestParameters()
        self.risk_manager = RiskManager(risk_parameters)
        
        # Backtest state
        self.current_date = None
        self.equity = self.parameters.initial_capital
        self.cash = self.parameters.initial_capital
        self.positions: Dict[str, BacktestPosition] = {}
        self.position_value = 0.0
        self.high_water_mark = self.parameters.initial_capital
        
        # Results tracking
        self.results = BacktestResults()
    
    def run(
        self, 
        data: Dict[str, pd.DataFrame],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> BacktestResults:
        """Run backtest on historical data"""
        if not data:
            print("No data provided for backtest")
            return self.results
        
        # Determine date range
        start_date = start_date or self.parameters.start_date
        end_date = end_date or self.parameters.end_date
        
        # Get common date range across all symbols
        all_dates = set()
        for symbol, df in data.items():
            if 'date' in df.columns:
                dates = pd.to_datetime(df['date'])
            else:
                df = df.copy()
                df['date'] = df.index
                dates = pd.to_datetime(df['date'])
            
            if start_date:
                dates = dates[dates >= start_date]
            if end_date:
                dates = dates[dates <= end_date]
            
            all_dates.update(dates.tolist())
        
        # Sort dates
        all_dates = sorted(all_dates)
        
        if not all_dates:
            print("No dates in common date range")
            return self.results
        
        # Initialize results tracking
        self.results.equity_curve.append(self.equity)
        self.results.dates.append(all_dates[0])
        self.results.drawdowns.append(0.0)
        
        # Run simulation for each date
        for date in all_dates:
            self.current_date = date
            
            # Update positions with latest prices
            self._update_positions(data, date)
            
            # Generate signals
            signals = self._generate_signals(data, date)
            
            # Process signals
            self._process_signals(signals, data, date)
            
            # Record daily state
            self._record_daily_state()
        
        # Close any remaining positions at the end of the backtest
        self._close_all_positions(data, all_dates[-1])
        
        # Calculate final metrics
        self.results.metrics = self.results.calculate_metrics()
        
        return self.results
    
    def _update_positions(self, data: Dict[str, pd.DataFrame], date: datetime) -> None:
        """Update positions with latest prices and check stops"""
        self.position_value = 0.0
        
        for symbol, position in list(self.positions.items()):
            # Get latest price
            price = self._get_price(data, symbol, date)
            if price is None:
                continue
            
            # Calculate current value
            direction_multiplier = -1 if position.direction == "short" else 1
            position_value = position.quantity * price * direction_multiplier
            
            # Check stop loss
            if position.stop_loss is not None:
                if (position.direction == "long" and price <= position.stop_loss) or \
                   (position.direction == "short" and price >= position.stop_loss):
                    self._close_position(symbol, price, date, "stopped")
                    continue
            
            # Check take profit
            if position.take_profit is not None:
                if (position.direction == "long" and price >= position.take_profit) or \
                   (position.direction == "short" and price <= position.take_profit):
                    self._close_position(symbol, price, date, "target_reached")
                    continue
            
            # Update position value
            self.position_value += position_value
        
        # Update equity
        self.equity = self.cash + self.position_value
        
        # Update high water mark and drawdown
        if self.equity > self.high_water_mark:
            self.high_water_mark = self.equity
        
        current_drawdown = 0.0
        if self.high_water_mark > 0:
            current_drawdown = (self.high_water_mark - self.equity) / self.high_water_mark
        
        # Record state
        self.results.equity_curve.append(self.equity)
        self.results.dates.append(date)
        self.results.drawdowns.append(current_drawdown)
    
    def _generate_signals(
        self, 
        data: Dict[str, pd.DataFrame], 
        date: datetime
    ) -> Dict[str, Signal]:
        """Generate signals from strategies"""
        # Prepare data for strategies
        strategy_data = {}
        for symbol, df in data.items():
            # Filter data up to current date
            if 'date' in df.columns:
                filtered_df = df[pd.to_datetime(df['date']) <= date].copy()
            else:
                df = df.copy()
                df['date'] = df.index
                filtered_df = df[pd.to_datetime(df['date']) <= date].copy()
            
            if not filtered_df.empty:
                strategy_data[symbol] = filtered_df
        
        # Get signals from strategy registry
        signals = self.strategy_registry.get_combined_signals(strategy_data)
        
        # Record signals
        for symbol, signal in signals.items():
            self.results.signals_history.append({
                "date": date,
                "symbol": symbol,
                "signal_type": signal.signal_type.name,
                "confidence": signal.confidence,
                "source": signal.source
            })
        
        return signals
    
    def _process_signals(
        self, 
        signals: Dict[str, Signal],
        data: Dict[str, pd.DataFrame],
        date: datetime
    ) -> None:
        """Process trading signals"""
        # Prepare portfolio data for risk manager
        portfolio_data = {
            "portfolio_value": self.equity,
            "cash": self.cash,
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "market_value": pos.quantity * self._get_price(data, symbol, date),
                    "direction": pos.direction
                }
                for symbol, pos in self.positions.items()
                if self._get_price(data, symbol, date) is not None
            }
        }
        
        # Update risk manager with current portfolio
        self.risk_manager.update_portfolio(portfolio_data)
        
        # Process buy signals first
        buy_signals = {s: sig for s, sig in signals.items() if sig.is_buy}
        for symbol, signal in buy_signals.items():
            # Skip if already at max positions
            if len(self.positions) >= self.parameters.max_positions and symbol not in self.positions:
                continue
            
            # Get current price
            price = self._get_price(data, symbol, date)
            if price is None:
                continue
            
            # Calculate volatility
            volatility = self._calculate_volatility(data, symbol, date)
            
            # Calculate position size
            market_data = {symbol: {"historical_prices": self._get_historical_prices(data, symbol, date)}}
            position_sizing = self.risk_manager.calculate_position_size(signal, price, volatility, market_data)
            
            # Validate trade
            valid, reason = self.risk_manager.validate_trade(signal, position_sizing, market_data)
            if not valid:
                continue
            
            # Adjust for available cash
            max_quantity = self.cash / price
            quantity = min(position_sizing.quantity, max_quantity)
            
            if quantity <= 0:
                continue
            
            # Apply commission and slippage
            execution_price = price * (1 + self.parameters.slippage_pct)
            commission = quantity * execution_price * self.parameters.commission_pct
            
            # Open position
            self._open_position(
                symbol=symbol,
                quantity=quantity,
                price=execution_price,
                date=date,
                direction="long",
                stop_loss=position_sizing.stop_loss_price,
                take_profit=position_sizing.take_profit_price,
                commission=commission
            )
        
        # Process sell signals
        sell_signals = {s: sig for s, sig in signals.items() if sig.is_sell}
        for symbol, signal in sell_signals.items():
            # Close existing long position if present
            if symbol in self.positions and self.positions[symbol].direction == "long":
                price = self._get_price(data, symbol, date)
                if price is None:
                    continue
                
                # Apply slippage
                execution_price = price * (1 - self.parameters.slippage_pct)
                
                # Close position
                self._close_position(symbol, execution_price, date, "signal")
                continue
            
            # Skip short selling if not enabled
            if not self.parameters.enable_short_selling:
                continue
            
            # Short sell if not already in position
            if symbol not in self.positions:
                # Get current price
                price = self._get_price(data, symbol, date)
                if price is None:
                    continue
                
                # Calculate volatility
                volatility = self._calculate_volatility(data, symbol, date)
                
                # Calculate position size
                market_data = {symbol: {"historical_prices": self._get_historical_prices(data, symbol, date)}}
                position_sizing = self.risk_manager.calculate_position_size(signal, price, volatility, market_data)
                
                # Validate trade
                valid, reason = self.risk_manager.validate_trade(signal, position_sizing, market_data)
                if not valid:
                    continue
                
                # Adjust for available cash (margin requirement)
                margin_requirement = 1.5  # 150% of position value as margin
                max_quantity = self.cash / (price * margin_requirement)
                quantity = min(position_sizing.quantity, max_quantity)
                
                if quantity <= 0:
                    continue
                
                # Apply commission and slippage
                execution_price = price * (1 - self.parameters.slippage_pct)
                commission = quantity * execution_price * self.parameters.commission_pct
                
                # Open short position
                self._open_position(
                    symbol=symbol,
                    quantity=quantity,
                    price=execution_price,
                    date=date,
                    direction="short",
                    stop_loss=position_sizing.stop_loss_price,
                    take_profit=position_sizing.take_profit_price,
                    commission=commission
                )
    
    def _open_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        date: datetime,
        direction: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        commission: float = 0.0
    ) -> None:
        """Open a new position or add to existing position"""
        # Check if position already exists
        if symbol in self.positions:
            existing_position = self.positions[symbol]
            
            # Only add to position if same direction
            if existing_position.direction != direction:
                return
            
            # Calculate new average entry price
            total_quantity = existing_position.quantity + quantity
            total_cost = (existing_position.quantity * existing_position.entry_price) + (quantity * price)
            avg_price = total_cost / total_quantity
            
            # Update position
            existing_position.quantity = total_quantity
            existing_position.entry_price = avg_price
            
            # Deduct from cash
            cost = quantity * price + commission
            self.cash -= cost
            
            # Record position update
            self.results.positions_history.append({
                "date": date,
                "symbol": symbol,
                "action": "add",
                "quantity": quantity,
                "price": price,
                "direction": direction,
                "cost": cost
            })
            
        else:
            # Create new position
            position = BacktestPosition(
                symbol=symbol,
                quantity=quantity,
                entry_price=price,
                entry_date=date,
                direction=direction,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            self.positions[symbol] = position
            
            # Deduct from cash
            cost = quantity * price + commission
            self.cash -= cost
            
            # Record new position
            self.results.positions_history.append({
                "date": date,
                "symbol": symbol,
                "action": "open",
                "quantity": quantity,
                "price": price,
                "direction": direction,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "cost": cost
            })
    
    def _close_position(
        self, 
        symbol: str, 
        price: float, 
        date: datetime,
        reason: str = "signal"
    ) -> None:
        """Close an existing position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculate P&L
        direction_multiplier = -1 if position.direction == "short" else 1
        pnl = direction_multiplier * position.quantity * (price - position.entry_price)
        return_pct = (price / position.entry_price - 1) * direction_multiplier
        
        # Apply commission
        commission = position.quantity * price * self.parameters.commission_pct
        pnl -= commission
        
        # Update cash
        self.cash += position.quantity * price + pnl
        
        # Record trade
        trade = {
            "symbol": symbol,
            "direction": position.direction,
            "entry_date": position.entry_date,
            "entry_price": position.entry_price,
            "exit_date": date,
            "exit_price": price,
            "quantity": position.quantity,
            "pnl": pnl,
            "return_pct": return_pct,
            "duration": (date - position.entry_date).days,
            "reason": reason
        }
        
        self.results.trades.append(trade)
        
        # Record position close
        self.results.positions_history.append({
            "date": date,
            "symbol": symbol,
            "action": "close",
            "quantity": position.quantity,
            "price": price,
            "pnl": pnl,
            "return_pct": return_pct,
            "reason": reason
        })
        
        # Remove position
        del self.positions[symbol]
    
    def _close_all_positions(self, data: Dict[str, pd.DataFrame], date: datetime) -> None:
        """Close all open positions at the end of the backtest"""
        for symbol in list(self.positions.keys()):
            price = self._get_price(data, symbol, date)
            if price is not None:
                self._close_position(symbol, price, date, "end_of_backtest")
    
    def _record_daily_state(self) -> None:
        """Record daily portfolio state"""
        # Record positions
        positions_snapshot = {}
        for symbol, position in self.positions.items():
            positions_snapshot[symbol] = {
                "quantity": position.quantity,
                "entry_price": position.entry_price,
                "direction": position.direction,
                "entry_date": position.entry_date
            }
        
        # Add to positions history
        self.results.positions_history.append({
            "date": self.current_date,
            "action": "snapshot",
            "equity": self.equity,
            "cash": self.cash,
            "positions": positions_snapshot
        })
    
    def _get_price(
        self, 
        data: Dict[str, pd.DataFrame], 
        symbol: str, 
        date: datetime
    ) -> Optional[float]:
        """Get price for a symbol at a specific date"""
        if symbol not in data:
            return None
        
        df = data[symbol]
        
        # Convert date column to datetime if it's not already
        if 'date' in df.columns:
            date_col = pd.to_datetime(df['date'])
        else:
            df = df.copy()
            df['date'] = df.index
            date_col = pd.to_datetime(df['date'])
        
        # Find closest date not exceeding current date
        mask = date_col <= date
        if not mask.any():
            return None
        
        closest_idx = mask.idxmax() if isinstance(mask, pd.Series) else mask.values.argmax()
        
        # Get closing price
        if 'close' in df.columns:
            return df.iloc[closest_idx]['close']
        elif 'price' in df.columns:
            return df.iloc[closest_idx]['price']
        else:
            return None
    
    def _get_historical_prices(
        self, 
        data: Dict[str, pd.DataFrame], 
        symbol: str, 
        date: datetime,
        lookback: int = 60
    ) -> List[float]:
        """Get historical prices for a symbol up to a specific date"""
        if symbol not in data:
            return []
        
        df = data[symbol]
        
        # Convert date column to datetime if it's not already
        if 'date' in df.columns:
            date_col = pd.to_datetime(df['date'])
        else:
            df = df.copy()
            df['date'] = df.index
            date_col = pd.to_datetime(df['date'])
        
        # Filter data up to current date
        mask = date_col <= date
        filtered_df = df[mask].tail(lookback)
        
        # Get closing prices
        if 'close' in filtered_df.columns:
            return filtered_df['close'].tolist()
        elif 'price' in filtered_df.columns:
            return filtered_df['price'].tolist()
        else:
            return []
    
    def _calculate_volatility(
        self, 
        data: Dict[str, pd.DataFrame], 
        symbol: str, 
        date: datetime,
        lookback: int = 20
    ) -> float:
        """Calculate historical volatility for a symbol"""
        prices = self._get_historical_prices(data, symbol, date, lookback)
        
        if len(prices) < 5:
            return 0.20  # Default volatility if not enough data
        
        # Calculate daily returns
        returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]
        
        # Calculate annualized volatility
        daily_volatility = np.std(returns)
        annualized_volatility = daily_volatility * np.sqrt(252)  # Assuming 252 trading days
        
        return annualized_volatility


def load_data(data_dir: str, symbols: List[str] = None) -> Dict[str, pd.DataFrame]:
    """Load historical data for backtesting"""
    data = {}
    
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} does not exist")
        return data
    
    # List all CSV files in directory
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    # Filter by symbols if provided
    if symbols:
        files = [f for f in files if any(s in f for s in symbols)]
    
    # Load each file
    for file in files:
        try:
            file_path = os.path.join(data_dir, file)
            df = pd.read_csv(file_path)
            
            # Extract symbol from filename
            symbol = file.split('.')[0].upper()
            
            # Ensure required columns exist
            required_cols = ['date', 'close']
            if not all(col in df.columns for col in required_cols):
                print(f"Missing required columns in {file}")
                continue
            
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Sort by date
            df = df.sort_values('date')
            
            data[symbol] = df
            
        except Exception as e:
            print(f"Error loading {file}: {str(e)}")
    
    return data
