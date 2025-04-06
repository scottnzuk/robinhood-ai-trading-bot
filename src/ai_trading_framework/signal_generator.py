"""
Signal Generator Module
-----------------------

Combines sentiment, technical, and fundamental features to generate trading signals.

"""

def generate_signals(sentiments, market_data):
    """
    Combine inputs to produce a trading signal.

    Args:
        sentiments (list of str): List of sentiment labels.
        market_data (dict): Market data and fundamentals.

    Returns:
        dict: Signal info including scores and action.
    """
    sentiment_score = sum(
        1 if s == "positive" else -1 if s == "negative" else 0 for s in sentiments
    )
    rsi_score = (market_data.get("rsi", 50) - 50) / 10
    macd_score = market_data.get("macd", 0)
    fundamentals = market_data.get("fundamentals", {})
    pe_score = -1 if fundamentals.get("pe_ratio", 15) > 20 else 1
    earnings_score = 1 if fundamentals.get("earnings_growth", 0) > 0 else -1

    combined_score = (
        sentiment_score + rsi_score + macd_score + pe_score + earnings_score
    )

    signal = "buy" if combined_score > 2 else "sell" if combined_score < -2 else "hold"

    return {
        "sentiment_score": sentiment_score,
        "rsi_score": rsi_score,
        "macd_score": macd_score,
        "pe_score": pe_score,
        "earnings_score": earnings_score,
        "combined_score": combined_score,
        "signal": signal,
    }