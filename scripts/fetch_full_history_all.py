import os
import time
import ccxt
import requests
import json
from datetime import datetime

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "3d", "1w", "1M"]
EXCHANGES = ["binance", "coinbasepro", "kraken", "bitfinex", "bybit", "kucoin", "okx"]

def fetch_candles(exchange, symbol, timeframe, limit=2000):
    since = None
    all_candles = []
    while True:
        candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        if not candles:
            break
        all_candles.extend(candles)
        if len(candles) < limit:
            break
        since = candles[-1][0] + 1
        time.sleep(exchange.rateLimit / 1000)
    return all_candles

def save_candles(exchange_name, symbol, timeframe, candles):
    safe_symbol = symbol.replace("/", "_")
    filename = f"{DATA_DIR}/{exchange_name}_{safe_symbol}_{timeframe}.json"
    with open(filename, "w") as f:
        json.dump(candles, f)

def fetch_all():
    for ex_name in EXCHANGES:
        try:
            ex = getattr(ccxt, ex_name)({'enableRateLimit': True})
            ex.load_markets()
        except Exception:
            continue
        for symbol in ex.symbols:
            for tf in TIMEFRAMES:
                try:
                    print(f"Fetching {ex_name} {symbol} {tf}")
                    candles = fetch_candles(ex, symbol, tf)
                    save_candles(ex_name, symbol, tf, candles)
                except Exception:
                    continue

def fetch_web3_data():
    # Whale alerts (via Whale Alert API or similar)
    try:
        r = requests.get("https://api.whale-alert.io/v1/transactions?api_key=demo&min_value=500000&currency=usd")
        if r.status_code == 200:
            with open(f"{DATA_DIR}/whale_alerts.json", "w") as f:
                json.dump(r.json(), f)
    except:
        pass

    # Gas fees (Etherscan API or similar)
    try:
        r = requests.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=YourApiKeyToken")
        if r.status_code == 200:
            with open(f"{DATA_DIR}/gas_fees.json", "w") as f:
                json.dump(r.json(), f)
    except:
        pass

    # Wallet flows (Glassnode, Nansen, or other APIs if available)
    # Placeholder: add your own API integration here

if __name__ == "__main__":
    fetch_all()
    fetch_web3_data()