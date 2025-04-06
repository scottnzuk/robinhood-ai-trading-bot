import pytest
from unittest.mock import patch, MagicMock
from src.api.ai_provider import AIProviderClient, AIResponse

@pytest.fixture
def ai_client(monkeypatch):
    # Patch environment variables to simulate API keys
    monkeypatch.setenv("REQUESTY_API_KEY", "testkey")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "testkey")
    monkeypatch.setenv("OPENROUTER_API_KEY", "testkey")
    monkeypatch.setenv("OPENAI_API_KEY", "testkey")
    return AIProviderClient()

def test_select_provider_returns_default_or_priority(ai_client):
    provider = ai_client._select_provider()
    assert provider is None or provider in ai_client.providers

@patch('src.api.ai_provider.requests.post')
def test_make_request_success(mock_post, ai_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"choices":[{"message":{"content":"Test reply"}}]}'
    mock_post.return_value = mock_response

    result = ai_client.make_request("Hello?")
    assert isinstance(result, AIResponse)
    assert result.status_code == 200
    assert "Test reply" in result.content

@patch('src.api.ai_provider.requests.get')
def test_check_provider_online_success(mock_get, ai_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    for provider in ai_client.providers:
        assert ai_client._check_provider_online(provider) is True

@patch('src.api.ai_provider.requests.get')
def test_check_provider_online_failure(mock_get, ai_client):
    mock_get.side_effect = Exception("Network error")
    for provider in ai_client.providers:
        assert ai_client._check_provider_online(provider) is False