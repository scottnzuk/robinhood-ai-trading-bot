import os
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from src.api.trading_utils import error, debug
from src.utils.logger import info, warning, error
from src.api.ai_provider import AIProvider, make_ai_request
from src.api.robinhood_utils import (
    get_account_info,
    get_portfolio_stocks,
    get_watchlist_stocks,
    get_historical_data,
    is_market_open
)

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

class DecisionType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    ADJUST = "adjust"

@dataclass
class TradingDecision:
    symbol: str
    decision: DecisionType
    quantity: Optional[float] = None
    price_target: Optional[float] = None
    confidence: float = 0.0
    reasoning: str = ""
    timestamp: str = datetime.now(timezone.utc).isoformat()

class DecisionType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    ADJUST = "adjust"

class TradingDecisionEngine:
    def __init__(self, ai_provider: AIProvider = AIProvider.OPENAI):
        self.ai_provider = ai_provider
        self.last_decision_time = None
        
    def analyze_market(self) -> Dict[str, TradingDecision]:
        if not is_market_open():
            debug("Market is closed - no decisions made")
            return {}
            
        try:
            account_info = get_account_info()
            portfolio = get_portfolio_stocks()
            watchlist = get_watchlist_stocks("default")
            
            context = {
                "account": account_info,
                "portfolio": portfolio,
                "watchlist": watchlist,
                "market_conditions": self._get_market_conditions()
            }
            
            prompt = self._build_analysis_prompt(context)
            response = make_ai_request(prompt, self.ai_provider)
            
            decisions = self._parse_ai_response(response)
            self.last_decision_time = datetime.now(timezone.utc)
            
            return decisions
            
        except Exception as e:
            error(f"Error in market analysis: {str(e)}")
            return {}
            
    def _get_market_conditions(self) -> Dict[str, Any]:
        market_status = "open" if is_market_open() else "closed"
        market_trend = "neutral"
        volatility = "unknown"
        
        try:
            spy_data = get_historical_data("SPY", interval="5minute", span="day")
            qqq_data = get_historical_data("QQQ", interval="5minute", span="day")
            vix_data = get_historical_data("VIX", interval="5minute", span="day")
            
            current_vix = float(vix_data['close'][-1]) if vix_data['close'] else 20.0
            volatility = "high" if current_vix > 25 else "medium" if current_vix > 15 else "low"
            
            spy_change = ((float(spy_data['close'][-1]) / float(spy_data['open'][0])) - 1) * 100
            qqq_change = ((float(qqq_data['close'][-1]) / float(qqq_data['open'][0])) - 1) * 100
            
            market_trend = "bullish" if spy_change > 0.5 and qqq_change > 0.5 else \
                          "bearish" if spy_change < -0.5 and qqq_change < -0.5 else "neutral"
            
            sectors = {
                "XLK": "Technology",
                "XLF": "Financial",
                "XLE": "Energy",
                "XLV": "Healthcare",
                "XLP": "Consumer Staples"
            }
            
            sector_performance = {}
            for symbol, sector in sectors.items():
                try:
                    sector_data = get_historical_data(symbol, interval="5minute", span="day")
                    if sector_data['close']:
                        perf = ((float(sector_data['close'][-1]) / float(sector_data['open'][0])) - 1) * 100
                        sector_performance[sector] = {
                            "performance": perf,
                            "trend": "up" if perf > 0 else "down"
                        }
                except Exception:
                    continue
            
            return {
                "market_status": market_status,
                "volatility": volatility,
                "market_trend": market_trend,
                "indices": {
                    "SPY": {"change": spy_change},
                    "QQQ": {"change": qqq_change},
                    "VIX": {"value": current_vix}
                },
                "sector_performance": sector_performance,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error(f"Error getting market conditions: {str(e)}")
            return {
                "market_status": market_status,
                "volatility": "unknown",
                "market_trend": "unknown",
                "error": str(e)
            }

    def _build_analysis_prompt(self, context: Dict) -> str:
        return f"""
        As an expert trading advisor, analyze the following market context and provide detailed trading recommendations.
        
        CONTEXT:
        {json.dumps(context, indent=2)}
        
        EVALUATION CRITERIA:
        1. Portfolio Analysis:
           - Current positions and their performance
           - Portfolio diversification across sectors
           - Risk concentration in specific sectors/stocks
        
        2. Market Conditions:
           - Overall market trend and sentiment
           - Sector-specific performance
           - Volatility indicators and risk levels
        
        3. Risk Management:
           - Position sizing relative to portfolio
           - Market volatility considerations
           - Sector exposure limits
        
        4. Technical Factors:
           - Price momentum and trends
           - Volume analysis
           - Market volatility impact
        
        RESPONSE FORMAT:
        Provide recommendations in JSON format with the following structure:
        {{
            "recommendations": [
                {{
                    "symbol": "TICKER",              // Stock symbol (required)
                    "decision": "buy/sell/hold",     // Trading decision (required)
                    "quantity": 100,                 // Number of shares (optional)
                    "price_target": 150.00,         // Target price (required for buy/sell)
                    "confidence": 0.85,             // Confidence score 0-1 (required)
                    "reasoning": "Detailed analysis" // Explanation (required)
                }}
            ],
            "market_outlook": "bullish/bearish/neutral",
            "risk_level": "low/medium/high"
        }}
        
        Note: Ensure confidence scores reflect thorough analysis and avoid speculative recommendations.
        Prioritize risk management and portfolio balance in your decisions.
        """
    def _parse_ai_response(self, response: Dict) -> Dict[str, TradingDecision]:
        decisions = {}
        
        if not isinstance(response, dict) or "recommendations" not in response:
            raise ValueError("Invalid AI response format")
            
        for rec in response["recommendations"]:
            try:
                decisions[rec["symbol"]] = TradingDecision(
                    symbol=rec["symbol"],
                    decision=DecisionType(rec["decision"].lower()),
                    quantity=rec.get("quantity"),
                    price_target=rec.get("price_target"),
                    confidence=rec["confidence"],
                    reasoning=rec["reasoning"]
                )
            except Exception as e:
                error(f"Failed to parse recommendation: {str(e)}")
                continue
                
        return decisions

def make_trading_decisions(ai_provider: str = "openai") -> Dict[str, TradingDecision]:
    """Make trading decisions using the specified AI provider.
    
    Args:
        ai_provider: Name of AI provider ('openai' or other supported providers)
        
    Returns:
        Dictionary of trading decisions keyed by symbol
    """
    engine = TradingDecisionEngine(ai_provider=AIProvider(ai_provider.lower()))
    return engine.analyze_market()
            
