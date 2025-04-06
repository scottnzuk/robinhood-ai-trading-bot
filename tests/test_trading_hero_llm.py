import unittest
from src.ai_trading_framework import trading_hero_llm

class TestTradingHeroLLM(unittest.TestCase):
    def test_predict_sentiment(self):
        samples = {
            "Market analysts predict a stable outlook for the coming weeks.": "neutral",
            "Investor sentiment improved following news of a potential trade deal.": "positive",
            "The company reported a significant loss in the last quarter.": "negative",
        }
        for text, expected in samples.items():
            pred = trading_hero_llm.predict_sentiment(text)
            print(f"Input: {text}\nPredicted: {pred}\nExpected: {expected}\n")
            self.assertEqual(pred, expected)

if __name__ == "__main__":
    unittest.main()