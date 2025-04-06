import asyncio
import pandas as pd
import os
from src.ai_trading_framework.data_ingestion import DataIngestion

async def fetch_and_enrich(symbol):
    ingestion = DataIngestion(config={})
    print(f"Fetching {symbol} daily data from Binance...")
    data = await ingestion.fetch_market_data(symbol, "1d")
    print(f"Fetched {len(data)} candles for {symbol}.")

    csv_path = f"data/crypto/{symbol.replace('/', '')}_1d.csv"
    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    df['return'] = df['close'].pct_change()
    df['volatility'] = df['return'].rolling(window=14).std()

    enriched_path = f"data/crypto/{symbol.replace('/', '')}_1d_enriched.csv"
    df.to_csv(enriched_path, index=False)
    print(f"Saved enriched data to {enriched_path}")

async def main():
    await asyncio.gather(
        fetch_and_enrich("BTC/USDT"),
        fetch_and_enrich("ETH/USDT"),
        fetch_and_enrich("XRP/USDT"),
    )

if __name__ == "__main__":
    asyncio.run(main())