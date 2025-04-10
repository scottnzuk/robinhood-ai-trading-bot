"""
Execution package for the Robinhood AI Trading Bot.

This package provides order execution functionality with anti-gaming protection
and circuit breaker mechanisms.
"""

from src.execution.strategy_execution import StrategyExecutor, ExecutionState
from src.execution.anti_gaming import AntiGamingSystem, AntiGamingConfig
from src.execution.circuit_breaker import CircuitBreaker, CircuitBreakerService

__all__ = [
    'StrategyExecutor',
    'ExecutionState',
    'AntiGamingSystem',
    'AntiGamingConfig',
    'CircuitBreaker',
    'CircuitBreakerService'
]
