import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

import src.api.ai_clients as ai_clients
from src.api.ai_provider import AIProvider
from src.ai_trading_engine import AITradingEngine, AITradingStrategy

@pytest.mark.asyncio
async def test_openai_compatible_client_success_per_provider():
    prompt = "Test prompt"
    for provider in [AIProvider.REQUESTY, AIProvider.DEEPSEEK, AIProvider.OPENROUTER, AIProvider.OPENAI]:
        client = ai_clients.OpenAICompatibleClient(fallback_order=[provider])

        with patch("src.api.ai_clients.OpenAI") as mock_openai_class:
            mock_openai_instance = MagicMock()
            mock_openai_class.return_value = mock_openai_instance
            mock_response = MagicMock()
            mock_response.json.return_value = '{"choices":[{"message":{"content":"response"}}]}'
            mock_openai_instance.chat.completions.create.return_value = mock_response

            response = await client.get_chat_completion(prompt)
            assert "choices" in response

@pytest.mark.asyncio
async def test_openai_compatible_client_fallback_on_failure():
    prompt = "Test prompt"
    fallback_order = [AIProvider.REQUESTY, AIProvider.DEEPSEEK, AIProvider.OPENROUTER, AIProvider.OPENAI]
    client = ai_clients.OpenAICompatibleClient(fallback_order=fallback_order)

    with patch("src.api.ai_clients.OpenAI") as mock_openai_class:
        # Fail first 3 providers, succeed on last
        def side_effect(*args, **kwargs):
