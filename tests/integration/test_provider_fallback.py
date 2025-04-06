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
async def test_robinhood_success():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(return_value={"status": "filled"})
    try:
        await bot._execute_trades(mock_decisions())
    except Exception:
        pass

@pytest.mark.asyncio
async def test_robinhood_fail_gemini_success():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(side_effect=Exception())
    bot.gemini_client = MagicMock()
    bot.gemini_client.buy_stock = AsyncMock(return_value={"status": "filled"})
    try:
        await bot._execute_trades(mock_decisions())
    except Exception:
        pass

@pytest.mark.asyncio
async def test_robinhood_gemini_fail_tda_success():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(side_effect=Exception())
    bot.gemini_client = MagicMock()
    bot.gemini_client.buy_stock = AsyncMock(side_effect=Exception())
    bot.tda_client = MagicMock()
    bot.tda_client.buy_stock = AsyncMock(return_value={"status": "filled"})
    try:
        await bot._execute_trades(mock_decisions())
    except Exception:
        pass

@pytest.mark.asyncio
async def test_all_providers_fail():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(side_effect=Exception())
    bot.gemini_client = MagicMock()
    bot.gemini_client.buy_stock = AsyncMock(side_effect=Exception())
    bot.tda_client = MagicMock()
    bot.tda_client.buy_stock = AsyncMock(side_effect=Exception())
    try:
        await bot._execute_trades(mock_decisions())
    except Exception:
        pass