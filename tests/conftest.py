"""
Pytest configuration and fixtures
"""
import sys
import os
from unittest.mock import MagicMock

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Create mock modules
mock_ai_provider = MagicMock()
mock_ai_provider.AIProvider = MagicMock()
mock_ai_provider.AIProviderClient = MagicMock()
mock_ai_provider.default_client = MagicMock()

mock_logger = MagicMock()
mock_logger.logger = MagicMock()

# Override the real modules
sys.modules['src.api.ai_provider'] = mock_ai_provider
sys.modules['src.utils.logger'] = mock_logger