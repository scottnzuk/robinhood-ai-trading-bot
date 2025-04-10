import asyncio
import pytest
from src.strategy_framework import StrategyRegistry
from src.risk_management.risk_management import RiskManager
from src.ai_trading_engine import cached_openai_call
from unittest.mock import patch

@pytest.mark.asyncio
async def test_plugin_loader_discovers_strategies():
    registry = StrategyRegistry()
    registry.auto_discover_and_register(package="strategies")
    assert len(registry.list_strategies()) > 0

def test_adaptive_risk_manager_adjustment():
    rm = RiskManager()
    rm.portfolio_value = 100000
    rm.parameters.max_risk_per_trade = 0.02
    rm.parameters.max_risk_per_trade_default = 0.02
    rm.parameters.max_position_size = 0.1
    rm.parameters.max_position_size_default = 0.1
    rm.parameters.volatility_threshold_high = 0.05
    rm.parameters.volatility_threshold_low = 0.01

    rm.adjust_risk_parameters(0.06)
    assert rm.parameters.max_risk_per_trade < 0.02
    rm.adjust_risk_parameters(0.005)
    assert rm.parameters.max_risk_per_trade <= 0.02

@pytest.mark.asyncio
async def test_cached_openai_call_retry_and_cache():
    prompt = "Test prompt"
    model = "gpt-4"
    ai_provider = "openai"

    with patch('src.ai_trading_engine.openai.ChatCompletion.acreate') as mock_acreate:
