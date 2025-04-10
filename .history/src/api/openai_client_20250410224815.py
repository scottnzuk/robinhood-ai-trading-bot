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
    OPENROUTER_API_KEY,
    REQUESTY_API_KEY,
    DEEPSEEK_API_KEY,
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
    AIProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "",
        "default_model": "gpt-4"
    },
    AIProvider.REQUESTY: {
        "base_url": "https://router.requesty.ai/v1",
        "api_key": os.getenv("REQUESTY_API_KEY"),
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

from .key_manager import ProviderRegistry

class OpenAIClient:
    """Client for OpenAI-compatible APIs"""

    def __init__(self, registry: ProviderRegistry, preferred_provider: AIProvider = None):
        self.registry = registry
        self.preferred_provider = preferred_provider or AIProvider(DEFAULT_AI_PROVIDER)

    def get_completion(self, prompt: str, **kwargs) -> str:
        """Get completion using dynamic key manager"""
        last_exception = None
        for _ in range(4):  # Max providers to try
            provider_name, key_obj = self.registry.get_next_key()
            if not key_obj:
                logger.error("No available API keys across all providers.")
                raise RuntimeError("No available API keys.")
            api_key = key_obj.get_decrypted()
            try:
                # Override API key dynamically
                result = make_ai_request(prompt, api_key=api_key, provider=provider_name, **kwargs)
                return result['choices'][0]['message']['content']
            except Exception as e:
                logger.warning(f"Provider {provider_name} key failed: {str(e)}")
                self.registry.mark_key_error(provider_name, key_obj, rate_limited_seconds=60)
                last_exception = e
                continue
        logger.error(f"All providers failed: {last_exception}")
        raise last_exception

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

from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=60, period=60)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def make_ai_request(
    prompt: str,
    provider: AIProvider = None,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    **kwargs
) -> Dict[str, Any]:
    """
    Make request to AI provider with fallback and decorators
    
    Args:
        prompt: Input prompt/message
        provider: Preferred AI provider to use
        model: Model to use (overrides provider default)
        temperature: Creativity parameter
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters for completion
        
    Returns:
        Dictionary with AI response
    """
    fallback_chain = [
        AIProvider.REQUESTY,
        AIProvider.DEEPSEEK,
        AIProvider.OPENROUTER,
        AIProvider.OPENAI
    ]

    # If user specified provider, start from there
    if provider:
        try_chain = [provider] + [p for p in fallback_chain if p != provider]
    else:
        try_chain = fallback_chain

    # Validate environment variables once
    assert OPENAI_API_KEY, "OPENAI_API_KEY is not set"
    assert REQUESTY_API_KEY, "REQUESTY_API_KEY is not set"
    assert DEEPSEEK_API_KEY, "DEEPSEEK_API_KEY is not set"
    assert OPENROUTER_API_KEY, "OPENROUTER_API_KEY is not set"

    last_exception = None

    for prov in try_chain:
        config = PROVIDER_CONFIG[prov]
        selected_model = model or config["default_model"]

        try:
            logger.info(f"Attempting provider: {prov.value} with model: {selected_model}")

            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"]
            )

            if prov == AIProvider.REQUESTY:
                client._client.headers.update({"Authorization": f"Bearer {config['api_key']}"})

            response = client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            logger.info(f"Provider {prov.value} succeeded.")
            return json.loads(response.json())

        except Exception as e:
            logger.warning(f"Provider {prov.value} failed: {str(e)}")
            last_exception = e
            continue

    logger.error(f"All AI providers failed. Raising last error: {last_exception}")
    raise last_exception
