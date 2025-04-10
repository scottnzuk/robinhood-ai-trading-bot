import abc


class OrchestratorBase(abc.ABC):
    """
    Abstract base class for Orchestration modules.
    Manages lifecycle, plugin reloads, and centralized error handling.
    """

    @abc.abstractmethod
    async def start_all(self) -> None:
        """Start all modules."""
        pass

    @abc.abstractmethod
    async def stop_all(self) -> None:
        """Stop all modules."""
        pass

    @abc.abstractmethod
    async def reload_plugins(self) -> None:
        """Reload all plugins dynamically."""
        pass

    @abc.abstractmethod
    async def handle_error(self, error: Exception) -> None:
        """Centralized error handling and recovery."""
        pass