import asyncio
import pandas as pd
import os
from src.ai_trading_framework.data_ingestion import DataIngestion

async def main():
    ingestion = DataIngestion(config={})
    print("Fetching BTCUSDT daily data from Binance...")
    data = await ingestion.fetch_market_data("BTC/USDT", "1d")
    print(f"Fetched {len(data)} candles.")

    # Load saved CSV
    csv_path = "data/crypto/BTCUSDT_1d.csv"
    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(df.head())

    # Compute returns and volatility
    df['return'] = df['close'].pct_change()
    df['volatility'] = df['return'].rolling(window=14).std()

    # Save enriched dataset
    enriched_path = "data/crypto/BTCUSDT_1d_enriched.csv"
    df.to_csv(enriched_path, index=False)
    print(f"Saved enriched data to {enriched_path}")

    # Basic insights
    mean_return = df['return'].mean()
    vol = df['volatility'].mean()
    print(f"Mean daily return: {mean_return:.5f}")
    print(f"Average volatility: {vol:.5f}")

if __name__ == "__main__":
    asyncio.run(main())