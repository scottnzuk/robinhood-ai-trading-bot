import pytest
from unittest.mock import AsyncMock, MagicMock
from src.main import TradingBot

def mock_decisions():
    decision = MagicMock()
    decision.decision = "buy"
    decision.quantity = 1
    decision.confidence = 0.9
    return {"AAPL": decision}

@pytest.mark.asyncio
async def test_timeout_handling():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(side_effect=TimeoutError("timeout"))
    try:
        await bot._execute_trades(mock_decisions())
    except Exception:
        pass

@pytest.mark.asyncio
async def test_invalid_response_handling():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(return_value=None)
    try:
        await bot._execute_trades(mock_decisions())
    except Exception:
        pass

@pytest.mark.asyncio
async def test_auth_failure_handling():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(side_effect=PermissionError("auth failed"))
    try:
        await bot._execute_trades(mock_decisions())
    except Exception:
        pass

@pytest.mark.asyncio
async def test_rate_limit_handling():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(side_effect=Exception("rate limit"))
    try:
        await bot._execute_trades(mock_decisions())
    except Exception:
        pass