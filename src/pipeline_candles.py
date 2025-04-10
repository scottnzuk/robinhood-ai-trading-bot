import pandas as pd
from src.candle_patterns_talib import detect_patterns
from src.candle_classifier import CandleClassifier

def process_ohlcv(df: pd.DataFrame):
    # Detect candlestick patterns
    df_patterns = detect_patterns(df)

    # Initialize LLM classifier
    clf = CandleClassifier(device="cpu")

    # Run LLM classification for each row
    llm_results = []
    for _, row in df.iterrows():
        label = clf.classify_llm(row['open'], row['close'], row['high'], row['low'])
        llm_results.append(label)
    df_patterns['llm_label'] = llm_results

    # Generate classic signals
    signals = clf.generate_signals(df)
    df_patterns = pd.concat([df_patterns, signals], axis=1)

    return df_patterns