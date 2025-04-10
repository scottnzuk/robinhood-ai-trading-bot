import sys
import os
import asyncio
import time
from datetime import datetime, timezone
import json
from aiocache import Cache
from aiocache.serializers import JsonSerializer

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from src.decorators import RateLimited, rh_api_retry, ai_api_retry
from src.circuit_breaker import CircuitBreakerService, BreakerConfig
from src.trading_utils import get_ai_amount_guidelines, limit_watchlist_stocks, format_trading_results
from src.exceptions import *

from config import (
    MIN_SELLING_AMOUNT_USD,
    MAX_SELLING_AMOUNT_USD,
    MIN_BUYING_AMOUNT_USD,
    MAX_BUYING_AMOUNT_USD,
    PORTFOLIO_LIMIT,
    TRADE_EXCEPTIONS,
    RUN_INTERVAL_SECONDS,
    WATCHLIST_NAMES,
    WATCHLIST_OVERVIEW_LIMIT,
    MODE,
    AI_PROVIDERS,
    RISK_PARAMS,
    AUTOMATION_MODE
)
from src.api import robinhood
from src.api.ai_provider import AIMultiProvider
from src.utils import logger
from src.risk import RiskManager
from src.monitoring import HealthMonitor
from src.patterns import YOLOv8sDetector

# Cache configuration
cache = Cache(
    Cache.MEMORY,
    serializer=JsonSerializer(),
    timeout=10,
    size=1000  # Will auto-evict LRU items when full
)

# Initialize services
health_monitor = HealthMonitor()

# Rate limiters with health monitoring
rh_rate_limiter = RateLimited(calls=60, period=60, priority=1)
ai_rate_limiter = RateLimited(calls=30, period=60, priority=2)
rh_rate_limiter.set_health_monitor(health_monitor)
ai_rate_limiter.set_health_monitor(health_monitor)

# Log initial rate limits
logger.info(f"Initialized rate limiters - Robinhood: {rh_rate_limiter.calls}/min, AI: {ai_rate_limiter.calls}/min")

# Circuit breaker
breaker_service = CircuitBreakerService()
breaker_service.register_endpoint(
    "robinhood_api",
    BreakerConfig(failure_threshold=5, success_threshold=3, timeout_seconds=300)
)
breaker_service.register_endpoint(
    "ai_service",
    BreakerConfig(failure_threshold=3, success_threshold=2, timeout_seconds=180)
)

# Initialize services
ai_provider = AIMultiProvider(AI_PROVIDERS)
risk_manager = RiskManager(RISK_PARAMS)
pattern_detector = YOLOv8sDetector()

# Initialize metrics collection
health_monitor.register_metric('rate_limit_adjustments', 'counter')

@rh_api_retry
@rh_rate_limiter
async def get_account_info():
    cached = await cache.get("account_info")
    if cached:
        return cached
    info = await robinhood.get_account_info()
    await cache.set("account_info", info, ttl=300)
    return info

@rh_api_retry
@rh_rate_limiter
async def get_portfolio_stocks():
    cached = await cache.get("portfolio")
    if cached:
        return cached
    portfolio = await robinhood.get_portfolio_stocks()
    await cache.set("portfolio", portfolio, ttl=60)
    return portfolio

@ai_api_retry
@ai_rate_limiter
async def make_ai_request(prompt):
    return ai_provider.make_request(prompt)

def get_ai_amount_guidelines():
    sell_guidelines = []
    if MIN_SELLING_AMOUNT_USD is not False:
        sell_guidelines.append(f"Minimum amount {MIN_SELLING_AMOUNT_USD} USD")
    if MAX_SELLING_AMOUNT_USD is not False:
        sell_guidelines.append(f"Maximum amount {MAX_SELLING_AMOUNT_USD} USD")
    sell_guidelines = ", ".join(sell_guidelines) if sell_guidelines else None

    buy_guidelines = []
    if MIN_BUYING_AMOUNT_USD is not False:
        buy_guidelines.append(f"Minimum amount {MIN_BUYING_AMOUNT_USD} USD")
    if MAX_BUYING_AMOUNT_USD is not False:
        buy_guidelines.append(f"Maximum amount {MAX_BUYING_AMOUNT_USD} USD")
    buy_guidelines = ", ".join(buy_guidelines) if buy_guidelines else None

    return sell_guidelines, buy_guidelines

def make_ai_decisions(account_info, portfolio_overview, watchlist_overview):
    # Get pattern detection signals
    pattern_signals = pattern_detector.detect(portfolio_overview.keys())
    
    constraints = [
        f"- Initial budget: {account_info['buying_power']} USD",
        f"- Max portfolio size: {PORTFOLIO_LIMIT} stocks",
        f"- Risk tolerance: {RISK_PARAMS['risk_tolerance']}",
        *[f"- Pattern detected for {sym}: {pat}" for sym, pat in pattern_signals.items()]
    ]
    
    sell_guidelines, buy_guidelines = get_ai_amount_guidelines()
    if sell_guidelines:
        constraints.append(f"- Sell Amounts Guidelines: {sell_guidelines}")
    if buy_guidelines:
        constraints.append(f"- Buy Amounts Guidelines: {buy_guidelines}")
    if TRADE_EXCEPTIONS:
        constraints.append(f"- Excluded stocks: {', '.join(TRADE_EXCEPTIONS)}")

    ai_prompt = (
        "**Context:**\n"
        f"Today is {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}.{chr(10)}"
        f"You are a short-term investment advisor managing a stock portfolio.{chr(10)}"
        f"You analyze market conditions every {RUN_INTERVAL_SECONDS} seconds and make investment decisions.{chr(10)}{chr(10)}"
        "**Constraints:**\n"
        f"{chr(10).join(constraints)}"
        "\n\n"
        "**Stock Data:**\n"
        "```json\n"
        f"{json.dumps({**portfolio_overview, **watchlist_overview}, indent=1)}{chr(10)}"
        "```\n\n"
        "**Response Format:**\n"
        "Return your decisions in a JSON array with this structure:\n"
        "```json\n"
        "[\n"
        '  {"symbol": <symbol>, "decision": <decision>, "quantity": <quantity>},\n'
        "  ...\n"
        "]\n"
        "```\n"
        "- <symbol>: Stock symbol.\n"
        "- <decision>: One of `buy`, `sell`, or `hold`.\n"
        "- <quantity>: Recommended transaction quantity.\n\n"
        "**Instructions:**\n"
        "- Provide only the JSON output with no additional text.\n"
        "- Return an empty array if no actions are necessary."
    )
    
    logger.debug(f"AI making-decisions prompt:{chr(10)}{ai_prompt}")
    from src.validation import AIResponseValidator
    
    ai_response = make_ai_request(ai_prompt)
    logger.debug(f"AI making-decisions response:{chr(10)}{ai_response}")
    decisions = ai_provider.parse_response(ai_response)
    portfolio_symbols = list(portfolio_overview.keys())
    validated_decisions = AIResponseValidator.full_validation(decisions, portfolio_symbols)
    return validated_decisions

async def main():
    robinhood_token_expiry = 0
    
    # Skip confirmation if in full automation mode
    if AUTOMATION_MODE != "full" and input("Run bot? (yes/no): ").lower() != "yes":
        logger.warning("Execution cancelled by user")
        return

    while True:
        try:
            if breaker_service.check("main_loop"):
                logger.warning("Circuit breaker active - skipping iteration")
                await asyncio.sleep(60)
                continue
                
            # Token refresh
            if time.time() >= robinhood_token_expiry - 300:
                try:
                    login_resp = await robinhood.login_to_robinhood()
                    if not login_resp or 'expires_in' not in login_resp:
                        raise APIEndpointError("robinhood/auth", 500, "Invalid login response")
                    robinhood_token_expiry = time.time() + login_resp['expires_in']
                    breaker_service.record_success("robinhood_api")
                except Exception as e:
                    breaker_service.record_failure("robinhood_api")
                    raise

            if robinhood.is_market_open():
                try:
                    trading_results = await execute_trading_cycle()
                    health_monitor.record_iteration(
                        success=all(r['result'] in ('success', 'cancelled')
                        for r in trading_results.values()
                    ))
                    
                    if health_monitor.is_unhealthy():
                        breaker_service.record_failure("main_loop")
                    
                    await asyncio.sleep(RUN_INTERVAL_SECONDS)
                except CircuitTrippedError:
                    await asyncio.sleep(60)
                except RateLimitExceededError as e:
                    logger.error(f"Rate limit exceeded: {e}")
                    await asyncio.sleep(60)
                except Exception as e:
                    logger.error(f"Trading cycle error: {e}")
                    breaker_service.record_failure("main_loop")
                    await asyncio.sleep(60)
            else:
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            breaker_service.record_failure("main_loop")
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
