import asyncio
from typing import Dict, Any, List, Optional, Protocol
import time
import random


class MarketDataFetcher(Protocol):
    async def fetch(self, symbol: str, timeframe: str) -> List[Dict]:
        ...


class AltDataFetcher(Protocol):
    async def fetch(self, query: Optional[str] = None) -> List[Dict]:
        ...


class OnChainDataFetcher(Protocol):
    async def fetch(self, asset: str) -> Dict:
        ...


class CCXTMarketFetcher:
    """
    Example market data fetcher using ccxt (mocked here).
    """
    async def fetch(self, symbol: str, timeframe: str) -> List[Dict]:
        # Simulate API latency
        await asyncio.sleep(0.1)
        now = int(time.time() * 1000)
        # Return dummy OHLCV data
        return [{
            "timestamp": now,
            "symbol": symbol,
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 102.0,
            "volume": 1234.5
        }]


class DummyAltDataFetcher:
    """
    Example alternative data fetcher (news/sentiment).
    """
    async def fetch(self, query: Optional[str] = None) -> List[Dict]:
        await asyncio.sleep(0.1)
        now = int(time.time() * 1000)
        sentiment = random.uniform(-1, 1)
        return [{
            "timestamp": now,
            "source": "twitter",
            "sentiment_score": sentiment,
            "headline": f"Simulated news for {query or 'market'}"
        }]


class DummyOnChainDataFetcher:
    """
    Example on-chain data fetcher.
    """
    async def fetch(self, asset: str) -> Dict:
        await asyncio.sleep(0.1)
        now = int(time.time() * 1000)
        return {
            "timestamp": now,
            "asset": asset,
            "active_addresses": random.randint(1000, 100000),
            "tx_volume": random.uniform(100.0, 10000.0)
        }


class DataIngestion:
    """
    Async data ingestion module.
    Fetches market data, alternative data (news, sentiment), and on-chain data.
    Supports both streaming (WebSockets) and REST polling.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with API keys, endpoints, and asset configs.
        """
        self.config = config
        # Initialize fetchers
        self.market_fetcher: MarketDataFetcher = CCXTMarketFetcher()
        self.alt_fetcher: AltDataFetcher = DummyAltDataFetcher()
        self.onchain_fetcher: OnChainDataFetcher = DummyOnChainDataFetcher()

    async def fetch_market_data(self, symbol: str, timeframe: str) -> List[Dict]:
        """
        Fetch OHLCV and order book data for a symbol.
        """
        try:
            data = await self.market_fetcher.fetch(symbol, timeframe)
            return data
        except Exception as e:
            # Log error
            print(f"[Error] fetch_market_data: {e}")
            return []

    async def fetch_alt_data(self, query: Optional[str] = None) -> List[Dict]:
        """
        Fetch alternative data like news sentiment and social media.
        """
        try:
            data = await self.alt_fetcher.fetch(query)
            return data
        except Exception as e:
            print(f"[Error] fetch_alt_data: {e}")
            return []

    async def fetch_onchain_data(self, asset: str) -> Dict:
        """
        Fetch on-chain metrics for a crypto asset.
        """
        try:
            data = await self.onchain_fetcher.fetch(asset)
            return data
        except Exception as e:
            print(f"[Error] fetch_onchain_data: {e}")
            return {}

    async def stream_data(self):
        """
        Main async loop to continuously fetch and update data.
        """
        while True:
            try:
                market = await self.fetch_market_data("BTC/USDT", "1m")
                alt = await self.fetch_alt_data("bitcoin")
                onchain = await self.fetch_onchain_data("BTC")
                print(f"[Market] {market}")
                print(f"[Alt] {alt}")
                print(f"[OnChain] {onchain}")
            except Exception as e:
                print(f"[Error] stream_data loop: {e}")
            await asyncio.sleep(1)