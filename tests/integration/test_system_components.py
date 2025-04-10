import pytest
from unittest.mock import patch, MagicMock
from src.validation import validate_input, ValidationError
from src.metrics import track_metrics
from src.decorators import RateLimited
from src.circuit_breaker import CircuitBreakerService
import asyncio

@pytest.mark.asyncio
async def test_validation_decorator():
    """Test input validation decorator with various cases"""
    
    @validate_input(
        required=['user_id', 'amount'],
        numeric=['amount'],
        positive=['amount'],
        max_length={'user_id': 10},
        min_value={'amount': 1}
    )
    async def process_transaction(user_id: str, amount: float):
        return True
    
    # Test valid input
    assert await process_transaction(user_id="abc123", amount=5.0)
    
    # Test missing required field
    with pytest.raises(ValidationError):
        await process_transaction(user_id="abc123")
        
    # Test invalid type
    with pytest.raises(ValidationError):
        await process_transaction(user_id="abc123", amount="five")
        
    # Test below min value
    with pytest.raises(ValidationError):
        await process_transaction(user_id="abc123", amount=0.5)

@pytest.mark.asyncio
async def test_metrics_collection():
    """Test metrics collection decorator"""
    
    mock_inc = MagicMock()
    mock_observe = MagicMock()
    
    with patch('src.metrics.API_CALLS.labels') as mock_labels:
        mock_labels.return_value.inc = mock_inc
        
        @track_metrics(endpoint="/api/trade", track_latency=False)
        async def place_trade(symbol: str, amount: float):
            return {'symbol': symbol, 'amount': amount, 'action': 'buy'}
            
        result = await place_trade("AAPL", 100.0)
        assert result['symbol'] == "AAPL"
        mock_inc.assert_called_once()

@pytest.mark.asyncio
async def test_circuit_breaker_integration():
    """Test circuit breaker state transitions"""
    service = CircuitBreakerService()
    service.register_endpoint("/api/trade", service.BreakerConfig(
        failure_threshold=2,
        success_threshold=1,
        timeout_seconds=1
    ))
    
    # Should not be tripped initially
    assert not service.check("/api/trade")
    
    # Trip the circuit
    with pytest.raises(Exception):
        service.record_failure("/api/trade")
        service.record_failure("/api/trade")
        
    # Should be tripped now
    assert service.check("/api/trade")
    
    # Wait for timeout and reset
    await asyncio.sleep(1.1)
    assert not service.check("/api/trade")

@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting behavior"""
    rate_limiter = RateLimited(calls=2, period=1)
    
    @rate_limiter
    async def api_call():
        return True
    
    # First two calls should succeed
    assert await api_call()
    assert await api_call()
    
    # Third call should fail
    with pytest.raises(Exception):
        await api_call()