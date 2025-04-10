import pandas as pd
from src.candle_patterns_talib import detect_patterns
from src.strategies import MovingAverageCrossStrategy, RSIStrategy
from src.candle_llm_gen import CandleGen

def process_ohlcv(df: pd.DataFrame):
    # Detect candlestick patterns (TA-Lib)
    df_patterns = detect_patterns(df)

    # Classic signals
    strat = MovingAverageCrossStrategy(df)
    signals_ma = strat.generate_signals()
    strat_rsi = RSIStrategy(df)
    signals_rsi = strat_rsi.generate_signals()
    df_patterns['ma_signal'] = signals_ma['signal']
    df_patterns['rsi_signal'] = signals_rsi['signal']

    # LLM candle classification
    llm = CandleGen(device="cpu")
    llm_labels = []
    for _, row in df.iterrows():
        label = llm.classify("identify candle", f"open:{row['open']},close:{row['close']},high:{row['high']},low:{row['low']}")
        llm_labels.append(label)
    df_patterns['llm_label'] = llm_labels

    return df_patterns