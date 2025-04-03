import pytest
import time
from unittest.mock import patch, MagicMock
from src.api.robinhood import RobinhoodTrader, TRADE_RATE_LIMIT
from cachetools import TTLCache

@pytest.fixture
def rh_client():
    """Fixture providing authenticated Robinhood client with proper mocks"""
    with patch('src.api.robinhood.RobinhoodTrader.authenticate') as mock_auth, \
         patch('src.api.robinhood.OPClient') as mock_op_client, \
         patch('requests.Session') as mock_session:
        
        # Setup mock OPClient
        mock_op = MagicMock()
        mock_op_client.return_value = mock_op
        mock_op.get_robinhood_credentials.return_value = {
            'username': 'test_user',
            'password': 'test_pass',
            'mfa_secret': 'test_mfa'
        }
        
        # Setup mock session with timeout behavior
        mock_session.return_value = MagicMock()
        mock_session.return_value.request.return_value.json.return_value = {
            'results': [{'close_price': '150.00'}]
        }
        mock_session.return_value.request.return_value.elapsed.total_seconds.return_value = 0.1
        
        client = RobinhoodTrader()
        client.credentials = mock_op.get_robinhood_credentials()
        client.session = mock_session.return_value
        client.price_cache = TTLCache(maxsize=1000, ttl=300)
        
        # Mock successful authentication
        mock_auth.return_value = True
        yield client

@pytest.mark.skip(reason="Benchmark tests disabled - focus on functional testing")
def test_trade_execution_performance(rh_client, benchmark):
    """Benchmark trade execution performance"""
    decision = {
        "symbol": "AAPL",
        "quantity": 1,
        "price": 150.0,
        "side": "buy"
    }
    
    benchmark.extra_info['test_type'] = 'trade_execution'
    benchmark.extra_info['iterations'] = 5
    
    def trade_execution():
        return rh_client.make_trade(decision)
    
    result = benchmark(trade_execution)
    assert isinstance(result, bool)

@pytest.mark.skip(reason="Benchmark tests disabled - focus on functional testing")
def test_api_response_time(rh_client, benchmark):
    """Benchmark API response time for critical endpoints"""
    benchmark.extra_info['test_type'] = 'api_response'
    
    # Mock account info response
    rh_client.session.request.return_value.json.return_value = {
        'account_number': '12345678'
    }
    
    def get_account_info():
        return rh_client.get_account_info()
    
    result = benchmark(get_account_info)
    assert isinstance(result, dict)

@pytest.mark.skip(reason="Benchmark tests disabled - focus on functional testing")
def test_cache_performance(rh_client, benchmark):
    """Benchmark cache hit vs miss performance"""
    params = {"symbol": "AAPL", "interval": "day", "span": "week"}
    
    benchmark.extra_info['test_type'] = 'cache_performance'
    
    # Clear cache before test
    rh_client.price_cache.clear()
    
    # Benchmark cache miss
    def cache_miss():
        return rh_client.get_historical_data(**params)
    
    miss_result = benchmark(cache_miss)
    assert isinstance(miss_result, dict)
    
    # Benchmark cache hit (same params)
    def cache_hit():
        return rh_client.get_historical_data(**params)
    
    hit_result = benchmark(cache_hit)
    assert isinstance(hit_result, dict)

@pytest.mark.skip(reason="Benchmark tests disabled - focus on functional testing")
def test_rate_limiting_impact(rh_client, benchmark):
    """Measure throughput impact of rate limiting"""
    decision = {
        "symbol": "AAPL",
        "quantity": 1,
        "price": 150.0,
        "side": "buy"
    }
    
    benchmark.extra_info['test_type'] = 'rate_limiting'
    
    # Benchmark with rate limiting
    def trade_execution():
        return rh_client.make_trade(decision)
    
    limited_result = benchmark(trade_execution)
    assert isinstance(limited_result, bool)

@pytest.mark.skip(reason="Benchmark tests disabled - focus on functional testing")
def test_retry_overhead(rh_client, benchmark):
    """Measure overhead added by retry mechanism"""
    params = {"symbol": "AAPL", "interval": "day", "span": "week"}
    
    benchmark.extra_info['test_type'] = 'retry_overhead'
    
    def operation():
        return rh_client.get_historical_data(**params)
    
    result = benchmark(operation)
    assert isinstance(result, dict)

@pytest.mark.skip(reason="Benchmark tests disabled - focus on functional testing")
def test_historical_data_performance(rh_client, benchmark):
    """Benchmark historical data fetch performance"""
    test_cases = [
        ("AAPL", "day", "week"),
        ("MSFT", "hour", "day"),
        ("TSLA", "5minute", "day")
    ]
    
    benchmark.extra_info['test_type'] = 'historical_data'
    
    for symbol, interval, span in test_cases:
        params = {"symbol": symbol, "interval": interval, "span": span}
        
        def operation():
            return rh_client.get_historical_data(**params)
        
        result = benchmark(operation)
        assert isinstance(result, dict)