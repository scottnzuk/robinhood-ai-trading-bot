import time
import asyncio
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from src.exceptions import CircuitTrippedError

@dataclass
class BreakerConfig:
    """Configuration for a circuit breaker
    
    Attributes:
        failure_threshold: Number of failures before tripping
        success_threshold: Number of successes needed to reset
        timeout_seconds: How long the circuit stays open
        failure_window: Time window for counting failures
        half_open_max_calls: Maximum calls allowed in half-open state
    """
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 300
    failure_window: int = 60
    half_open_max_calls: int = 1

@dataclass
class BreakerState:
    """State of a circuit breaker
    
    Attributes:
        failures: Count of recent failures
        successes: Count of recent successes
        tripped: Whether the circuit is currently open
        last_trip: Timestamp of last trip
        failure_timestamps: List of recent failure timestamps
        active_calls: Count of in-progress calls
    """
    failures: int = 0
    successes: int = 0
    tripped: bool = False
    last_trip: Optional[float] = None
    failure_timestamps: List[float] = field(default_factory=list)
    active_calls: int = 0

class CircuitBreakerService:
    """Service for managing multiple circuit breakers
    
    This service implements the circuit breaker pattern to prevent
    cascading failures when external services are unavailable.
    """
    def __init__(self):
        self._breakers: Dict[str, BreakerState] = {}
        self._configs: Dict[str, BreakerConfig] = {}
        self._lock = asyncio.Lock()

    async def register_endpoint(self, endpoint: str, config: Optional[BreakerConfig] = None):
        """Register an endpoint with the circuit breaker service
        
        Args:
            endpoint: Name of the endpoint/service to monitor
            config: Configuration for this breaker, or None for defaults
        """
        async with self._lock:
            self._configs[endpoint] = config or BreakerConfig()
            self._breakers[endpoint] = BreakerState()

    async def check(self, endpoint: str) -> bool:
        """Check if circuit is tripped for endpoint
        
        Args:
            endpoint: The endpoint to check
            
        Returns:
            True if circuit is open (tripped), False otherwise
        """
        async with self._lock:
            # Auto-register unknown endpoints with default config
            if endpoint not in self._breakers:
                await self.register_endpoint(endpoint)
                return False
                
            breaker = self._breakers[endpoint]
            config = self._configs[endpoint]
            
            # Circuit is closed - allow calls
            if not breaker.tripped:
                return False
                
            # Check if timeout has elapsed - transition to half-open
            current_time = time.time()
            if current_time - breaker.last_trip > config.timeout_seconds:
                # Reset to half-open state
                breaker.tripped = False
                breaker.failures = 0
                breaker.successes = 0
                return False
                
            # Circuit is open - block calls
            return True

    async def record_failure(self, endpoint: str):
        """Record a failed call
        
        Args:
            endpoint: The endpoint that failed
            
        Raises:
            CircuitTrippedError: If this failure trips the circuit
        """
        async with self._lock:
            # Auto-register unknown endpoints
            if endpoint not in self._breakers:
                await self.register_endpoint(endpoint)
                
            breaker = self._breakers[endpoint]
            config = self._configs[endpoint]
            
            # Record failure
            current_time = time.time()
            breaker.failures += 1
            breaker.successes = 0
            breaker.failure_timestamps.append(current_time)
            
            # Prune old failures outside the window
            window_start = current_time - config.failure_window
            breaker.failure_timestamps = [t for t in breaker.failure_timestamps if t >= window_start]
            
            # Check recent failure rate within window
            recent_failures = len(breaker.failure_timestamps)
            
            # Trip the circuit if threshold reached
            if (recent_failures >= config.failure_threshold and not breaker.tripped):
                breaker.tripped = True
                breaker.last_trip = current_time
                raise CircuitTrippedError(f"Circuit tripped for {endpoint} after {recent_failures} failures")

    async def record_success(self, endpoint: str):
        """Record a successful call
        
        Args:
            endpoint: The endpoint that succeeded
        """
        async with self._lock:
            # Auto-register unknown endpoints
            if endpoint not in self._breakers:
                await self.register_endpoint(endpoint)
                return
                
            breaker = self._breakers[endpoint]
            config = self._configs[endpoint]
            
            # Update counters
            breaker.successes += 1
            breaker.failures = 0
            
            # Clear failure history
            breaker.failure_timestamps = []
            
            # Reset circuit if enough consecutive successes
            if (breaker.successes >= config.success_threshold and breaker.tripped):
                await self.reset(endpoint)

    async def reset(self, endpoint: str):
        """Reset circuit for endpoint
        
        Args:
            endpoint: The endpoint to reset
        """
        async with self._lock:
            if endpoint in self._breakers:
                self._breakers[endpoint] = BreakerState()
                
    async def execute(self, endpoint: str, func, *args, **kwargs):
        """Execute a function with circuit breaker protection
        
        Args:
            endpoint: The endpoint/service being called
            func: Async function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function call
            
        Raises:
            CircuitTrippedError: If the circuit is open
            Any exceptions raised by the function
        """
        # Check if circuit is open
        if await self.check(endpoint):
            raise CircuitTrippedError(f"Circuit open for {endpoint}")
            
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            # Record success
            await self.record_success(endpoint)
            return result
        except Exception as e:
            # Record failure
            await self.record_failure(endpoint)
            raise
            
    def is_active(self, endpoint: str = "global") -> bool:
        """Check if a circuit breaker is active (synchronous version)
        
        Args:
            endpoint: The endpoint to check, defaults to "global"
            
        Returns:
            True if the circuit is open, False otherwise
        """
        if endpoint not in self._breakers:
            return False
            
        breaker = self._breakers[endpoint]
        if not breaker.tripped:
            return False
            
        # Check if timeout has elapsed
        if breaker.last_trip and time.time() - breaker.last_trip > self._configs[endpoint].timeout_seconds:
            return False
            
        return True
        
    def trip(self, endpoint: str = "global", duration_seconds: int = 300):
        """Manually trip a circuit breaker (synchronous version)
        
        Args:
            endpoint: The endpoint to trip, defaults to "global"
            duration_seconds: How long to keep the circuit open
        """
        # Auto-register if needed
        if endpoint not in self._breakers:
            self._breakers[endpoint] = BreakerState()
            self._configs[endpoint] = BreakerConfig(timeout_seconds=duration_seconds)
            
        # Trip the circuit
        self._breakers[endpoint].tripped = True
        self._breakers[endpoint].last_trip = time.time()


# Simplified CircuitBreaker class for use in main.py
class CircuitBreaker:
    """Simplified circuit breaker for global application use"""
    def __init__(self):
        self._service = CircuitBreakerService()
        self._global_endpoint = "global"
        
    def is_active(self) -> bool:
        """Check if the global circuit breaker is active"""
        return self._service.is_active(self._global_endpoint)
        
    def trip(self, duration_seconds: int = 300):
        """Trip the global circuit breaker"""
        self._service.trip(self._global_endpoint, duration_seconds)
        
    async def execute(self, func, *args, **kwargs):
        """Execute a function with circuit breaker protection"""
        return await self._service.execute(self._global_endpoint, func, *args, **kwargs)