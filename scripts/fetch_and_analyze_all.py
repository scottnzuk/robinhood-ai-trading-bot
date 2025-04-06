import asyncio
import pandas as pd
import requests
import os
from src.ai_trading_framework.data_ingestion import DataIngestion

async def fetch_and_enrich(symbol):
    ingestion = DataIngestion(config={})
    print(f"Fetching {symbol} daily data from Binance...")
    try:
        data = await ingestion.fetch_market_data(symbol, "1d")
        print(f"Fetched {len(data)} candles for {symbol}.")
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return

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
    # Fetch all USDT trading pairs
    url = "https://api.binance.com/api/v3/exchangeInfo"
    symbols = []
    try:
        response = requests.get(url)
        data = response.json()
        for s in data['symbols']:
            if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING':
                base = s['baseAsset']
                pair = f"{base}/USDT"
                symbols.append(pair)
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return

    print(f"Found {len(symbols)} USDT pairs.")

    tasks = [fetch_and_enrich(symbol) for symbol in symbols]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())