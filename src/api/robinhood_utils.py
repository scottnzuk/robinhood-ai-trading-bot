"""
Robinhood Utility Functions

Contains core Robinhood operations extracted from robinhood.py
to break circular dependencies.
"""

from typing import List, Dict, Any
from ..utils.logger import debug, info, warning, error

def get_account_info() -> Dict[str, Any]:
    """Get account information from Robinhood"""
    from .robinhood import RobinhoodTrader
    trader = RobinhoodTrader()
    return trader.get_account_info()

def get_portfolio_stocks() -> List[Dict[str, Any]]:
    """Get current portfolio holdings"""
    from .robinhood import RobinhoodTrader
    trader = RobinhoodTrader()
    return trader.get_portfolio_stocks()

def get_watchlist_stocks(watchlist_name: str) -> List[Dict[str, Any]]:
    """Get stocks from specified watchlist"""
    from .robinhood import RobinhoodTrader
    trader = RobinhoodTrader()
    return trader.get_watchlist_stocks(watchlist_name)

def get_historical_data(symbol: str, interval: str = '5minute', span: str = 'day') -> Dict[str, Any]:
    """Get historical price data for a symbol"""
    from .robinhood import RobinhoodTrader
    trader = RobinhoodTrader()
    return trader.get_historical_data(symbol, interval, span)

def is_market_open() -> bool:
    """Check if market is currently open"""
    from .robinhood import RobinhoodTrader
    trader = RobinhoodTrader()
    return trader.is_market_open()