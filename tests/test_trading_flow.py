import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.main import TradingBot

@pytest.mark.asyncio
async def test_full_trading_flow():
    bot = TradingBot(demo_mode=True)

    with patch.object(bot, '_should_run', side_effect=[True, False]), \
         patch.object(bot, '_analyze_and_decide', new_callable=AsyncMock) as mock_analyze, \
         patch.object(bot, '_execute_trades', new_callable=AsyncMock) as mock_execute:

        mock_analyze.return_value = {"AAPL": "BUY", "TSLA": "SELL"}
        await bot.run()

        mock_analyze.assert_awaited_once()
        mock_execute.assert_awaited_once_with({"AAPL": "BUY", "TSLA": "SELL"})