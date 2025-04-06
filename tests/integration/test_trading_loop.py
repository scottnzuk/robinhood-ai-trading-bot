"""
Integration tests for trading loop functionality
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.main import TradingBot
from src.api import (
    login_to_robinhood,
    is_market_open,
    make_trading_decisions
)

@pytest.fixture
def trading_bot():
    return TradingBot()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_bot_initialization(trading_bot):
    """Test trading bot initialization"""
    assert trading_bot.trade_count == 0
    assert trading_bot.last_trade_time is None
    assert trading_bot.session_start is not None

@pytest.mark.integration
@pytest.mark.asyncio
@patch('src.main.login_to_robinhood')
async def test_auth_failure(mock_login, trading_bot):
    """Test authentication failure handling"""
    mock_login.return_value = False
    with pytest.raises(SystemExit):
        await trading_bot.run()

@pytest.mark.integration
@pytest.mark.asyncio
@patch('src.main.is_market_open')
@patch('src.main.make_trading_decisions')
async def test_market_analysis(mock_decisions, mock_market, trading_bot):
    """Test market analysis execution"""
    mock_market.return_value = True
    mock_decisions.return_value = {
        "TEST": {
            "decision": "hold",
            "confidence": 0.8,
            "reasoning": "Test decision"
        }
    }
    
    try:
        decisions = await asyncio.wait_for(
            trading_bot._analyze_and_decide(),
            timeout=5.0
        )
        assert len(decisions) == 1
        assert decisions["TEST"]["decision"] == "hold"
    except asyncio.TimeoutError:
        pytest.fail("Test timed out")

@pytest.mark.integration
@pytest.mark.asyncio
@patch('src.main.login_to_robinhood')
@patch('src.main.is_market_open')
@patch('src.main.get_account_info')
async def test_error_handling(mock_account, mock_market, mock_login):
    """Test error handling in trading loop"""
    trading_bot = TradingBot(demo_mode=True)
    mock_login.return_value = True
    mock_market.return_value = True
    mock_account.side_effect = Exception("Test error")
    
    with pytest.raises(Exception):
        await asyncio.wait_for(
            trading_bot.run(),
            timeout=5.0
        )