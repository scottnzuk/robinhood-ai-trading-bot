from datetime import datetime
from typing import Any, Callable, Dict, Optional
from functools import wraps
import asyncio
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    start_http_server
)

# Initialize Prometheus metrics
METRICS_PORT = 8000

# API Metrics
API_CALLS = Counter(
    'trading_api_calls_total',
    'Total API calls',
    ['endpoint', 'status']
)
API_LATENCY = Histogram(
    'trading_api_latency_seconds',
    'API call latency',
    ['endpoint']
)

# Trading Metrics
TRADES_EXECUTED = Counter(
    'trading_executed_total',
    'Executed trades',
    ['symbol', 'action']
)
TRADE_AMOUNTS = Histogram(
    'trading_amount_usd',
    'Trade amounts in USD',
    ['symbol', 'action']
)

# System Metrics
CACHE_HITS = Counter(
    'trading_cache_hits_total',
    'Cache hit counter',
    ['cache_name']
)
CIRCUIT_STATE = Gauge(
    'trading_circuit_state',
    'Circuit breaker state',
    ['endpoint']
)

def start_metrics_server():
    """Start Prometheus metrics server"""
    start_http_server(METRICS_PORT)

def track_metrics(
    endpoint: Optional[str] = None,
    track_latency: bool = True,
    track_counts: bool = True
) -> Callable:
    """
    Decorator for tracking function metrics
    
    Args:
        endpoint: Endpoint name for API metrics
        track_latency: Whether to track execution time
        track_counts: Whether to track call counts
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                
                if track_counts and endpoint:
                    API_CALLS.labels(endpoint=endpoint, status='success').inc()
                
                if isinstance(result, dict) and 'symbol' in result:
                    TRADES_EXECUTED.labels(
                        symbol=result['symbol'],
                        action=result.get('action', 'unknown')
                    ).inc()
                    
                    if 'amount' in result:
                        TRADE_AMOUNTS.labels(
                            symbol=result['symbol'],
                            action=result.get('action', 'unknown')
                        ).observe(result['amount'])
                
                return result
            except Exception as e:
                if track_counts and endpoint:
                    API_CALLS.labels(endpoint=endpoint, status='error').inc()
                raise
            finally:
                if track_latency and endpoint:
                    latency = (datetime.now() - start_time).total_seconds()
                    API_LATENCY.labels(endpoint=endpoint).observe(latency)
        return wrapper
    return decorator

def record_cache_hit(cache_name: str):
    """Record a cache hit"""
    CACHE_HITS.labels(cache_name=cache_name).inc()

def update_circuit_state(endpoint: str, state: int):
    """Update circuit breaker state gauge"""
    CIRCUIT_STATE.labels(endpoint=endpoint).set(state)