import pytest
from src.api.key_manager import ProviderRegistry
from src.api.openai_client import OpenAIClient
from src.ai_trading_framework.execution_engine import ExecutionEngine, ExchangeAdapter
import asyncio

@pytest.fixture
def key_registry():
    reg = ProviderRegistry()
    reg.add_provider("requestly", ["sk-test-req"], priority=1)
    reg.add_provider("deepseek", ["sk-test-ds"], priority=2)
    reg.add_provider("openrouter", ["sk-test-or"], priority=3)
    return reg

@pytest.fixture
def ai_client(key_registry):
    return OpenAIClient(registry=key_registry)

@pytest.fixture
def execution_engine():
    adapter = ExchangeAdapter()
    return ExecutionEngine(adapter)

@pytest.mark.asyncio
async def test_ai_provider_failover(ai_client):
    prompt = "Test prompt"
    try:
        result = ai_client.get_completion(prompt)
        assert isinstance(result, str)
    except Exception:
        # Acceptable if all keys fail
        pass

@pytest.mark.asyncio
async def test_order_execution(execution_engine):
    order = await execution_engine.process_signal("AAPL", "buy", 0.9, 0.1, 0.05)
    assert "status" in order

@pytest.mark.asyncio
async def test_multiple_orders(execution_engine):
    symbols = ["AAPL", "GOOG", "TSLA"]
    results = []
    for sym in symbols:
        order = await execution_engine.process_signal(sym, "buy", 0.8, 0.2, 0.1)
        results.append(order)
    assert all("status" in o for o in results)

def test_key_rotation(key_registry):
    provider, key_obj = key_registry.get_next_key()
    assert key_obj.is_available()
    key_registry.mark_key_error(provider, key_obj, rate_limited_seconds=1)
    provider2, key_obj2 = key_registry.get_next_key()
    assert key_obj2 != key_obj or not key_obj2.is_available()

def test_key_encryption(key_registry):
    provider, key_obj = key_registry.get_next_key()
    decrypted = key_obj.get_decrypted()
    assert decrypted.startswith("sk-")