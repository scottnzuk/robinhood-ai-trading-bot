import pytest
from unittest.mock import patch, MagicMock
from tenacity import RetryError
from ratelimit import limits, RateLimitException
from cachetools import TTLCache

from src.api.robinhood import RobinhoodTrader

class TestRobinhoodAPIFeatures:
    """Integration tests for Robinhood API features"""
    
    @pytest.fixture
    def mock_client(self):
        """Fixture providing a mock Robinhood client"""
        with patch('src.api.robinhood.RobinhoodTrader.authenticate'), \
             patch('src.api.robinhood.OPClient') as mock_op_client:
            # Setup mock OPClient
            mock_op = MagicMock()
            mock_op_client.return_value = mock_op
            mock_op.get_robinhood_credentials.return_value = {
                'username': 'test_user',
                'password': 'test_pass', 
                'mfa_secret': 'test_mfa'
            }
            
            client = RobinhoodTrader()
            client.session = MagicMock()
            client.cache = TTLCache(maxsize=1000, ttl=300)
            yield client

    def test_retry_logic(self, mock_client):
        """Test that API calls are retried on failure"""
        # Setup mock to fail twice then succeed
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        
        mock_client.session.request.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            mock_response
        ]
        
        # This should succeed after retries
        result = mock_client._make_request('GET', 'https://api.robinhood.com/test')
        assert result == {'success': True}

    def test_rate_limiting(self, mock_client):
        """Test that rate limiting is properly enforced"""
        # Setup mock to return 429 once
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'success': True}
        
        mock_client.session.request.side_effect = [
            mock_response_429,
            mock_response_200
        ]
        
        # This should handle the rate limit and retry
        result = mock_client._make_request('GET', 'https://api.robinhood.com/test')
        assert result == {'success': True}

    def test_caching(self, mock_client):
        """Test that repeated calls use caching"""
        # Setup mock to return consistent data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        
        mock_client.session.request.return_value = mock_response
        
        # First call should hit API
        result1 = mock_client._make_request('GET', 'https://api.robinhood.com/cached')
        assert mock_client.session.request.call_count == 1
        
        # Second call should use cache
        result2 = mock_client._make_request('GET', 'https://api.robinhood.com/cached')
        assert mock_client.session.request.call_count == 1
        assert result1 == result2

    def test_authentication_retry_success(self, mock_client):
        """Test successful authentication after retries"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'authenticated': True}
        
        # Setup to fail twice then succeed
        mock_client.authenticate.side_effect = [
            Exception("First auth failure"),
            Exception("Second auth failure"),
            None  # Success on third attempt
        ]
        
        mock_client.session.request.return_value = mock_response
        
        # This should succeed after retries
        result = mock_client._make_request('GET', 'https://api.robinhood.com/auth')
        assert result == {'authenticated': True}
        assert mock_client.authenticate.call_count == 3

    def test_authentication_retry_failure(self, mock_client):
        """Test authentication failure after max retries"""
        # Setup to always fail
        mock_client.authenticate.side_effect = Exception("Auth failed")
        
        with pytest.raises(RetryError):
            mock_client._make_request('GET', 'https://api.robinhood.com/auth')
        assert mock_client.authenticate.call_count == 3

    def test_watchlist_retry_behavior(self, mock_client):
        """Test watchlist retries on failure"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'watchlist': ['AAPL', 'MSFT']}
        
        # Setup to fail twice then succeed
        mock_client.session.request.side_effect = [
            Exception("First watchlist failure"),
            Exception("Second watchlist failure"),
            mock_response
        ]
        
        result = mock_client.get_watchlist('default')
        assert result == {'watchlist': ['AAPL', 'MSFT']}
        assert mock_client.session.request.call_count == 3

    def test_trade_execution_rate_limiting(self, mock_client):
        """Test trade execution respects rate limits"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'executed'}
        
        # Setup to return 429 once
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_client.session.request.side_effect = [
            mock_response_429,
            mock_response
        ]
        
        result = mock_client.execute_trade({'symbol': 'AAPL', 'side': 'buy'})
        assert result == {'status': 'executed'}
        assert mock_client.session.request.call_count == 2

    def test_cache_ttl_expiration(self, mock_client):
        """Test that cache entries expire after TTL"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        
        mock_client.session.request.return_value = mock_response
        
        # First call - cache miss
        result1 = mock_client._make_request('GET', 'https://api.robinhood.com/cached')
        assert mock_client.session.request.call_count == 1
        
        # Second call - cache hit
        result2 = mock_client._make_request('GET', 'https://api.robinhood.com/cached')
        assert mock_client.session.request.call_count == 1
        
        # Force TTL expiration
        mock_client.cache.clear()
        
        # Third call - cache miss again
        result3 = mock_client._make_request('GET', 'https://api.robinhood.com/cached')
        assert mock_client.session.request.call_count == 2