class TradingSystemError(Exception):
    """Base exception for all trading system errors"""
    pass

class RateLimitExceededError(TradingSystemError):
    """Raised when API rate limits are exceeded"""
    def __init__(self, message="API rate limit exceeded"):
        self.message = message
        super().__init__(self.message)

class CircuitTrippedError(TradingSystemError):
    """Raised when circuit breaker is active"""
    def __init__(self, message="Circuit breaker tripped"):
        self.message = message
        super().__init__(self.message)

class CacheValidationError(TradingSystemError):
    """Raised for cache integrity violations"""
    pass

class PatternDetectionTimeout(TradingSystemError):
    """Raised when pattern detection exceeds allowed time"""
    pass

class RiskValidationError(TradingSystemError):
    """Raised when trade violates risk parameters"""
    pass

class APIEndpointError(TradingSystemError):
    """Base class for API-specific errors"""
    def __init__(self, endpoint: str, status_code: int, message: str):
        self.endpoint = endpoint
        self.status_code = status_code
        self.message = f"{endpoint} returned {status_code}: {message}"
        super().__init__(self.message)

class RobinhoodAPIError(APIEndpointError):
    """Robinhood API specific errors"""
    pass

class AIProviderError(APIEndpointError):
    """AI provider API specific errors"""
    pass

class InvalidAIResponseError(TradingSystemError):
    """Raised when AI response cannot be parsed or is invalid"""
    def __init__(self, message="Invalid AI response format or content"):
        self.message = message
        super().__init__(self.message)