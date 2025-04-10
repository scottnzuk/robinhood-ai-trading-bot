import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.main import TradingBot

@pytest.mark.asyncio
async def test_trading_bot_run_demo_mode():
    bot = TradingBot(demo_mode=True)

    with patch.object(bot, '_should_run', return_value=False):
        await bot.run()

@patch('src.main.TradingBot._analyze_and_decide', new_callable=AsyncMock)
@patch('src.main.TradingBot._execute_trades', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_trading_bot_run_once(mock_execute, mock_analyze):
    bot = TradingBot(demo_mode=False)

    call_count = 0

    async def limited_should_run():
        nonlocal call_count
        call_count += 1
        return call_count < 2  # Run loop once

    with patch.object(bot, '_should_run', side_effect=limited_should_run):
        mock_analyze.return_value = {"AAPL": "BUY"}
        await bot.run()

    mock_analyze.assert_awaited()
    mock_execute.assert_awaited()