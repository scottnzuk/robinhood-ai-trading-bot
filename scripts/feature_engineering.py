import pandas as pd
import ta  # Technical Analysis library
import os

def main():
    csv_path = "data/crypto/BTCUSDT_1d_enriched.csv"
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)

    # Add SMA and EMA
    df['sma_14'] = df['close'].rolling(window=14).mean()
    df['ema_14'] = df['close'].ewm(span=14, adjust=False).mean()

    # Add RSI
    df['rsi_14'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

    # Add MACD
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()

    # Save features
    out_path = "data/crypto/BTCUSDT_1d_features.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved feature-enhanced data to {out_path}")

if __name__ == "__main__":
    main()