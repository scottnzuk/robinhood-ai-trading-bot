"""
Main training loop for adaptive AI trading system.
Fetches data, generates features/signals, updates learner.
"""

import asyncio
import numpy as np
from src.ai_trading_framework.data_ingestion import DataIngestion
from src.ai_trading_framework.feature_pipeline import build_feature_pipeline
from src.ai_trading_framework.signal_generation import SignalGenerator
from src.ai_trading_framework.adaptive_learning import OnlineLearner
from sklearn.linear_model import SGDClassifier
from src.ai_trading_framework.mps_utils import timeout_async, safe_mps_op

@timeout_async(300)
@safe_mps_op
async def main_training_loop():
    config = {}
    ingestion = DataIngestion(config)
    feature_pipeline = build_feature_pipeline()
    signal_generator = SignalGenerator()
    learner = OnlineLearner(SGDClassifier())

    while True:
        # Fetch data asynchronously
        market = await ingestion.fetch_market_data("BTC/USDT", "1h")
        alt = await ingestion.fetch_alt_data("bitcoin")
        onchain = await ingestion.fetch_onchain_data("BTC")

        # Prepare raw data dict
        raw_data = {
            'market': market,
            'sentiment': alt,
            'onchain': [onchain]
        }

        # Transform features
        features = feature_pipeline.transform(raw_data)

        # Generate signals
        signals = signal_generator.generate_signals(features)

        # Generate real labels: future returns over next period
        import pandas as pd
        df_market = pd.DataFrame(market)
        df_market['future_close'] = df_market['close'].shift(-1)
        df_market['future_return'] = (df_market['future_close'] - df_market['close']) / df_market['close']
        threshold = 0.001  # 0.1% threshold
        labels = (df_market['future_return'] > threshold).astype(int).values[:-1]
        signals = signals[:-1]  # align with labels length

        # Update learner
        learner.add_experience((signals, labels))
        learner.update_model()

        # Evaluate performance (accuracy)
        learner.evaluate_performance(signals, labels, metric_fn=lambda y_true, y_pred: (y_true == y_pred).mean())

        print("Training loop iteration complete.")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main_training_loop())