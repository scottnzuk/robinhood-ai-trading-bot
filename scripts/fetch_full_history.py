import requests
import pandas as pd
import os
import time

def fetch_full_history(symbol, interval="1d", max_days=1000):
    symbol_clean = symbol.replace("/", "")
    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    end_time = int(time.time() * 1000)  # now in ms

    while True:
        params = {
            "symbol": symbol_clean,
            "interval": interval,
            "limit": 1000,
            "endTime": end_time
        }
        response = requests.get(url, params=params)
        data = response.json()

        if not data:
            break

        all_data = data + all_data  # prepend older data
        first_open_time = data[0][0]

        if len(all_data) >= max_days or len(data) < 1000:
            break

        # Prepare for next loop
        end_time = first_open_time - 1

    # Parse data
    parsed = []
    for d in all_data[-max_days:]:  # limit to max_days
        parsed.append({
            "timestamp": d[0],
            "open": float(d[1]),
            "high": float(d[2]),
            "low": float(d[3]),
            "close": float(d[4]),
            "volume": float(d[5])
        })

    # Save CSV
    os.makedirs("data/crypto", exist_ok=True)
    df = pd.DataFrame(parsed)
    df.to_csv(f"data/crypto/{symbol_clean}_{interval}_full.csv", index=False)
    print(f"Saved {len(df)} candles for {symbol} to {symbol_clean}_{interval}_full.csv")

if __name__ == "__main__":
    # Example usage
    fetch_full_history("BTC/USDT")
    fetch_full_history("ETH/USDT")
    fetch_full_history("XRP/USDT")