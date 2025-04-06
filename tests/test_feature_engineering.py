import pytest
from ai_trading_framework.feature_engineering import FeatureEngineer
import pandas as pd
import numpy as np

@pytest.fixture
def feature_engineer():
    return FeatureEngineer()

def test_normalization(feature_engineer):
    data = {
        'close': np.array([100, 200, 300, 400, 500]),
        'volume': np.array([1000, 2000, 3000, 4000, 5000])
    }
    df = pd.DataFrame(data)
    feature_engineer.fit_scalers({'ohlcv': df})
    normed = feature_engineer.transform({'ohlcv': df})
    expected_close = (df['close'] - df['close'].mean()) / df['close'].std()
    expected_volume = (df['volume'] - df['volume'].mean()) / df['volume'].std()
    pd.testing.assert_series_equal(normed['ohlcv']['close'], expected_close, check_dtype=False)
    pd.testing.assert_series_equal(normed['ohlcv']['volume'], expected_volume, check_dtype=False)

def test_technical_indicators(feature_engineer):
    data = {
        'close': np.array([100, 200, 300, 400, 500]),
        'volume': np.array([1000, 2000, 3000, 4000, 5000])
    }
    df = pd.DataFrame(data)
    df = feature_engineer.compute_technical_indicators(df)
    assert 'ema_20' in df.columns
    assert 'rsi_14' in df.columns
    assert 'macd' in df.columns
    assert 'bollinger_upper' in df.columns
    assert 'bollinger_lower' in df.columns
    assert 'vwap' in df.columns
    # Additional assertions for vwap
    expected_vwap = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    pd.testing.assert_series_equal(df['vwap'], expected_vwap, check_dtype=False)

def test_order_book_features(feature_engineer):
    data = {
        'bid': np.array([100, 200, 300, 400, 500]),
        'ask': np.array([110, 210, 310, 410, 510]),
        'bid_size': np.array([1000, 2000, 3000, 4000, 5000]),
        'ask_size': np.array([900, 1900, 2900, 3900, 4900])
    }
    df = pd.DataFrame(data)
    df = feature_engineer.engineer_order_book_features(df)
    assert 'spread' in df.columns
    assert 'imbalance' in df.columns
    assert df['spread'].equals(np.array([10, 10, 10, 10, 10]))
    # Recalculate imbalance with correct formula
    expected_imbalance = (df['bid_size'] - df['ask_size']) / (df['bid_size'] + df['ask_size'])
    pd.testing.assert_series_equal(df['imbalance'], expected_imbalance, check_dtype=False)

def test_embedding_outputs(feature_engineer):
    sentiment_vecs = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    event_vecs = np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]])
    blockchain_vecs = np.array([[1, 1, 1], [0, 0, 0], [1, 1, 1]])
    sent, event, chain = feature_engineer.embed_sentiment_event_blockchain(sentiment_vecs, event_vecs, blockchain_vecs)
    np.testing.assert_array_equal(sent, sentiment_vecs)
    np.testing.assert_array_equal(event, event_vecs)
    np.testing.assert_array_equal(chain, blockchain_vecs)