import asyncio
import sys
import time
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

from src.api import RobinhoodClient
from src.utils.logger import logger
from src.config import MODE, TRADING_INTERVAL_MINUTES, MAX_TRADES_PER_DAY
from src.trading_utils import is_market_open
from src.exceptions import TradingSystemError, RobinhoodAPIError
from src.execution import CircuitBreaker, AntiGamingSystem, AntiGamingConfig, StrategyExecutor

# Import new trading framework components
from src.strategy_framework import StrategyRegistry, MovingAverageCrossStrategy, RSIStrategy, Signal, SignalType
from src.risk_management import RiskManager, RiskParameters, PositionSizing
from src.ai_trading_engine import AITradingEngine, AITradingStrategy

class TradingBot:
    def __init__(self, demo_mode: bool = False, rh_client: Optional[RobinhoodClient] = None):
        self.trade_count = 0
        self.last_trade_time = None
        self.session_start = datetime.now(timezone.utc)
        self.demo_mode = demo_mode
        self.metrics = {
            'decisions_made': 0,
            'trades_executed': 0,
            'errors': 0,
            'last_decision_time': None
        }
        self.rh_client = rh_client  # Injected or None
        self.circuit_breaker = CircuitBreaker()
        self._lock = asyncio.Lock()
        
        # Initialize strategy registry
        self.strategy_registry = self._setup_strategies()
        
        # Initialize risk manager
        self.risk_manager = RiskManager()
        
        # Initialize AI trading engine
        self.ai_engine = AITradingEngine()
        
        # Trade history for feedback loop
        self.trade_history = []
        
        # Initialize anti-gaming system
        self._setup_anti_gaming_system()
        
        # Initialize strategy executor
        self.strategy_executor = StrategyExecutor(
            account_balance=0.0,  # Will be updated with actual balance
            risk_per_trade=0.02,  # 2% risk per trade
            exchange_api=self.rh_client if self.rh_client else None
        )
        
    async def run(self):
        """Main trading loop"""
        logger.info(f"Starting trading bot session {'(DEMO MODE)' if self.demo_mode else ''}")
        
        try:
            if self.rh_client is None:
                self.rh_client = RobinhoodClient()
            
            if not await self.rh_client.authenticate():
                logger.error("Failed to authenticate with Robinhood")
                if self.demo_mode:
                    raise RobinhoodAPIError("authentication", 401, "Failed to authenticate with Robinhood")
                else:
                    sys.exit(1)
                
            while True:
                try:
                    # Check if circuit breaker is active
                    if self.circuit_breaker.is_active():
                        logger.warning("Circuit breaker active - pausing trading operations")
                        await asyncio.sleep(60)
                        continue
                        
                    if not await self._should_run():
                        await asyncio.sleep(60)
                        continue
                        
                    async with self._lock:  # Thread safety for metrics
                        decisions = await self._analyze_and_decide()
                        await self._execute_trades(decisions)
                    
                    if self.demo_mode:
                        self._display_demo_status()
                        
                    await asyncio.sleep(TRADING_INTERVAL_MINUTES * 60)
                    
                except RobinhoodAPIError as e:
                    self.metrics['errors'] += 1
                    logger.error(f"Robinhood API error: {e.message}")
                    self.circuit_breaker.trip(duration_seconds=300)  # 5 minute pause
                    await asyncio.sleep(10)
                    
                except TradingSystemError as e:
                    self.metrics['errors'] += 1
                    logger.error(f"Trading system error: {str(e)}")
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    self.metrics['errors'] += 1
                    logger.error(f"Critical error in trading loop: {str(e)}")
                    if not self.demo_mode:
                        raise
                    await asyncio.sleep(10)  # Recover in demo mode
                    
        except Exception as e:
            logger.critical(f"Fatal error in trading bot: {str(e)}")
            if not self.demo_mode:
                sys.exit(1)

    async def _should_run(self) -> bool:
        """Check if trading should continue"""
        try:
            # Check market status - use async version
            market_open = await is_market_open()
            if not market_open:
                logger.debug("Market closed - waiting")
                return False
                
            if self.trade_count >= MAX_TRADES_PER_DAY:
                logger.info(f"Reached daily trade limit of {MAX_TRADES_PER_DAY}")
                return False
                
            if datetime.now(timezone.utc) > self.session_start + timedelta(hours=6):
                logger.info("Completed maximum session duration")
                return False
                
            # Check account status
            if self.rh_client:
                account_status = await self.rh_client.check_account_status()
                if not account_status.get('active', False):
                    logger.warning("Account not active for trading")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error checking if trading should run: {str(e)}")
            return False
        
    def _setup_strategies(self) -> StrategyRegistry:
        """Set up and register trading strategies"""
        registry = StrategyRegistry()

        # Automatically discover and register all plugin strategies
        registry.auto_discover_and_register(package="strategies", default_weight=0.3)

        
        # Register technical strategies
        ma_cross = MovingAverageCrossStrategy(short_window=20, long_window=50)
        registry.register(ma_cross, weight=0.3)
        
        rsi_strategy = RSIStrategy(period=14, overbought=70, oversold=30)
        registry.register(rsi_strategy, weight=0.3)
        
        # Register AI strategy
        ai_strategy = AITradingStrategy()
        registry.register(ai_strategy, weight=0.4)
        
        return registry
    
    async def _analyze_and_decide(self) -> Dict[str, Signal]:
        """Perform market analysis and get trading decisions
        
        Returns:
            Dictionary of trading signals by symbol
            
        Raises:
            TradingSystemError: If decision making fails
        """
        logger.info("Analyzing market...")
        try:
            # Get market data
            market_data = await self.rh_client.get_market_data()
            portfolio = await self.rh_client.get_portfolio()
            
            # Prepare data for strategies
            strategy_data = {
                "market_data": market_data,
                "portfolio": portfolio
            }
            
            # Get historical data for technical analysis
            for symbol in portfolio.get("positions", {}).keys():
                historical_data = await self.rh_client.get_historical_data(symbol)
                if historical_data:
                    strategy_data[symbol] = historical_data
            
            # Add watchlist symbols
            watchlist = await self.rh_client.get_watchlist()
            for symbol in watchlist:
                if symbol not in strategy_data:
                    historical_data = await self.rh_client.get_historical_data(symbol)
                    if historical_data:
                        strategy_data[symbol] = historical_data
            
            # Generate signals using strategy registry
            signals = self.strategy_registry.get_combined_signals(strategy_data)
            
            # Update metrics
            self.metrics['decisions_made'] += len(signals)
            self.metrics['last_decision_time'] = datetime.now(timezone.utc)
            logger.debug(f"Generated {len(signals)} trading signals")
            
            return signals
            
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Decision making failed: {str(e)}")
            if not self.demo_mode:
                raise TradingSystemError(f"Decision making failed: {str(e)}")
            return {}
            
    async def _execute_trades(self, signals: Dict[str, Signal]):
        """Execute trading signals with risk management
        
        Args:
            signals: Dictionary of trading signals by symbol
            
        Raises:
            RobinhoodAPIError: If API calls fail
            TradingSystemError: For other execution errors
        """
        if not signals:
            logger.info("No trading signals to execute")
            return
             
        try:
            # Get account info with retry logic
            account_info = await self.rh_client.get_account_info()
            if not account_info:
                error_msg = "Cannot execute trades - failed to get account info"
                logger.error(error_msg)
                raise TradingSystemError(error_msg)
            
            # Get portfolio data for risk management
            portfolio = await self.rh_client.get_portfolio()
            portfolio_value = account_info.get('portfolio_value', 0.0)
            cash_balance = account_info.get('cash', 0.0)
            
            # Update risk manager with current portfolio
            portfolio_data = {
                "portfolio_value": portfolio_value,
                "cash": cash_balance,
                "positions": portfolio.get("positions", {})
            }
            self.risk_manager.update_portfolio(portfolio_data)
            
            # Get market data for volatility calculation
            market_data = {}
            for symbol in signals.keys():
                historical_data = await self.rh_client.get_historical_data(symbol)
                if historical_data:
                    market_data[symbol] = {
                        "historical_prices": [bar["close"] for bar in historical_data if "close" in bar],
                        "sector": portfolio.get("positions", {}).get(symbol, {}).get("sector", "Unknown")
                    }
            
            # Execute each trade decision
            executed_trades = []
            for symbol, signal in signals.items():
                try:
                    # Get current price
                    quote = await self.rh_client.get_quote(symbol)
                    if not quote or "last_price" not in quote:
                        logger.error(f"Failed to get quote for {symbol}")
                        continue
                    
                    price = float(quote["last_price"])
                    
                    # Calculate volatility
                    volatility = self.risk_manager.calculate_volatility(symbol, market_data)
                    
                    # Calculate position size
                    position_sizing = self.risk_manager.calculate_position_size(
                        signal, price, volatility, market_data
                    )
                    
                    # Validate trade against risk parameters
                    valid, reason = self.risk_manager.validate_trade(
                        signal, position_sizing, market_data
                    )
                    
                    if not valid:
                        logger.info(f"Trade rejected for {symbol}: {reason}")
                        continue
                    
                    # Update the strategy executor with the current account balance
                    self.strategy_executor.account_balance = portfolio_value
                    
                    # Update market conditions for adaptive anti-gaming
                    volatility = self.risk_manager.calculate_volatility(symbol, market_data)
                    volume = 1.0  # Default value, should be calculated from market data if available
                    self.anti_gaming.update_market_conditions(volatility, volume)
                    
                    # Execute based on signal type with anti-gaming protection
                    if signal.is_buy:
                        # Create signal object for strategy executor
                        execution_signal = Signal()
                        execution_signal.symbol = symbol
                        execution_signal.action = "buy"
                        execution_signal.quantity = position_sizing.quantity
                        execution_signal.price = price
                        execution_signal.confidence = signal.confidence
                        
                        # Execute with anti-gaming protection
                        result = await self.anti_gaming.execute_with_protection(
                            symbol=symbol,
                            side="buy",
                            size=position_sizing.quantity,
                            price=price,
                            exchange_api=self.rh_client,
                            execution_strategy="auto"  # Let the system choose the best strategy
                        )
                        
                        self._log_trade("BUY", symbol, signal, position_sizing, result)
                        
                        # Record trade for feedback loop
                        trade_record = {
                            "symbol": symbol,
                            "action": "buy",
                            "quantity": position_sizing.quantity,
                            "price": price,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "confidence": signal.confidence,
                            "strategy": result.get("strategy", "simple"),
                            "result": "success" if result.get("success", False) else "failed"
                        }
                        executed_trades.append(trade_record)
                        
                    elif signal.is_sell:
                        # Create signal object for strategy executor
                        execution_signal = Signal()
                        execution_signal.symbol = symbol
                        execution_signal.action = "sell"
                        execution_signal.quantity = position_sizing.quantity
                        execution_signal.price = price
                        execution_signal.confidence = signal.confidence
                        
                        # Execute with anti-gaming protection
                        result = await self.anti_gaming.execute_with_protection(
                            symbol=symbol,
                            side="sell",
                            size=position_sizing.quantity,
                            price=price,
                            exchange_api=self.rh_client,
                            execution_strategy="auto"  # Let the system choose the best strategy
                        )
                        
                        self._log_trade("SELL", symbol, signal, position_sizing, result)
                        
                        # Record trade for feedback loop
                        trade_record = {
                            "symbol": symbol,
                            "action": "sell",
                            "quantity": position_sizing.quantity,
                            "price": price,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "confidence": signal.confidence,
                            "strategy": result.get("strategy", "simple"),
                            "result": "success" if result.get("success", False) else "failed"
                        }
                        
                    else:
                        logger.info(f"No action taken for {symbol} (signal: HOLD)")
                        continue
                    
                    # Update metrics
                    self.trade_count += 1
                    self.metrics['trades_executed'] += 1
                    self.last_trade_time = datetime.now(timezone.utc)
                    
                    # Add delay between trades to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except RobinhoodAPIError as e:
                    self.metrics['errors'] += 1
                    logger.error(f"Robinhood API error for {symbol}: {e.message}")
                    if not self.demo_mode:
                        raise
                except Exception as e:
                    self.metrics['errors'] += 1
                    logger.error(f"Trade execution failed for {symbol}: {str(e)}")
                    if not self.demo_mode:
                        raise TradingSystemError(f"Trade execution failed: {str(e)}")
            
            # Update trade history
            self.trade_history.extend(executed_trades)
            
            # Provide feedback to AI engine
            if executed_trades:
                self.ai_engine.feedback_loop(executed_trades)
                
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Trade execution batch failed: {str(e)}")
            if not self.demo_mode:
                raise

    def _log_trade(self, action: str, symbol: str, signal: Signal, position_sizing: PositionSizing, result: Any):
        """Log trade details with risk information"""
        logger.info(
            f"{action} {symbol} | "
            f"Qty: {position_sizing.quantity:.4f} | "
            f"Price: ${result.get('price', 0):.2f} | "
            f"Value: ${position_sizing.notional_value:.2f} | "
            f"Confidence: {signal.confidence:.2f} | "
            f"Risk: {position_sizing.risk_contribution:.2%} | "
            f"Strategy: {result.get('strategy', 'simple')} | "
            f"Result: {'Success' if result.get('success', False) else 'Failed'}"
        )
        
        # Log risk management details
        logger.debug(
            f"Risk details for {symbol}: "
            f"Stop loss: ${position_sizing.stop_loss_price:.2f} | "
            f"Take profit: ${position_sizing.take_profit_price:.2f} | "
            f"Portfolio %: {position_sizing.percentage_of_portfolio:.2%}"
        )
        
        # Log signal metadata if available
        if signal.metadata and "reasoning" in signal.metadata:
            logger.debug(f"Reasoning: {signal.metadata['reasoning']}")
        
    def _setup_anti_gaming_system(self):
        """Initialize the anti-gaming system with appropriate configuration"""
        # Create anti-gaming configuration
        anti_gaming_config = AntiGamingConfig(
            # Order execution randomization
            jitter_range_ms=(50, 500),
            size_variance_pct=0.15,
            
            # Execution strategies
            use_iceberg=True,
            iceberg_chunk_pct=0.2,
            min_iceberg_chunks=3,
            max_iceberg_chunks=8,
            
            use_twap=True,
            twap_slices=5,
            twap_interval_range_sec=(30, 120),
            
            use_vwap=True,
            vwap_volume_profile=[0.08, 0.12, 0.15, 0.2, 0.15, 0.12, 0.1, 0.08],
            
            # Behavioral noise
            add_decoy_orders=True,
            decoy_order_probability=0.2,
            decoy_size_range_pct=(0.01, 0.05),
            
            cancel_modify_probability=0.15,
            
            # Exchange rotation
            exchange_rotation=True,
            exchange_weights={
                "primary": 0.6, "secondary": 0.3, "tertiary": 0.1
            },
            
            # Adaptive parameters
            adaptive_timing=True,
            market_volatility_factor=1.0,
            
            # Circuit breaker settings
            max_consecutive_failures=3,
            circuit_breaker_cooldown_sec=300,
            
            # Pattern disruption
            disrupt_time_patterns=True,
            time_pattern_variance_pct=0.3
        )
        
        # Create anti-gaming system
        self.anti_gaming = AntiGamingSystem(anti_gaming_config)
        
        logger.info("Anti-gaming system initialized with advanced protection strategies")
    
    def _display_demo_status(self):
        """Display real-time monitoring information in demo mode"""
        # Get risk report
        risk_report = self.risk_manager.get_risk_report()
        
        # Get strategy information
        strategies = self.strategy_registry.list_strategies()
        
        status = f"""
=== DEMO MODE STATUS ===
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
Session duration: {datetime.now(timezone.utc) - self.session_start}
Market open: {'YES' if is_market_open() else 'NO'}
Trades today: {self.trade_count}/{MAX_TRADES_PER_DAY}
Last trade: {self.last_trade_time.strftime('%H:%M:%S') if self.last_trade_time else 'N/A'}

Portfolio:
  - Value: ${risk_report.get('portfolio_value', 0):.2f}
  - Cash: ${risk_report.get('cash_balance', 0):.2f}
  - Positions: {len(risk_report.get('positions', {}))}

Risk Status:
  - Daily P&L: ${risk_report.get('daily_pnl', 0):.2f}
  - Max Drawdown Reached: {'YES' if risk_report.get('max_drawdown_reached', False) else 'NO'}

Strategies: {', '.join(strategies)}

Metrics:
  - Decisions made: {self.metrics['decisions_made']}
  - Trades executed: {self.metrics['trades_executed']}
  - Errors: {self.metrics['errors']}
"""
        print(status)
        logger.debug(status.strip())
        
        # Save trade history periodically
        if self.trade_history and len(self.trade_history) % 5 == 0:
            self._save_trade_history()
            
    def _save_trade_history(self):
        """Save trade history to a file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs('data/trades', exist_ok=True)
            
            # Save to file
            filename = f"trades_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
            filepath = os.path.join('data/trades', filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.trade_history, f, indent=2)
                
            logger.debug(f"Saved {len(self.trade_history)} trades to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save trade history: {str(e)}")

async def run_backtest(args):
    """Run backtesting mode"""
    from src.backtesting import BacktestEngine, BacktestParameters, load_data
    
    logger.info("Starting backtest mode")

    import asyncio
    import concurrent.futures

    # Create a process pool for CPU-bound parallel backtests
    executor = concurrent.futures.ProcessPoolExecutor()

    async def run_parallel_backtests(param_sets, engine_factory):
        loop = asyncio.get_event_loop()
        tasks = []
        for params in param_sets:
            task = loop.run_in_executor(
                executor,
                lambda p=params: engine_factory(p).run()
            )
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        return results

    # Example usage:
    # param_sets = [BacktestParameters(...), ...]
    # results = await run_parallel_backtests(param_sets, lambda p: BacktestEngine(registry, p))

    
    # Create strategy registry
    registry = StrategyRegistry()
    
    # Register strategies based on args
    if args.strategies:
        strategies = args.strategies.split(',')
        for strategy in strategies:
            if strategy == 'ma_cross':
                ma_cross = MovingAverageCrossStrategy()
                registry.register(ma_cross)
            elif strategy == 'rsi':
                rsi = RSIStrategy()
                registry.register(rsi)
            elif strategy == 'ai':
                ai = AITradingStrategy()
                registry.register(ai)
    else:
        # Default strategies
        ma_cross = MovingAverageCrossStrategy()
        registry.register(ma_cross)
        rsi = RSIStrategy()
        registry.register(rsi)
    
    # Create backtest parameters
    params = BacktestParameters(
        initial_capital=args.capital,
        start_date=datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else None,
        end_date=datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else None
    )
    
    # Create risk parameters
    risk_params = RiskParameters(
        max_position_size=args.max_position,
        max_portfolio_risk=args.max_risk
    )
    
    # Create backtest engine
    engine = BacktestEngine(registry, params, risk_params)
    
    # Load data
    data = load_data(args.data_dir, args.symbols.split(',') if args.symbols else None)
    
    if not data:
        logger.error("No data loaded for backtest")
        return
    
    # Run backtest
    results = engine.run(data)
    
    # Save results
    os.makedirs('results', exist_ok=True)
    results_file = f"results/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results.save_results(results_file)
    
    # Plot equity curve
    plot_file = f"results/equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    results.plot_equity_curve(plot_file)
    
    # Display summary
    print("\n=== BACKTEST RESULTS ===")
    for metric, value in results.metrics.items():
        if isinstance(value, float):
            if metric.endswith('_rate') or metric.endswith('_return') or metric.endswith('_drawdown'):
                print(f"{metric}: {value:.2%}")
            else:
                print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")
    
    print(f"\nResults saved to {results_file}")
    print(f"Equity curve saved to {plot_file}")

async def main():
    """Entry point for trading bot
    
    Parses command line arguments and initializes the trading bot
    """
    parser = argparse.ArgumentParser(description="Robinhood AI Trading Bot")
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--demo-mode', action='store_true', help='Run in demo/testing mode')
    mode_group.add_argument('--backtest', action='store_true', help='Run in backtest mode')
    
    # Common parameters
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Set logging level')
    parser.add_argument('--max-trades', type=int, help='Override maximum trades per day')
    
    # Backtest parameters
    parser.add_argument('--data-dir', default='data/historical', help='Directory with historical data for backtesting')
    parser.add_argument('--start-date', help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=100000.0, help='Initial capital for backtest')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to backtest')
    parser.add_argument('--strategies', help='Comma-separated list of strategies to use')
    parser.add_argument('--max-position', type=float, default=0.05, help='Maximum position size as fraction of portfolio')
    parser.add_argument('--max-risk', type=float, default=0.02, help='Maximum portfolio risk per day')
    
    args = parser.parse_args()
    
    # Configure logging based on arguments
    if args.log_level:
        logger.setLevel(args.log_level)
        
    # Override config if specified
    if args.max_trades:
        global MAX_TRADES_PER_DAY
        MAX_TRADES_PER_DAY = args.max_trades
        logger.info(f"Maximum trades per day set to {MAX_TRADES_PER_DAY}")
    
    try:
        if args.backtest:
            await run_backtest(args)
        else:
            bot = TradingBot(demo_mode=args.demo_mode)
            await bot.run()
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
