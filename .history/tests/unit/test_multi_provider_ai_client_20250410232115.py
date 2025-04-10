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
            prov_url = kwargs.get("base_url", "")
            if "openai" in prov_url:
                mock_instance = MagicMock()
                mock_response = MagicMock()
                mock_response.json.return_value = '{"choices":[{"message":{"content":"response"}}]}'
                mock_instance.chat.completions.create.return_value = mock_response
                return mock_instance
            else:
                raise Exception("Provider failure")

        mock_openai_class.side_effect = side_effect

        response = await client.get_chat_completion(prompt)
        assert "choices" in response

@pytest.mark.asyncio
async def test_get_ai_client_preferred_provider_order():
    preferred = AIProvider.DEEPSEEK
    client = ai_clients.get_ai_client(preferred_provider=preferred)
    assert isinstance(client, ai_clients.OpenAICompatibleClient)
    assert client.fallback_order[0] == preferred

@pytest.mark.asyncio
async def test_ai_trading_engine_integration_with_client():
    prompt = "Test prompt"
    mock_client = MagicMock()
    mock_client.get_chat_completion = AsyncMock(return_value={
        "choices": [{"message": {"content": '{"recommendations": []}'}}]
    })

    engine = AITradingEngine(ai_client=mock_client)
    result = await engine._analyze_with_primary_model(prompt)
    assert "recommendations" in result

@pytest.mark.asyncio
async def test_ai_trading_strategy_generate_signals():
    mock_client = MagicMock()
    mock_client.get_chat_completion = AsyncMock(return_value={
        "choices": [{"message": {"content": '{"recommendations": [{"symbol": "AAPL", "decision": "buy", "confidence": 0.9}]}'}}]
    })

    strategy = AITradingStrategy(ai_client=mock_client)
    data = {"market_data": {}, "portfolio": {}}
    signals = await strategy.generate_signals(data)
    assert isinstance(signals, list)
    assert signals[0].symbol == "AAPL"
    assert signals[0].signal_type.name.lower() == "buy"