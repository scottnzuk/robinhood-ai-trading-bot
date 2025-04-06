import pytest
from src import meta_learning

@pytest.mark.asyncio
async def test_log_call():
    await meta_learning.log_call("agent", "prompt", "response", True, 0.1, 0.01, "good")

@pytest.mark.asyncio
async def test_analyze_performance():
    result = await meta_learning.analyze_performance()
    assert isinstance(result, dict) or result is None

@pytest.mark.asyncio
async def test_adaptive_routing():
    prompt = "Test prompt"
    candidates = ["agent1", "agent2"]
    result = await meta_learning.adaptive_routing(prompt, candidates)
    assert isinstance(result, list) or result is None

@pytest.mark.asyncio
async def test_discover_plugins():
    sources = ["source1", "source2"]
    result = await meta_learning.discover_plugins(sources)
    assert isinstance(result, dict) or result is None