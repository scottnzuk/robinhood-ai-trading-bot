import pytest
import asyncio
import time
from src.circuit_breaker import CircuitBreaker, CircuitBreakerService, BreakerConfig
from src.exceptions import CircuitTrippedError

@pytest.mark.asyncio
async def test_circuit_breaker_basic():
    """Test basic circuit breaker functionality"""
    breaker = CircuitBreaker()
    
    # Initially not active
    assert not breaker.is_active()
    
    # Trip the breaker
    breaker.trip(duration_seconds=1)
    
    # Should be active
    assert breaker.is_active()
    
    # Wait for timeout
    await asyncio.sleep(1.1)
    
    # Should be inactive again
    assert not breaker.is_active()

@pytest.mark.asyncio
async def test_circuit_breaker_service():
    """Test circuit breaker service with multiple endpoints"""
    service = CircuitBreakerService()
    
    # Register endpoints with different configs
    await service.register_endpoint("api1", BreakerConfig(failure_threshold=2))
    await service.register_endpoint("api2", BreakerConfig(failure_threshold=3))
    
    # Record failures for api1
    await service.record_failure("api1")
    
    # Should not trip yet
    assert not await service.check("api1")
    
    # Second failure should trip api1
    with pytest.raises(CircuitTrippedError):
        await service.record_failure("api1")
    
    # Now api1 should be tripped
    assert await service.check("api1")
    
    # But api2 should still be fine
    assert not await service.check("api2")

@pytest.mark.asyncio
async def test_execute_with_circuit_breaker():
    """Test executing functions with circuit breaker protection"""
    service = CircuitBreakerService()
    
    # Test function that succeeds
    async def success_func():
        return "success"
    
    # Test function that fails
    async def failure_func():
        raise ValueError("Simulated failure")
    
    # Execute success function
    result = await service.execute("test_endpoint", success_func)
    assert result == "success"
    
    # Execute failing function, should record failure
    with pytest.raises(ValueError):
        await service.execute("test_endpoint", failure_func)
    
    # Configure with low threshold
    await service.register_endpoint("test_endpoint", BreakerConfig(failure_threshold=1))
    
    # Next failure should trip the circuit
    with pytest.raises(CircuitTrippedError):
        await service.execute("test_endpoint", failure_func)
    
    # Further calls should be blocked
    with pytest.raises(CircuitTrippedError):
        await service.execute("test_endpoint", success_func)

@pytest.mark.asyncio
async def test_circuit_reset():
    """Test circuit breaker reset functionality"""
    service = CircuitBreakerService()
    
    # Register with custom config
    config = BreakerConfig(
        failure_threshold=2,
        success_threshold=2,
        timeout_seconds=1
    )
    await service.register_endpoint("api", config)
    
    # Trip the circuit
    await service.record_failure("api")
    with pytest.raises(CircuitTrippedError):
        await service.record_failure("api")
    
    # Wait for timeout
    await asyncio.sleep(1.1)
    
    # Circuit should be half-open now
    assert not await service.check("api")
    
    # Record successes to fully close the circuit
    await service.record_success("api")
    await service.record_success("api")
    
    # Circuit should be fully closed
    assert not await service.check("api")
