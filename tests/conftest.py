"""
Pytest configuration and fixtures
"""
import sys
import os
from unittest.mock import MagicMock

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Set up test environment variables
os.environ.update({
    'MODE': 'test',
    'DEMO_MODE': 'true',
    'crypto_account': 'test_crypto_account',
    'ROBINHOOD_USERNAME': 'test_user@example.com',
    'ROBINHOOD_PASSWORD': 'test_pass',
    'ROBINHOOD_MFA_SECRET': 'test_secret',
    'robin_mfa': 'ABCDEFGHIJKLMNOP',  # Valid base32 string for testing
    'robin_username': 'test_user@example.com',
    'robin_password': 'test_pass',
    'OPENAI_API_KEY': 'test_key',
    'REQUESTY_API_KEY': 'test_key',
    'DEEPSEEK_API_KEY': 'test_key',
    'OPENROUTER_API_KEY': 'test_key'
})

# Create mock modules
mock_ai_provider = MagicMock()
mock_ai_provider.AIProvider = MagicMock()
mock_ai_provider.AIProviderClient = MagicMock()
mock_ai_provider.default_client = MagicMock()

mock_logger = MagicMock()
mock_logger.logger = MagicMock()

# Override the real modules
# sys.modules['src.api.ai_provider'] = mock_ai_provider
sys.modules['src.utils.logger'] = mock_logger