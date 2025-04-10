import abc


class MonitoringBase(abc.ABC):
    """
    Abstract base class for Monitoring modules.
    Handles metrics collection, alerting, and observability.
    """

    @abc.abstractmethod
    async def record_metric(self, name: str, value: float) -> None:
        """Record a system metric."""
        pass

    @abc.abstractmethod
    async def alert(self, message: str, severity: str) -> None:
        """Send an alert with a given severity."""
        pass

    async def handle_error(self, error: Exception) -> None:
        """
        Centralized error handling for monitoring failures.
        """
        # TODO: Implement retry, escalation
        pass