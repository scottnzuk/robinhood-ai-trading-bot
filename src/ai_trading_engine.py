"""
Enhanced AI trading engine with dynamic prompts and feedback loops.
"""
import json
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import asyncio

from src.strategy_framework import Strategy, Signal, SignalType, AIStrategy
from src.exceptions import InvalidAIResponseError, AIProviderError
from src.validation import AIResponseValidator
from src.models.phi_model import PhiModel


@dataclass
class MarketRegime:
    """Market regime classification"""
    volatility: str = "medium"  # low, medium, high
    trend: str = "neutral"  # bullish, bearish, neutral, choppy
    liquidity: str = "normal"  # tight, normal, abundant
    sentiment: str = "neutral"  # bullish, bearish, neutral, fearful, greedy
    correlation: str = "normal"  # high, normal, low
    
    @property
    def is_high_risk(self) -> bool:
        """Check if current regime is high risk"""
        return (
            self.volatility == "high" or
            self.sentiment in ["fearful", "greedy"] or
            self.liquidity == "tight"
        )
    
    @property
    def is_trending(self) -> bool:
        """Check if market is in a strong trend"""
        return self.trend in ["bullish", "bearish"]


@dataclass
class TradingPerformance:
    """Trading performance metrics"""
    win_rate: float = 0.0
    avg_profit_loss: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    profitable_trades: int = 0
    recent_trades: List[Dict[str, Any]] = field(default_factory=list)


class AITradingEngine:
    """Enhanced AI trading engine with dynamic prompts and feedback loops"""
    
    def __init__(self, ai_client, model: str = "gpt-4", use_ensemble: bool = False):
        self.ai_client = ai_client
        self.model = model
        self.use_ensemble = use_ensemble
        self.validator = AIResponseValidator()
        self.market_regime = MarketRegime()
        self.performance = TradingPerformance()
        self.prompt_templates = self._load_prompt_templates()
        self.last_analysis_time = None
        self.analysis_cache = {}
        self.analysis_cache_ttl = 15  # minutes
        
        # Initialize phi model if using ensemble
        self.phi_model = None
        if use_ensemble:
            self.phi_model = PhiModel()
            # Don't initialize immediately to avoid loading model until needed
            
        # Model weights for ensemble
        self.model_weights = {
            "primary": 0.7,  # Primary model (OpenAI)
            "phi": 0.3     # Phi model
        }
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates from files or use defaults"""
        templates = {}
        
        # Default base template
        templates["base"] = """
You are an expert financial advisor and algorithmic trading strategist.

Your task is to analyze the following market context and provide **step-by-step reasoning** before delivering **precise, actionable trading recommendations**.

---

### CONTEXT:
{context}

---

### GUIDELINES:

- **Think step-by-step** to ensure logical, well-supported conclusions.
- **Avoid hallucinations**: Do not invent data or make unsupported assumptions.
- If uncertain, **explicitly state uncertainty** rather than guessing.
- Use **domain-specific financial terminology**.
- Be **concise yet thorough**.
- Prioritize **risk management** and **portfolio diversification**.
- Remember prior context and maintain consistency if multi-turn.
- Format your output **strictly as specified** below.

---

### RESPONSE FORMAT:

Provide your recommendations in **valid JSON** with this structure:

{
    "recommendations": [
        {
            "symbol": "TICKER",              // Stock symbol (required)
            "decision": "buy/sell/hold",     // Trading decision (required)
            "quantity": 100,                 // Number of shares (optional)
            "price_target": 150.00,          // Target price (required for buy/sell)
            "confidence": 0.85,              // Confidence score 0-1 (required)
            "reasoning": "Detailed analysis" // Explanation (required)
        }
    ]
}
"""
        
        # High volatility template
        templates["high_volatility"] = """
IMPORTANT: The market is currently experiencing HIGH VOLATILITY.

In high volatility environments:
- Reduce position sizes by 30-50%
- Focus on defensive sectors (utilities, consumer staples)
- Consider partial profit taking on existing positions
- Implement tighter stop losses
- Avoid highly leveraged positions
"""
        
        # Bearish trend template
        templates["bearish"] = """
IMPORTANT: The market is currently in a BEARISH TREND.

In bearish environments:
- Focus on defensive positions and reduced exposure
- Look for short opportunities in weak sectors
- Consider hedging strategies
- Prioritize capital preservation
- Be selective with long positions, focusing on value and quality
"""
        
        # Bullish trend template
        templates["bullish"] = """
IMPORTANT: The market is currently in a BULLISH TREND.

In bullish environments:
- Focus on growth sectors with momentum
- Consider increasing position sizes for high-conviction trades
- Look for breakout opportunities
- Monitor for signs of excessive optimism
- Maintain trailing stops to protect profits
"""
        
        # Poor performance template
        templates["poor_performance"] = """
IMPORTANT: Recent trading performance has been BELOW EXPECTATIONS.

Given recent performance:
- Reassess your current positions critically
- Focus on higher probability setups with stronger confirmation
- Reduce position sizes temporarily
- Consider more defensive positioning
- Be especially careful with new positions
"""
        
        return templates
    
    def _build_dynamic_prompt(
        self, 
        context: Dict[str, Any],
        market_regime: MarketRegime,
        performance: TradingPerformance
    ) -> str:
        """Build a dynamic prompt based on market conditions and performance"""
        prompt = self.prompt_templates["base"]
        
        # Add regime-specific guidance
        if market_regime.volatility == "high":
            prompt = self.prompt_templates["high_volatility"] + "\n\n" + prompt
        
        if market_regime.trend == "bearish":
            prompt = self.prompt_templates["bearish"] + "\n\n" + prompt
        elif market_regime.trend == "bullish":
            prompt = self.prompt_templates["bullish"] + "\n\n" + prompt
        
        # Add performance-based guidance
        if performance.win_rate < 0.4 and performance.total_trades > 10:
            prompt = self.prompt_templates["poor_performance"] + "\n\n" + prompt
        
        # Format the context as JSON
        context_json = json.dumps(context, indent=2)
        prompt = prompt.replace("{context}", context_json)
        
        return prompt
    
    def _detect_market_regime(self, market_data: Dict[str, Any]) -> MarketRegime:
        """Detect current market regime from market data"""
        regime = MarketRegime()
        
        # Extract key market indicators
        vix = market_data.get("vix", {}).get("last_price", 20.0)
        spy_change = market_data.get("spy", {}).get("percent_change", 0.0)
        sector_performance = market_data.get("sector_performance", {})
        
        # Determine volatility regime
        if vix > 30:
            regime.volatility = "high"
        elif vix < 15:
            regime.volatility = "low"
        else:
            regime.volatility = "medium"
        
        # Determine trend regime
        if spy_change > 1.0:
            regime.trend = "bullish"
        elif spy_change < -1.0:
            regime.trend = "bearish"
        elif -0.3 <= spy_change <= 0.3:
            regime.trend = "neutral"
        else:
            # Check if sectors are moving in different directions
            up_sectors = sum(1 for perf in sector_performance.values() if perf.get("percent_change", 0) > 0)
            down_sectors = sum(1 for perf in sector_performance.values() if perf.get("percent_change", 0) < 0)
            
            if up_sectors > 0 and down_sectors > 0:
                regime.trend = "choppy"
            elif up_sectors > down_sectors:
                regime.trend = "bullish"
            else:
                regime.trend = "bearish"
        
        # Determine sentiment (simplified)
        fear_greed = market_data.get("fear_greed_index", 50)
        if fear_greed > 70:
            regime.sentiment = "greedy"
        elif fear_greed < 30:
            regime.sentiment = "fearful"
        else:
            regime.sentiment = "neutral"
        
        return regime
    
    async def analyze_market_async(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously analyze market data and generate trading recommendations"""
        # Check cache first
        cache_key = str(hash(str(context)))
        if cache_key in self.analysis_cache:
            cache_entry = self.analysis_cache[cache_key]
            cache_time = cache_entry.get("timestamp")
            if cache_time:
                time_diff = (datetime.now(timezone.utc) - cache_time).total_seconds() / 60
                if time_diff < self.analysis_cache_ttl:
                    return cache_entry.get("result", {})
        
        # Detect market regime
        self.market_regime = self._detect_market_regime(context.get("market_data", {}))
        
        # Build dynamic prompt
        prompt = self._build_dynamic_prompt(context, self.market_regime, self.performance)
        
        try:
            if self.use_ensemble:
                # Use ensemble of models
                result = await self._analyze_with_ensemble(context, prompt)
            else:
                # Use single model
                result = await self._analyze_with_primary_model(prompt)
            
            # Cache the result
            self.analysis_cache[cache_key] = {
                "timestamp": datetime.now(timezone.utc),
                "result": result
            }
            
            return result
            
        except Exception as e:
            raise AIProviderError(f"Error calling AI provider: {str(e)}")

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import cachetools

# Simple in-memory TTL cache for AI responses
        stream=True,
_ai_cache = cachetools.TTLCache(maxsize=1000, ttl=300)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)

















    async def _analyze_with_primary_model(self, prompt: str) -> Dict[str, Any]:
        """Analyze market data using the primary AI model"""
        try:
            response_json = await self.ai_client.get_chat_completion(
                prompt,
                model=self.model,
                temperature=0.2,
                max_tokens=1000
            )
            result_text = response_json["choices"][0]["message"]["content"]
        except Exception:
            # Default fallback
            result_text = "{\"recommendations\": []}"

        # Extract and validate JSON
        result = self.validator.extract_and_validate_json(result_text)
        return result
    
    async def _analyze_with_ensemble(self, context: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Analyze market data using an ensemble of AI models"""
        results = {}
        weights = {}
        
        # Get primary model results
        try:
            primary_result = await self._analyze_with_primary_model(prompt)
            if primary_result and "recommendations" in primary_result:
                results["primary"] = primary_result
                weights["primary"] = self.model_weights["primary"]
        except Exception as e:
            print(f"Error with primary model: {str(e)}")
        
        # Get phi model results
        try:
            if self.phi_model is None:
                self.phi_model = PhiModel()
                self.phi_model.initialize()
            
            phi_result = self.phi_model.analyze_market(context)
            if phi_result and "recommendations" in phi_result:
                results["phi"] = phi_result
                weights["phi"] = self.model_weights["phi"]
        except Exception as e:
            print(f"Error with phi model: {str(e)}")
        
        # Combine results
        if not results:
            return {"recommendations": []}
        
        return self._combine_model_results(results, weights)
    
    def _combine_model_results(self, results: Dict[str, Dict[str, Any]], weights: Dict[str, float]) -> Dict[str, Any]:
        """Combine results from multiple models using weighted ensemble"""
        combined_recommendations = {}
        total_weight = sum(weights.values())
        
        # Normalize weights
        if total_weight > 0:
            norm_weights = {k: v/total_weight for k, v in weights.items()}
        else:
            return {"recommendations": []}
        
        # Process each model's recommendations
        for model_name, result in results.items():
            model_weight = norm_weights[model_name]
            for rec in result.get("recommendations", []):
                symbol = rec.get("symbol")
                if not symbol:
                    continue
                
                if symbol not in combined_recommendations:
                    combined_recommendations[symbol] = {
                        "symbol": symbol,
                        "decisions": {"buy": 0.0, "sell": 0.0, "hold": 0.0},
                        "confidence": 0.0,
                        "reasoning": []
                    }
                
                # Add weighted decision
                decision = rec.get("decision", "hold").lower()
                confidence = float(rec.get("confidence", 0.5))
                weighted_confidence = confidence * model_weight
                
                if decision in combined_recommendations[symbol]["decisions"]:
                    combined_recommendations[symbol]["decisions"][decision] += weighted_confidence
                
                # Track reasoning
                reasoning = rec.get("reasoning", "")
                if reasoning:
                    combined_recommendations[symbol]["reasoning"].append(
                        f"[{model_name.upper()}]: {reasoning}"
                    )
        
        # Create final recommendations
        final_recommendations = []
        for symbol, data in combined_recommendations.items():
            # Find decision with highest weight
            decisions = data["decisions"]
            max_decision = max(decisions.items(), key=lambda x: x[1])
            decision_type = max_decision[0]
            confidence = max_decision[1]
            
            # Only include if confidence exceeds threshold
            if confidence > 0.2:
                final_recommendations.append({
                    "symbol": symbol,
                    "decision": decision_type,
                    "confidence": confidence,
                    "reasoning": " | ".join(data["reasoning"])
                })
        
        return {"recommendations": final_recommendations}
    
    def _parse_ai_recommendations(self, response: Dict[str, Any]) -> Dict[str, Signal]:
        """Parse AI recommendations into trading signals"""
        signals = {}
        
        recommendations = response.get("recommendations", [])
        if not recommendations:
            return signals
        
        for rec in recommendations:
            symbol = rec.get("symbol")
            decision = rec.get("decision", "").lower()
            confidence = float(rec.get("confidence", 0.5))
            reasoning = rec.get("reasoning", "")
            
            if not symbol or not decision:
                continue
            
            # Convert decision to signal type
            if decision == "buy":
                signal_type = SignalType.BUY
            elif decision == "sell":
                signal_type = SignalType.SELL
            else:
                signal_type = SignalType.HOLD
            
            signals[symbol] = Signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                source="ai_trading_engine",
                metadata={
                    "reasoning": reasoning,
                    "price_target": rec.get("price_target"),
                    "suggested_quantity": rec.get("quantity")
                }
            )
        
        return signals
    
    def _update_performance(self, trade_results: List[Dict[str, Any]]) -> None:
        """Update performance metrics based on trade results"""
        if not trade_results:
            return
        
        # Add to recent trades
        self.performance.recent_trades.extend(trade_results)
        
        # Keep only the last 100 trades
        if len(self.performance.recent_trades) > 100:
            self.performance.recent_trades = self.performance.recent_trades[-100:]
        
        # Calculate metrics
        total_trades = len(self.performance.recent_trades)
        if total_trades == 0:
            return
            
        profitable_trades = sum(1 for trade in self.performance.recent_trades if trade.get("profit", 0) > 0)
        win_rate = profitable_trades / total_trades
        
        # Calculate average profit/loss
        total_pnl = sum(trade.get("profit", 0) for trade in self.performance.recent_trades)
        avg_pnl = total_pnl / total_trades
        
        # Update performance metrics
        self.performance.total_trades = total_trades
        self.performance.profitable_trades = profitable_trades
        self.performance.win_rate = win_rate
        self.performance.avg_profit_loss = avg_pnl
        
        # Simplified Sharpe ratio calculation
        if total_trades > 5:
            returns = [trade.get("return_pct", 0) for trade in self.performance.recent_trades]
            mean_return = sum(returns) / len(returns)
            std_dev = (sum((r - mean_return) ** 2 for r in returns) / len(returns)) ** 0.5
            
            if std_dev > 0:
                self.performance.sharpe_ratio = mean_return / std_dev
    
    async def analyze_market(
        self, 
        market_data: Dict[str, Any], 
        portfolio: Dict[str, Any]
    ) -> Dict[str, Signal]:
        """Analyze market and generate trading signals"""
        context = {
            "market_data": market_data,
            "portfolio": portfolio,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        result = await self.analyze_market_async(context)
        signals = self._parse_ai_recommendations(result)
        
        return signals
    
    def feedback_loop(self, trade_results: List[Dict[str, Any]]) -> None:
        """Process trade results to improve future recommendations"""
        self._update_performance(trade_results)


    def _combine_model_results(self, results: Dict[str, Dict[str, Any]], weights: Dict[str, float]) -> Dict[str, Any]:
        """Combine results from multiple models using weighted ensemble"""
        combined_recommendations = {}
        total_weight = sum(weights.values())
        
        # Normalize weights
        if total_weight > 0:
            norm_weights = {k: v/total_weight for k, v in weights.items()}
        else:
            return {"recommendations": []}
        
        # Process each model's recommendations
        for model_name, result in results.items():
            model_weight = norm_weights[model_name]
            for rec in result.get("recommendations", []):
                symbol = rec.get("symbol")
                if not symbol:
                    continue
                
                if symbol not in combined_recommendations:
                    combined_recommendations[symbol] = {
                        "symbol": symbol,
                        "decisions": {"buy": 0.0, "sell": 0.0, "hold": 0.0},
                        "confidence": 0.0,
                        "reasoning": []
                    }
                
                # Add weighted decision
                decision = rec.get("decision", "hold").lower()
                confidence = float(rec.get("confidence", 0.5))
                weighted_confidence = confidence * model_weight
                
                if decision in combined_recommendations[symbol]["decisions"]:
                    combined_recommendations[symbol]["decisions"][decision] += weighted_confidence
                
                # Track reasoning
                reasoning = rec.get("reasoning", "")
                if reasoning:
                    combined_recommendations[symbol]["reasoning"].append(
                        f"[{model_name.upper()}]: {reasoning}"
                    )
        
        # Create final recommendations
        final_recommendations = []
        for symbol, data in combined_recommendations.items():
            # Find decision with highest weight
            decisions = data["decisions"]
            max_decision = max(decisions.items(), key=lambda x: x[1])
            decision_type = max_decision[0]
            confidence = max_decision[1]
            
            # Only include if confidence exceeds threshold
            if confidence > 0.2:
                final_recommendations.append({
                    "symbol": symbol,
                    "decision": decision_type,
                    "confidence": confidence,
                    "reasoning": " | ".join(data["reasoning"])
                })
        
        return {"recommendations": final_recommendations}


class AITradingStrategy(AIStrategy):
    """AI-based trading strategy using the AITradingEngine"""
    
    def __init__(self, ai_client, model: str = "gpt-4", use_ensemble: bool = False):
        super().__init__("custom", {"model": model, "use_ensemble": use_ensemble})
        self.engine = AITradingEngine(ai_client, model, use_ensemble)
    
    async def generate_signals(self, data: Dict[str, Any]) -> List[Signal]:
        """Generate trading signals using AI analysis"""
        market_data = data.get("market_data", {})
        portfolio = data.get("portfolio", {})
        
        signals_dict = await self.engine.analyze_market(market_data, portfolio)
        return list(signals_dict.values())
    
    def get_required_data(self) -> List[str]:
        """AI strategies need market data and portfolio information"""
        return ["market_data", "portfolio"]
