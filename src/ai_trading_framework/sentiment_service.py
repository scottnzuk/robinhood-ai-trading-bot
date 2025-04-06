"""
Sentiment Service Module
------------------------

Wraps Trading-Hero-LLM for batch or streaming sentiment analysis.
"""

from src.ai_trading_framework import trading_hero_llm

def analyze_sentiments(texts):
    """
    Analyze a list of text inputs and return sentiment labels.

    Args:
        texts (list of str): Input sentences or paragraphs.

    Returns:
        list of str: Sentiment labels ('neutral', 'positive', 'negative').
    """
    return [trading_hero_llm.predict_sentiment(text) for text in texts]