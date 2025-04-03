"""
Mock AI Provider for testing
"""
from unittest.mock import MagicMock
from enum import Enum

class AIProvider(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    REQUESTLY = "requestly"
    OPENROUTER = "openrouter"

class AIProviderClient:
    def __init__(self, provider, config=None):
        self.provider = provider
        self.mock = MagicMock()
        
    def make_request(self, *args, **kwargs):
        return self.mock(*args, **kwargs)

# Mock the default client
default_client = AIProviderClient(AIProvider.OPENAI)