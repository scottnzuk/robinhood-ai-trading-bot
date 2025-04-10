import abc
from typing import Dict, List


class StrategyBase(abc.ABC):
    """
    Abstract base class for Strategy modules.
    Handles trading logic, signal generation, and plugin integration.
    """

    @abc.abstractmethod
    async def generate_signals(self, analytics_output: Dict) -> List[Dict]:
        """Generate trade signals based on analytics output."""
        pass

    async def load_plugin(self, plugin_name: str) -> None:
        """
        Dynamically load a strategy logic plugin.
        """
        # TODO: Implement dynamic plugin loading
        pass

    async def handle_error(self, error: Exception) -> None:
        """
        Centralized error handling for strategy failures.
        """
        # TODO: Implement fallback to default strategy, plugin reload
        pass

    # Placeholder for circuit breaker integration
    async def circuit_breaker_check(self) -> bool:
        """
        Check circuit breaker status before processing.
        """
        # TODO: Implement circuit breaker logic
        return False