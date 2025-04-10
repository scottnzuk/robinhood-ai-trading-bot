import time
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from functools import wraps
import asyncio
from typing import Callable, Any
from src.exceptions import RateLimitExceededError

class RateLimited:
    def __init__(self, calls: int, period: int, priority: int = 1):
        self.base_calls = calls
        self.calls = calls
        self.period = period
        self.priority = priority
        self.queue = asyncio.PriorityQueue()
        self.timestamps = []
        self.health_monitor = None
        self.last_adjusted = 0

    def set_health_monitor(self, monitor):
        self.health_monitor = monitor

    async def adjust_rate(self):
        """Dynamically adjust rate limits based on system health"""
        now = time.time()
        if now - self.last_adjusted < 60:  # Only adjust once per minute
            return

        # Calculate current call rate
        self.timestamps = [t for t in self.timestamps if t > now - self.period]
        current_rate = len(self.timestamps)

        # Adjust based on health if monitor available
        if self.health_monitor:
            health_factor = self.health_monitor.get_health_factor()
            # Scale between 50-150% of base calls
            self.calls = max(1, min(
                int(self.base_calls * (0.5 + health_factor)),
                int(self.base_calls * 1.5)
            ))

        self.last_adjusted = now

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            now = time.time()
            
            # Perform dynamic rate adjustment
            await self.adjust_rate()
            
            # Track call timestamps
            self.timestamps = [t for t in self.timestamps if t > now - self.period]
            self.timestamps.append(now)
            
            # Enqueue and check limits
            await self.queue.put((self.priority, func))
            if len(self.timestamps) > self.calls or self.queue.qsize() > self.calls:
                raise RateLimitExceededError(
                    f"Max {self.calls} calls per {self.period} seconds reached "
                    f"(current: {len(self.timestamps)})"
                )
                
            return await func(*args, **kwargs)
        return wrapper

def rh_api_retry(func: Callable) -> Callable:
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )(func)

def ai_api_retry(func: Callable) -> Callable:
    return retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        reraise=True
    )(func)