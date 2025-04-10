import os
import json
import time
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
from ..utils.logger import logger
from ..config import DEFAULT_AI_PROVIDER

class AIProvider(Enum):
    REQUESTY = "requesty"
    DEEPSEEK = "deepseek" 
    OPENROUTER = "openrouter"
    OPENAI = "openai"

PROVIDER_PRIORITY = [
    AIProvider.REQUESTY,
    AIProvider.DEEPSEEK,
    AIProvider.OPENROUTER,
    AIProvider.OPENAI
]

@dataclass
class AIResponse:
    content: str
    status_code: int
    latency: float

class AIProviderClient:
    """Client with failover capability between multiple AI providers"""
    
    def __init__(self):
        self.active_provider = None
        self.providers = self._initialize_providers()
        self.last_failover_time = 0
        self.failover_interval = 600  # 10 minutes
        
    def _initialize_providers(self) -> Dict[AIProvider, Dict]:
        """Initialize available providers based on env vars"""
        providers = {}
        for provider in PROVIDER_PRIORITY:
            api_key = os.getenv(f"{provider.name}_API_KEY")
            if api_key:
                providers[provider] = {
                    "api_key": api_key,
                    "base_url": self._get_base_url(provider),
                    "headers": {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                }
        return providers
        
    def _get_base_url(self, provider: AIProvider) -> str:
        """Get base API URL for provider"""
        return {
            AIProvider.REQUESTY: "https://api.requesty.ai/v1",
            AIProvider.DEEPSEEK: "https://api.deepseek.com/v1",
            AIProvider.OPENROUTER: "https://openrouter.ai/api/v1",
            AIProvider.OPENAI: "https://api.openai.com/v1"
        }[provider]
        
    def _select_provider(self) -> Optional[AIProvider]:
        """
        Select the highest priority available provider.

        Tries the default provider first, then falls back to the priority list.
        Returns:
            The selected AIProvider enum member or None if none available.
        """
        # Prefer default configured provider
        if DEFAULT_AI_PROVIDER in self.providers:
            return DEFAULT_AI_PROVIDER

        # Otherwise, select first available in priority order
        for provider in PROVIDER_PRIORITY:
            if provider in self.providers:
                return provider
        return None

    def _check_provider_online(self, provider: AIProvider) -> bool:
        """
        Check if a provider is online by querying its /models endpoint.

        Args:
            provider: The AIProvider enum member.

        Returns:
            True if provider responds with HTTP 200, False otherwise.
        """
        try:
            response = requests.get(
                f"{self.providers[provider]['base_url']}/models",
                headers=self.providers[provider]['headers'],
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def _attempt_failover(self) -> bool:
        """
        Attempt to failover to the next available provider in priority order.

        Failover occurs only if the failover interval has elapsed.
        Updates self.active_provider if successful.

        Returns:
            True if failover succeeded, False otherwise.
        """
        current_time = time.time()
        if current_time - self.last_failover_time < self.failover_interval:
            return False

        self.last_failover_time = current_time
        for provider in PROVIDER_PRIORITY:
            if (
                provider in self.providers
                and provider != self.active_provider
                and self._check_provider_online(provider)
            ):
                logger.warning(f"Failing over to {provider.name} provider")
                self.active_provider = provider
                return True
        return False
        
    def make_request(self, prompt: str) -> AIResponse:
        """Make request with automatic failover"""
        if not self.active_provider:
            self.active_provider = self._select_provider()
            if not self.active_provider:
                raise Exception("No available AI providers")
                
        try:
            provider = self.active_provider
            config = self.providers[provider]
            
            start_time = time.time()
            response = requests.post(
                f"{config['base_url']}/chat/completions",
                headers=config['headers'],
                json={"messages": [{"role": "user", "content": prompt}]},
                timeout=10
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                return AIResponse(
                    content=response.text,
                    status_code=response.status_code,
                    latency=latency
                )
                
            # Trigger failover on failure
            if self._attempt_failover():
                return self.make_request(prompt)
                
            raise Exception(f"{provider.name} API error: {response.status_code}")
            
        except Exception as e:
            logger.error(f"AI request failed: {str(e)}")
            if self._attempt_failover():
                return self.make_request(prompt)
            raise

# Global client instance with failover capability
ai_client = AIProviderClient()

def make_ai_request(prompt: str) -> str:
    """Make AI request using the failover client"""
    response = ai_client.make_request(prompt)
    data = json.loads(response.content)
    return data["choices"][0]["message"]["content"]