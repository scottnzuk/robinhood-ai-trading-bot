"""
OpenAI Client Wrapper

Handles communication with various AI providers using OpenAI-compatible API
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
import json
import logging
from openai import OpenAI
from openai._exceptions import APIError, AuthenticationError
from ..config import (
    OPENAI_API_KEY,
    REQUESTY_API_KEY,
    DEEPSEEK_API_KEY,
    OPENROUTER_API_KEY,
    DEFAULT_AI_PROVIDER,
    DEFAULT_AI_MODEL
)

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    OPENAI = "openai"
    REQUESTY = "requesty"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"

DEFAULT_AI_PROVIDER = AIProvider.REQUESTY

PROVIDER_CONFIG = {
    AIProvider.OPENAI: {
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "default_model": "gpt-4"
    },
    AIProvider.REQUESTY: {
        "base_url": "https://router.requesty.ai/v1",
        "api_key": "sk-Bvo4Ux8pT4iQ7pY/8rqn4tkP8FsRX4DSrI3qsN9zAYf9mr7VdF81Xr182G757Yytnd17sBE5GJ1RlzFsZAtITUa12PentDPN+WKu8hCqEAo=",
        "default_model": "openai/gpt-4o-mini-2024-07-18"
    },
    AIProvider.DEEPSEEK: {
        "base_url": "https://api.deepseek.com/v1",
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "default_model": "deepseek-chat"
    },
    AIProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "default_model": "openai/gpt-4"
    }
}

class OpenAIClient:
    """Client for OpenAI-compatible APIs"""
    
    def __init__(self, provider: AIProvider = None):
        self.provider = provider or AIProvider(DEFAULT_AI_PROVIDER)
        self.config = PROVIDER_CONFIG[self.provider]
        
    def get_completion(self, prompt: str, **kwargs) -> str:
        """Get completion from the configured provider"""
        try:
            result = make_ai_request(prompt, provider=self.provider, **kwargs)
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Completion failed: {str(e)}")
            raise

def get_top_finance_models() -> Dict[str, Any]:
    """Get list of top finance-focused models from OpenRouter"""
    try:
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        models = client.models.list()
        return {
            m.id: m.dict()
            for m in models.data
            if "finance" in m.id.lower() or "trading" in m.id.lower()
        }
    except Exception as e:
        logger.error(f"Error getting finance models: {str(e)}")
        return {}

def make_ai_request(
    prompt: str,
    provider: AIProvider = None,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    **kwargs
) -> Dict[str, Any]:
    """
    Make request to AI provider
    
    Args:
        prompt: Input prompt/message
        provider: AI provider to use
        model: Model to use (overrides provider default)
        temperature: Creativity parameter
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters for completion
        
    Returns:
        Dictionary with AI response
    """
    if provider is None:
        provider = AIProvider(DEFAULT_AI_PROVIDER)

    config = PROVIDER_CONFIG[provider]
    model = model or config["default_model"]

    # Validate environment variables
    assert OPENAI_API_KEY, "OPENAI_API_KEY is not set"
    assert REQUESTY_API_KEY, "REQUESTY_API_KEY is not set"
    assert DEEPSEEK_API_KEY, "DEEPSEEK_API_KEY is not set"
    assert OPENROUTER_API_KEY, "OPENROUTER_API_KEY is not set"

    try:
        # Print loaded API key for OpenAI
        logger.info(f"Loaded OpenAI API Key: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-5:]}")

        # Initialize client with API key
        client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"]
        )

        # Manually set headers for Requesty provider
        if provider == AIProvider.REQUESTY:
            client._client.headers.update({"Authorization": f"Bearer {config['api_key']}"})

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return json.loads(response.json())

    except Exception as e:
        logger.error(f"Error with {provider.value}: {str(e)}")
        raise
