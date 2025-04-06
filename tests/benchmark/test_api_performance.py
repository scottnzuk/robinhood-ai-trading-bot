import time
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.main import TradingBot

@pytest.mark.asyncio
async def test_benchmark_providers():
    bot = TradingBot()
    bot.rh_client = MagicMock()
    bot.rh_client.get_account_info = AsyncMock(return_value={"account": "mock"})
    bot.rh_client.buy_stock = AsyncMock(return_value={"status": "filled"})
    bot.rh_client.sell_stock = AsyncMock(return_value={"status": "filled"})

    decision_mock = MagicMock()
    decision_mock.decision = "buy"
    decision_mock.quantity = 1
    decision_mock.confidence = 0.9
    decisions = {"AAPL": decision_mock}

    timings = {}

    # Robinhood success
    start = time.perf_counter()
    try:
        await bot._execute_trades(decisions)
    except Exception:
        pass
    timings['Robinhood'] = time.perf_counter() - start

    # Robinhood fail, Gemini success
    bot.rh_client.buy_stock = AsyncMock(side_effect=Exception())
    bot.gemini_client = MagicMock()
    bot.gemini_client.buy_stock = AsyncMock(return_value={"status": "filled"})
    bot.gemini_client.sell_stock = AsyncMock(return_value={"status": "filled"})
    start = time.perf_counter()
    try:
        await bot._execute_trades(decisions)
    except Exception:
        pass
    timings['Gemini'] = time.perf_counter() - start

    # Robinhood & Gemini fail, TDA success
    bot.gemini_client.buy_stock = AsyncMock(side_effect=Exception())
    bot.tda_client = MagicMock()
    bot.tda_client.buy_stock = AsyncMock(return_value={"status": "filled"})
    bot.tda_client.sell_stock = AsyncMock(return_value={"status": "filled"})
    start = time.perf_counter()
    try:
        await bot._execute_trades(decisions)
    except Exception:
        pass
    timings['TDA'] = time.perf_counter() - start

    print("Benchmark timings (seconds):", timings)