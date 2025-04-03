import asyncio
import sys
import time
import argparse
from datetime import datetime, timedelta, UTC
from typing import Dict, Any

from src.api import RobinhoodClient, login_to_robinhood, get_account_info
from src.utils.logger import logger
from config import MODE, TRADING_INTERVAL_MINUTES, MAX_TRADES_PER_DAY
from src.api.trading_utils import is_market_open
from src.api.trading_decision import make_trading_decisions

class TradingBot:
    def __init__(self, demo_mode: bool = False):
        self.trade_count = 0
        self.last_trade_time = None
        self.session_start = datetime.now(UTC)
        self.demo_mode = demo_mode
        self.metrics = {
            'decisions_made': 0,
            'trades_executed': 0,
            'errors': 0,
            'last_decision_time': None
        }
        
    async def run(self):
        """Main trading loop"""
        logger.info(f"Starting trading bot session {'(DEMO MODE)' if self.demo_mode else ''}")
        
        self.rh_client = RobinhoodClient()
        
        if not await self.rh_client.authenticate():
            logger.error("Failed to authenticate with Robinhood")
            if self.demo_mode:
                raise Exception("Failed to authenticate with Robinhood")
            else:
                sys.exit(1)
            
        while True:
            try:
                if not self._should_run():
                    await asyncio.sleep(60)
                    continue
                    
                decisions = await self._analyze_and_decide()
                await self._execute_trades(decisions)
                
                if self.demo_mode:
                    self._display_demo_status()
                    
                await asyncio.sleep(TRADING_INTERVAL_MINUTES * 60)
                
            except Exception as e:
                self.metrics['errors'] += 1
                logger.error(f"Critical error in trading loop: {str(e)}")
                if not self.demo_mode:
                    raise
                await asyncio.sleep(10)  # Recover in demo mode

    def _should_run(self) -> bool:
        """Check if trading should continue"""
        if not is_market_open():
            logger.debug("Market closed - waiting")
            return False
            
        if self.trade_count >= MAX_TRADES_PER_DAY:
            logger.info(f"Reached daily trade limit of {MAX_TRADES_PER_DAY}")
            return False
            
        if datetime.now(UTC) > self.session_start + timedelta(hours=6):
            logger.info("Completed maximum session duration")
            return False
            
        return True
        
    async def _analyze_and_decide(self) -> Dict[str, Any]:
        """Perform market analysis and get trading decisions"""
        logger.info("Analyzing market...")
        try:
            decisions = make_trading_decisions()
            self.metrics['decisions_made'] += len(decisions)
            self.metrics['last_decision_time'] = datetime.now(UTC)
            logger.debug(f"Generated {len(decisions)} trading decisions")
            return decisions
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Decision making failed: {str(e)}")
            return {}
            
    async def _execute_trades(self, decisions: Dict[str, Any]):
        """Execute trading decisions"""
        if not decisions:
            return
             
        account_info = await self.rh_client.get_account_info()
        if not account_info:
            logger.error("Cannot execute trades - failed to get account info")
            raise Exception("Failed to get account info")
             
        for symbol, decision in decisions.items():
            try:
                if decision.decision == "buy":
                    result = await self.rh_client.buy_stock(symbol, decision.quantity)
                    self._log_trade("BUY", symbol, decision, result)
                elif decision.decision == "sell":
                    result = await self.rh_client.sell_stock(symbol, decision.quantity)
                    self._log_trade("SELL", symbol, decision, result)
                    
                self.trade_count += 1
                self.metrics['trades_executed'] += 1
                self.last_trade_time = datetime.now(UTC)
                
            except Exception as e:
                self.metrics['errors'] += 1
                logger.error(f"Trade execution failed for {symbol}: {str(e)}")
                if not self.demo_mode:
                    raise

    def _log_trade(self, action: str, symbol: str, decision: Any, result: Any):
        """Log trade details"""
        logger.info(
            f"{action} {symbol} | "
            f"Qty: {decision.quantity} | "
            f"Confidence: {decision.confidence:.2f} | "
            f"Result: {result}"
        )
        logger.debug(f"Reasoning: {decision.reasoning}")
        
    def _display_demo_status(self):
        """Display real-time monitoring information in demo mode"""
        status = f"""
=== DEMO MODE STATUS ===
Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}
Session duration: {datetime.now(UTC) - self.session_start}
Market open: {'YES' if is_market_open() else 'NO'}
Trades today: {self.trade_count}/{MAX_TRADES_PER_DAY}
Last trade: {self.last_trade_time.strftime('%H:%M:%S') if self.last_trade_time else 'N/A'}
Metrics:
  - Decisions made: {self.metrics['decisions_made']}
  - Trades executed: {self.metrics['trades_executed']}
  - Errors: {self.metrics['errors']}
"""
        print(status)
        logger.debug(status.strip())

async def main():
    """Entry point for trading bot"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo-mode', action='store_true', help='Run in demo/testing mode')
    args = parser.parse_args()
    
    bot = TradingBot(demo_mode=args.demo_mode)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
