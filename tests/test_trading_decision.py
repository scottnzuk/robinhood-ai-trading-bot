import pytest
from src.api.trading_decision import TradingDecisionEngine, TradingDecision

@pytest.fixture
def engine():
    return TradingDecisionEngine()

def test_analyze_market_returns_dict(engine):
    result = engine.analyze_market()
    assert isinstance(result, dict)
    for symbol, decision in result.items():
        assert isinstance(decision, TradingDecision)

def test_build_analysis_prompt(engine):
    context = {"market": "bullish", "symbols": ["AAPL", "TSLA"]}
    prompt = engine._build_analysis_prompt(context)
    assert isinstance(prompt, str)
    assert "AAPL" in prompt or "TSLA" in prompt

def test_parse_ai_response(engine):
    mock_response = {
        "recommendations": {
            "AAPL": "BUY",
            "TSLA": "SELL"
        }
    }
    parsed = engine._parse_ai_response(mock_response)
    assert isinstance(parsed, dict)
    assert "AAPL" in parsed and "TSLA" in parsed