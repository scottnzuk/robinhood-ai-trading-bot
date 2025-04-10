import asyncio
import aiohttp
from datetime import datetime
from typing import List
from pydantic import BaseModel, confloat, Field
from clickhouse_connect import get_client

client = get_client(host='localhost', port=8123, username='default', password='')

class CandleSchema(BaseModel):
    timestamp: datetime
    symbol: str
    open: confloat(gt=0)
    high: confloat(gt=0)
    low: confloat(gt=0)
    close: confloat(gt=0)
    volume: confloat(ge=0)

async def fetch_binance_klines(symbol: str, interval: str, start_time: int, end_time: int) -> List[CandleSchema]:
    url = f"https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000
    }
    candles = []
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                if not data:
                    break
                for c in data:
                    candles.append(CandleSchema(
                        timestamp=datetime.utcfromtimestamp(c[0]/1000),
                        symbol=symbol,
                        open=float(c[1]),
                        high=float(c[2]),
                        low=float(c[3]),
                        close=float(c[4]),
                        volume=float(c[5])
                    ))
                if len(data) < 1000:
                    break
                params["startTime"] = data[-1][0] + 1
    return candles

async def insert_candles(candles: List[CandleSchema]):
    values = [
        (c.timestamp, c.symbol, c.open, c.high, c.low, c.close, c.volume)
        for c in candles
    ]
    client.insert(
        "candles",
        values,
        column_names=["timestamp", "symbol", "open", "high", "low", "close", "volume"]
    )

async def backfill_binance(symbol: str, interval: str, start_time: int, end_time: int):
    candles = await fetch_binance_klines(symbol, interval, start_time, end_time)
    await insert_candles(candles)

if __name__ == "__main__":
    # Example: backfill last 24 hours of BTCUSDT 1m candles
    import time as t
    end = int(t.time() * 1000)
    start = end - 24 * 60 * 60 * 1000
    asyncio.run(backfill_binance("BTCUSDT", "1m", start, end))