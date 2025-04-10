"""
Advanced anti-gaming system for trading operations.

This module provides comprehensive protection against order detection, pattern recognition,
front-running, and other adversarial tactics used by market participants.
"""
import asyncio
import random
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import logging
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class AntiGamingConfig:
    """Configuration for anti-gaming strategies"""
    # Order execution randomization
    jitter_range_ms: Tuple[int, int] = (50, 500)  # Timing jitter range in milliseconds
    size_variance_pct: float = 0.15  # Random variance in order size (±%)
    
    # Iceberg/TWAP/VWAP settings
    use_iceberg: bool = True
    iceberg_chunk_pct: float = 0.2  # Chunk size as percentage of total order
    min_iceberg_chunks: int = 3
    max_iceberg_chunks: int = 8
    
    use_twap: bool = True
    twap_slices: int = 5
    twap_interval_range_sec: Tuple[int, int] = (30, 120)
    
    use_vwap: bool = True
    vwap_volume_profile: List[float] = field(default_factory=lambda: [0.08, 0.12, 0.15, 0.2, 0.15, 0.12, 0.1, 0.08])
    
    # Behavioral noise
    add_decoy_orders: bool = True
    decoy_order_probability: float = 0.2
    decoy_size_range_pct: Tuple[float, float] = (0.01, 0.05)
    
    cancel_modify_probability: float = 0.15
    
    # Exchange-specific tactics
    exchange_rotation: bool = True
    exchange_weights: Dict[str, float] = field(default_factory=lambda: {
        "primary": 0.6, "secondary": 0.3, "tertiary": 0.1
    })
    
    # Adaptive parameters
    adaptive_timing: bool = True
    market_volatility_factor: float = 1.0  # Adjusts timing based on volatility
    
    # Circuit breaker settings
    max_consecutive_failures: int = 3
    circuit_breaker_cooldown_sec: int = 300
    
    # Pattern disruption
    disrupt_time_patterns: bool = True
    time_pattern_variance_pct: float = 0.3


class AntiGamingSystem:
    """
    Advanced anti-gaming system with multiple protection strategies.
    
    Features:
    - Order execution randomization (timing, size)
    - Iceberg/TWAP/VWAP execution strategies
    - Behavioral noise (decoy orders, cancellations)
    - Exchange rotation and routing optimization
    - Adaptive parameter adjustment based on market conditions
    - Circuit breaker protection
    - Pattern disruption
    """
    
    def __init__(self, config: Optional[AntiGamingConfig] = None):
        """
        Initialize the anti-gaming system.
        
        Args:
            config: Configuration for anti-gaming strategies
        """
        self.config = config or AntiGamingConfig()
        self._lock = Lock()
        self._failure_counters = {}
        self._circuit_breakers = {}
        self._last_execution_times = {}
        self._execution_patterns = {}
        self._market_conditions = {"volatility": 1.0, "volume": 1.0}
    
    def update_market_conditions(self, volatility: float, volume: float):
        """
        Update market condition factors used for adaptive strategies.
        
        Args:
            volatility: Current market volatility (normalized, 1.0 = average)
            volume: Current market volume (normalized, 1.0 = average)
        """
        with self._lock:
            self._market_conditions["volatility"] = max(0.1, min(5.0, volatility))
            self._market_conditions["volume"] = max(0.1, min(5.0, volume))
    
    async def execute_with_protection(
        self, 
        symbol: str, 
        side: str, 
        size: float, 
        price: float,
        exchange_api: Any,
        execution_strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        Execute an order with anti-gaming protection.
        
        Args:
            symbol: Trading symbol
            side: Order side ("buy" or "sell")
            size: Order size
            price: Order price
            exchange_api: Exchange API client
            execution_strategy: Strategy to use ("auto", "iceberg", "twap", "vwap", "simple")
            
        Returns:
            Dictionary with execution results
        """
        # Check circuit breaker
        if self._is_circuit_tripped(symbol):
            logger.warning(f"Circuit breaker active for {symbol}, skipping execution")
            return {"success": False, "reason": "circuit_breaker"}
        
        # Apply timing jitter
        await self._apply_timing_jitter()
        
        # Apply size variance
        adjusted_size = self._apply_size_variance(size)
        
        # Select execution strategy
        if execution_strategy == "auto":
            execution_strategy = self._select_execution_strategy(symbol, adjusted_size)
        
        # Execute with selected strategy
        try:
            if execution_strategy == "iceberg":
                result = await self._execute_iceberg(symbol, side, adjusted_size, price, exchange_api)
            elif execution_strategy == "twap":
                result = await self._execute_twap(symbol, side, adjusted_size, price, exchange_api)
            elif execution_strategy == "vwap":
                result = await self._execute_vwap(symbol, side, adjusted_size, price, exchange_api)
            else:  # "simple"
                result = await self._execute_simple(symbol, side, adjusted_size, price, exchange_api)
            
            # Add decoy orders if configured
            if self.config.add_decoy_orders and random.random() < self.config.decoy_order_probability:
                await self._place_decoy_orders(symbol, side, size, price, exchange_api)
            
            # Reset failure counter on success
            self._reset_failure_counter(symbol)
            
            # Record execution time for pattern analysis
            self._record_execution_time(symbol)
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error for {symbol}: {str(e)}")
            self._increment_failure_counter(symbol)
            return {"success": False, "reason": str(e)}
    
    async def _apply_timing_jitter(self):
        """Apply random timing jitter to disrupt execution patterns"""
        jitter_ms = random.randint(*self.config.jitter_range_ms)
        
        # Adjust jitter based on market volatility if adaptive timing is enabled
        if self.config.adaptive_timing:
            volatility_factor = self._market_conditions["volatility"]
            jitter_ms = int(jitter_ms * (1.0 / volatility_factor))
        
        # Ensure minimum jitter
        jitter_ms = max(10, jitter_ms)
        
        await asyncio.sleep(jitter_ms / 1000.0)
    
    def _apply_size_variance(self, size: float) -> float:
        """Apply random variance to order size"""
        variance_factor = 1.0 + random.uniform(-self.config.size_variance_pct, self.config.size_variance_pct)
        return size * variance_factor
    
    def _select_execution_strategy(self, symbol: str, size: float) -> str:
        """
        Dynamically select the best execution strategy based on order characteristics and market conditions.
        
        This helps prevent predictable execution patterns.
        """
        strategies = []
        
        # Add eligible strategies based on configuration
        if self.config.use_iceberg:
            strategies.append(("iceberg", 0))
        if self.config.use_twap:
            strategies.append(("twap", 0))
        if self.config.use_vwap:
            strategies.append(("vwap", 0))
        
        # Always include simple execution as fallback
        strategies.append(("simple", 0))
        
        # Weight strategies based on order size and market conditions
        for i, (strategy, _) in enumerate(strategies):
            weight = 1.0  # Base weight
            
            if strategy == "iceberg":
                # Favor iceberg for larger orders in high volume
                if size > 0.1:  # Large order
                    weight += 2.0
                weight *= self._market_conditions["volume"]
                
            elif strategy == "twap":
                # Favor TWAP for medium orders in normal conditions
                if 0.05 <= size <= 0.2:  # Medium order
                    weight += 1.5
                
            elif strategy == "vwap":
                # Favor VWAP for larger orders in high volatility
                if size > 0.1:  # Large order
                    weight += 1.0
                weight *= self._market_conditions["volatility"]
                
            elif strategy == "simple":
                # Favor simple for small orders in low volatility
                if size < 0.05:  # Small order
                    weight += 2.0
                weight *= (1.0 / self._market_conditions["volatility"])
            
            # Add randomness to prevent predictability
            weight *= random.uniform(0.8, 1.2)
            
            strategies[i] = (strategy, weight)
        
        # Select strategy based on weights
        total_weight = sum(weight for _, weight in strategies)
        if total_weight <= 0:
            return "simple"  # Fallback
            
        # Normalize weights
        strategies = [(s, w/total_weight) for s, w in strategies]
        
        # Cumulative distribution
        cumulative = 0
        rand_val = random.random()
        for strategy, weight in strategies:
            cumulative += weight
            if rand_val <= cumulative:
                return strategy
        
        return "simple"  # Fallback
    
    async def _execute_iceberg(
        self, 
        symbol: str, 
        side: str, 
        size: float, 
        price: float,
        exchange_api: Any
    ) -> Dict[str, Any]:
        """Execute an order using iceberg strategy (split into smaller chunks)"""
        total_filled = 0
        chunk_pct = self.config.iceberg_chunk_pct
        
        # Randomize number of chunks for unpredictability
        num_chunks = random.randint(self.config.min_iceberg_chunks, self.config.max_iceberg_chunks)
        chunk_size = size / num_chunks
        
        results = []
        
        for i in range(num_chunks):
            # Last chunk handles any rounding errors
            if i == num_chunks - 1:
                current_chunk = size - total_filled
            else:
                # Add variance to chunk size
                variance = random.uniform(-0.1, 0.1)
                current_chunk = chunk_size * (1 + variance)
                current_chunk = min(current_chunk, size - total_filled)
            
            # Skip if chunk too small
            if current_chunk <= 0:
                continue
                
            try:
                # Execute chunk
                result = await exchange_api.place_order(symbol, side, current_chunk, price)
                results.append(result)
                total_filled += current_chunk
                
                # Random delay between chunks
                delay_sec = random.uniform(0.5, 3.0) * self._market_conditions["volatility"]
                await asyncio.sleep(delay_sec)
                
            except Exception as e:
                logger.error(f"Iceberg chunk execution error: {str(e)}")
                # Continue with next chunk
        
        return {
            "success": total_filled > 0,
            "filled_size": total_filled,
            "strategy": "iceberg",
            "results": results
        }
    
    async def _execute_twap(
        self, 
        symbol: str, 
        side: str, 
        size: float, 
        price: float,
        exchange_api: Any
    ) -> Dict[str, Any]:
        """Execute an order using TWAP strategy (time-weighted average price)"""
        slices = self.config.twap_slices
        slice_size = size / slices
        
        # Calculate time intervals with randomization
        min_interval, max_interval = self.config.twap_interval_range_sec
        intervals = []
        
        for _ in range(slices):
            interval = random.uniform(min_interval, max_interval)
            # Adjust interval based on volatility
            interval = interval / self._market_conditions["volatility"]
            intervals.append(max(1.0, interval))
        
        results = []
        total_filled = 0
        
        for i in range(slices):
            # Last slice handles any rounding errors
            if i == slices - 1:
                current_slice = size - total_filled
            else:
                # Add variance to slice size
                variance = random.uniform(-0.1, 0.1)
                current_slice = slice_size * (1 + variance)
                current_slice = min(current_slice, size - total_filled)
            
            # Skip if slice too small
            if current_slice <= 0:
                continue
                
            try:
                # Execute slice
                result = await exchange_api.place_order(symbol, side, current_slice, price)
                results.append(result)
                total_filled += current_slice
                
                # Wait for next interval if not last slice
                if i < slices - 1:
                    await asyncio.sleep(intervals[i])
                
            except Exception as e:
                logger.error(f"TWAP slice execution error: {str(e)}")
                # Continue with next slice
        
        return {
            "success": total_filled > 0,
            "filled_size": total_filled,
            "strategy": "twap",
            "results": results
        }
    
    async def _execute_vwap(
        self, 
        symbol: str, 
        side: str, 
        size: float, 
        price: float,
        exchange_api: Any
    ) -> Dict[str, Any]:
        """Execute an order using VWAP strategy (volume-weighted average price)"""
        # Use volume profile to distribute order
        volume_profile = self.config.vwap_volume_profile
        
        results = []
        total_filled = 0
        
        for i, volume_pct in enumerate(volume_profile):
            slice_size = size * volume_pct
            
            # Add variance to slice size
            variance = random.uniform(-0.1, 0.1)
            slice_size = slice_size * (1 + variance)
            
            # Ensure we don't exceed total size
            slice_size = min(slice_size, size - total_filled)
            
            # Skip if slice too small
            if slice_size <= 0:
                continue
                
            try:
                # Execute slice
                result = await exchange_api.place_order(symbol, side, slice_size, price)
                results.append(result)
                total_filled += slice_size
                
                # Wait between slices with randomized interval
                if i < len(volume_profile) - 1:
                    interval = random.uniform(30, 120) / self._market_conditions["volume"]
                    await asyncio.sleep(max(1.0, interval))
                
            except Exception as e:
                logger.error(f"VWAP slice execution error: {str(e)}")
                # Continue with next slice
        
        return {
            "success": total_filled > 0,
            "filled_size": total_filled,
            "strategy": "vwap",
            "results": results
        }
    
    async def _execute_simple(
        self, 
        symbol: str, 
        side: str, 
        size: float, 
        price: float,
        exchange_api: Any
    ) -> Dict[str, Any]:
        """Execute a simple order (single execution)"""
        try:
            result = await exchange_api.place_order(symbol, side, size, price)
            return {
                "success": True,
                "filled_size": size,
                "strategy": "simple",
                "results": [result]
            }
        except Exception as e:
            logger.error(f"Simple execution error: {str(e)}")
            return {
                "success": False,
                "filled_size": 0,
                "strategy": "simple",
                "error": str(e)
            }
    
    async def _place_decoy_orders(
        self, 
        symbol: str, 
        side: str, 
        size: float, 
        price: float,
        exchange_api: Any
    ):
        """Place decoy orders to mask true trading intent"""
        # Determine opposite side
        opposite_side = "sell" if side == "buy" else "buy"
        
        # Determine decoy size (small percentage of real order)
        min_pct, max_pct = self.config.decoy_size_range_pct
        decoy_size = size * random.uniform(min_pct, max_pct)
        
        # Determine decoy price (away from real price)
        price_offset_pct = random.uniform(0.01, 0.05)
        if opposite_side == "buy":
            decoy_price = price * (1 - price_offset_pct)  # Lower for buy
        else:
            decoy_price = price * (1 + price_offset_pct)  # Higher for sell
        
        try:
            # Place decoy order
            decoy_order = await exchange_api.place_order(
                symbol, opposite_side, decoy_size, decoy_price, 
                post_only=True  # Ensure it doesn't execute
            )
            
            # Schedule cancellation
            cancel_delay = random.uniform(5, 30)
            asyncio.create_task(self._cancel_after_delay(
                exchange_api, decoy_order, cancel_delay
            ))
            
        except Exception as e:
            logger.debug(f"Decoy order placement failed: {str(e)}")
    
    async def _cancel_after_delay(self, exchange_api: Any, order: Dict[str, Any], delay_sec: float):
        """Cancel an order after a delay"""
        await asyncio.sleep(delay_sec)
        try:
            await exchange_api.cancel_order(order["id"])
        except Exception as e:
            logger.debug(f"Decoy order cancellation failed: {str(e)}")
    
    def _increment_failure_counter(self, symbol: str):
        """Increment failure counter and trip circuit breaker if threshold reached"""
        with self._lock:
            if symbol not in self._failure_counters:
                self._failure_counters[symbol] = 0
                
            self._failure_counters[symbol] += 1
            
            if self._failure_counters[symbol] >= self.config.max_consecutive_failures:
                self._trip_circuit_breaker(symbol)
    
    def _reset_failure_counter(self, symbol: str):
        """Reset failure counter after successful execution"""
        with self._lock:
            self._failure_counters[symbol] = 0
    
    def _trip_circuit_breaker(self, symbol: str):
        """Trip circuit breaker for a symbol"""
        with self._lock:
            expiry = time.time() + self.config.circuit_breaker_cooldown_sec
            self._circuit_breakers[symbol] = expiry
            logger.warning(f"Circuit breaker tripped for {symbol} until {datetime.fromtimestamp(expiry)}")
    
    def _is_circuit_tripped(self, symbol: str) -> bool:
        """Check if circuit breaker is active for a symbol"""
        with self._lock:
            if symbol not in self._circuit_breakers:
                return False
                
            expiry = self._circuit_breakers[symbol]
            if time.time() > expiry:
                # Circuit breaker expired
                del self._circuit_breakers[symbol]
                return False
                
            return True
    
    def _record_execution_time(self, symbol: str):
        """Record execution time for pattern analysis"""
        with self._lock:
            now = time.time()
            
            if symbol not in self._last_execution_times:
                self._last_execution_times[symbol] = []
                
            # Keep last 10 execution times
            times = self._last_execution_times[symbol]
            times.append(now)
            if len(times) > 10:
                times.pop(0)
                
            # Analyze for patterns if we have enough data
            if len(times) >= 3:
                self._analyze_execution_patterns(symbol, times)
    
    def _analyze_execution_patterns(self, symbol: str, times: List[float]):
        """Analyze execution times for patterns and adjust if detected"""
        # Calculate intervals between executions
        intervals = [times[i] - times[i-1] for i in range(1, len(times))]
        
        # Check for consistent intervals (pattern)
        if len(intervals) >= 2:
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((i - avg_interval)**2 for i in intervals) / len(intervals)
            std_dev = variance**0.5
            
            # If standard deviation is low, we have a pattern
            if std_dev / avg_interval < 0.2:  # Less than 20% variation
                logger.info(f"Execution pattern detected for {symbol}, will disrupt")
                self._execution_patterns[symbol] = {
                    "avg_interval": avg_interval,
                    "detected_at": time.time()
                }
