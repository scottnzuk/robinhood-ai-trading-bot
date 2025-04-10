from datetime import datetime, timezone
from typing import Tuple, Optional
from config import (
    MIN_SELLING_AMOUNT_USD,
    MAX_SELLING_AMOUNT_USD,
    MIN_BUYING_AMOUNT_USD,
    MAX_BUYING_AMOUNT_USD
)

def get_ai_amount_guidelines() -> Tuple[Optional[str], Optional[str]]:
    """Generate formatted amount guidelines for AI prompt"""
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

def limit_watchlist_stocks(watchlist_stocks: list, limit: int) -> list:
    """Limit watchlist stocks based on current month rotation"""
    if len(watchlist_stocks) <= limit:
        return watchlist_stocks

    watchlist_stocks = sorted(watchlist_stocks, key=lambda x: x['symbol'])
    current_month = datetime.now(timezone.utc).month
    num_parts = (len(watchlist_stocks) + limit - 1) // limit  # Ceiling division
    part_index = (current_month - 1) % num_parts
    start_index = part_index * limit
    end_index = min(start_index + limit, len(watchlist_stocks))

    return watchlist_stocks[start_index:end_index]

def format_trading_results(results: dict) -> dict:
    """Format trading results for logging/display"""
    return {
        'sold': [f"{r['symbol']} ({r['quantity']})" 
                for r in results.values() 
                if r['decision'] == "sell" and r['result'] == "success"],
        'bought': [f"{r['symbol']} ({r['quantity']})" 
                  for r in results.values() 
                  if r['decision'] == "buy" and r['result'] == "success"],
        'errors': [f"{r['symbol']} ({r['details']})" 
                  for r in results.values() 
                  if r['result'] == "error"]
    }