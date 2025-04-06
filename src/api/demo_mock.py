import logging
from datetime import datetime
from typing import Dict, Any

class MockRobinhoodClient:
    def __init__(self):
        self.demo_mode = True
        self.logger = logging.getLogger(__name__)
        
    async def authenticate(self) -> bool:
        """Mock authentication that always succeeds"""
        self.logger.info("Demo mode - mock authentication successful")
        return True
        
    async def get_account_info(self) -> Dict[str, Any]:
        """Return mock account information"""
        return {
            'buying_power': 10000.00,
            'cash': 5000.00,
            'portfolio_value': 15000.00,
            'equity': 15000.00,
            'last_updated': datetime.now().isoformat()
        }
        
    async def buy_stock(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Mock buy operation"""
        return {
            'status': 'filled',
            'symbol': symbol,
            'quantity': quantity,
            'average_price': 100.00,
            'executed_at': datetime.now().isoformat()
        }
        
    async def sell_stock(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Mock sell operation"""
        return {
            'status': 'filled',
            'symbol': symbol,
            'quantity': quantity,
            'average_price': 100.00,
            'executed_at': datetime.now().isoformat()
        }
