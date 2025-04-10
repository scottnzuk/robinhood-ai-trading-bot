import asyncio
import random
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from src.databus import AsyncioQueueBus
from src.features_pb2 import Signal
from src.anti_gaming import AntiGamingSystem, AntiGamingConfig

logger = logging.getLogger(__name__)

@dataclass
class ExecutionState:
    recent_fills: List[float] = field(default_factory=list)
    recent_rejects: List[float] = field(default_factory=list)
    recent_latency: List[float] = field(default_factory=list)
    breaker_state: Dict = field(default_factory=lambda: {
        "symbol": {},
        "exchange": {},
        "global": {"paused": False, "until": 0}
    })

class StrategyExecutor:
    def __init__(self, account_balance: float, risk_per_trade: float = 0.01, exchange_api: Optional[Any] = None):
        self.bus = AsyncioQueueBus()
        self.state = ExecutionState()
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self._lock = asyncio.Lock()
        self.exchange_api = exchange_api or MockExchangeAPI()
        
        # Initialize anti-gaming system with default configuration
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
            
            # Behavioral noise
            add_decoy_orders=True,
            decoy_order_probability=0.2,
            
            # Circuit breaker settings
            max_consecutive_failures=3,
            circuit_breaker_cooldown_sec=300
        )
        self.anti_gaming = AntiGamingSystem(anti_gaming_config)

    async def risk_check(self, signal: Signal) -> bool:
        """Comprehensive risk assessment"""
        if signal.confidence < 0.5:
            return False
            
        # Position sizing based on account risk
        max_position_size = self.account_balance * self.risk_per_trade
        if signal.quantity > max_position_size:
            return False
            
        # TODO: Add more risk rules (volatility, correlation, etc.)
        return True

    async def execute_order(self, signal: Signal):
        """Improved order execution with proper state management and anti-gaming protection"""
        async with self._lock:
            now = datetime.utcnow().timestamp()
            
            if self._is_paused("global"):
                logger.warning(f"GLOBAL PAUSE active. Skipping order for {signal.symbol}.")
                return
                
            if not await self.risk_check(signal):
                logger.info(f"Risk check failed for {signal.symbol}")
                return

            try:
                # Execute order with anti-gaming protection
                await self._execute_with_anti_gaming(signal)
                
            except Exception as e:
                logger.error(f"Order execution failed for {signal.symbol}: {str(e)}")
                await self._handle_failure(signal)

    async def _execute_with_anti_gaming(self, signal: Signal):
        """Execute order with anti-gaming protection"""
        # Calculate position size based on risk
        base_size = self.account_balance * self.risk_per_trade
        size = min(base_size, signal.quantity) if hasattr(signal, 'quantity') else base_size
        
        # Determine price
        price = signal.price if hasattr(signal, 'price') else 0.0
        
        # Determine side
        side = signal.action.lower() if hasattr(signal, 'action') else 'buy'
        
        # Update market conditions for adaptive anti-gaming
        volatility = 1.0  # Default value, should be calculated from market data
        volume = 1.0      # Default value, should be calculated from market data
        self.anti_gaming.update_market_conditions(volatility, volume)
        
        # Execute with anti-gaming protection
        logger.info(f"Executing {side} order for {signal.symbol} with anti-gaming protection")
        result = await self.anti_gaming.execute_with_protection(
            symbol=signal.symbol,
            side=side,
            size=size,
            price=price,
            exchange_api=self.exchange_api,
            execution_strategy="auto"  # Let the system choose the best strategy
        )
        
        # Handle result
        if result["success"]:
            logger.info(f"Order executed successfully: {result['filled_size']} {signal.symbol} using {result['strategy']} strategy")
            # Update state
            async with self._lock:
                self.state.recent_fills.append(1.0)  # Success
        else:
            logger.warning(f"Order execution failed: {result.get('reason', 'unknown error')}")
            raise Exception(result.get('reason', 'Execution failed'))

    def _is_paused(self, level: str, key: Optional[str] = None) -> bool:
        """Thread-safe circuit breaker check"""
        if level == "global":
            return (self.state.breaker_state["global"]["paused"] and 
                    datetime.utcnow().timestamp() < self.state.breaker_state["global"]["until"])
        elif level in ["symbol", "exchange"] and key:
            state = self.state.breaker_state[level].get(key, {"paused": False, "until": 0})
            return state["paused"] and datetime.utcnow().timestamp() < state["until"]
        return False

    async def _handle_failure(self, signal: Signal):
        """Handle order execution failures"""
        async with self._lock:
            self.state.recent_rejects.append(1.0)
            
            # Trip circuit breaker if failure rate is high
            if len(self.state.recent_rejects) > 10:
                failure_rate = sum(self.state.recent_rejects[-10:]) / 10
                if failure_rate > 0.2:
                    self._trip_breaker("global", None, 120)

    def _trip_breaker(self, level: str, key: Optional[str], duration: int):
        """Trip circuit breaker"""
        now = datetime.utcnow().timestamp()
        print(f"Tripping {level} circuit breaker for {duration} seconds")
        
        if level not in self.state.breaker_state:
            self.state.breaker_state[level] = {}
            
        if key:
            self.state.breaker_state[level][key] = {"paused": True, "until": now + duration}
        else:
            self.state.breaker_state[level] = {"paused": True, "until": now + duration}

# Mock Exchange API for testing
class MockExchangeAPI:
    """Mock exchange API for testing"""
    
    async def place_order(self, symbol: str, side: str, size: float, price: float, **kwargs) -> Dict[str, Any]:
        """Mock order placement"""
        order_id = f"order-{random.randint(1000, 9999)}"
        logger.info(f"[MOCK] Placed {side} order for {size} {symbol} @ {price}")
        return {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "size": size,
            "price": price,
            "status": "filled",
            "filled": size
        }
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Mock order cancellation"""
        logger.info(f"[MOCK] Cancelled order {order_id}")
        return {"id": order_id, "status": "cancelled"}

async def strategy_worker():
    """Main strategy execution loop"""
    executor = StrategyExecutor(account_balance=10000.0)  # Example balance
    async for msg_bytes in executor.bus.subscribe("signals"):
        signal = Signal()
        signal.ParseFromString(msg_bytes)
        await executor.execute_order(signal)

if __name__ == "__main__":
    asyncio.run(strategy_worker())