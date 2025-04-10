import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

from openai import OpenAI
from src.api.ai_provider import AIProvider
from src.config import (
    OPENAI_API_KEY,
    REQUESTY_API_KEY,
    DEEPSEEK_API_KEY,
    OPENROUTER_API_KEY,
    PROVIDER_CONFIG,
)

class AIClient(ABC):
    @abstractmethod
    async def get_chat_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        pass

class OpenAICompatibleClient(AIClient):
    def __init__(self, fallback_order: Optional[List[AIProvider]] = None):
        self.fallback_order = fallback_order or [
            AIProvider.REQUESTY,
            AIProvider.DEEPSEEK,
            AIProvider.OPENROUTER,
            AIProvider.OPENAI,
        ]

    @sleep_and_retry
    @limits(calls=60, period=60)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_chat_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        last_exception = None

        for prov in self.fallback_order:
            config = PROVIDER_CONFIG[prov]
            selected_model = model or config["default_model"]

            try:
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

                return json.loads(response.json())

            except Exception as e:
                last_exception = e
                continue

        raise last_exception

def get_ai_client(preferred_provider: Optional[AIProvider] = None) -> AIClient:
    fallback_order = [
        AIProvider.REQUESTY,
        AIProvider.DEEPSEEK,
        AIProvider.OPENROUTER,
        AIProvider.OPENAI,
    ]

    if preferred_provider:
        fallback_order = [preferred_provider] + [p for p in fallback_order if p != preferred_provider]

    return OpenAICompatibleClient(fallback_order=fallback_order)