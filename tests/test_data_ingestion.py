import pytest
import asyncio
from src.ai_trading_framework.data_ingestion import DataIngestion


@pytest.mark.asyncio
async def test_fetch_market_data():
    ingestion = DataIngestion(config={})
    data = await ingestion.fetch_market_data("BTC/USDT", "1m")
    assert isinstance(data, list)
    assert len(data) > 0
    item = data[0]
    assert "timestamp" in item
    assert "symbol" in item
    assert "open" in item
    assert "high" in item
    assert "low" in item
    assert "close" in item
    assert "volume" in item


@pytest.mark.asyncio
async def test_fetch_alt_data():
    ingestion = DataIngestion(config={})
    data = await ingestion.fetch_alt_data("bitcoin")
    assert isinstance(data, list)
    assert len(data) > 0
    item = data[0]
    assert "timestamp" in item
    assert "source" in item
    assert "sentiment_score" in item
    assert "headline" in item


@pytest.mark.asyncio
async def test_fetch_onchain_data():
    ingestion = DataIngestion(config={})
    data = await ingestion.fetch_onchain_data("BTC")
    assert isinstance(data, dict)
    assert "timestamp" in data
    assert "asset" in data
    assert "active_addresses" in data
    assert "tx_volume" in data


@pytest.mark.asyncio
async def test_error_handling(monkeypatch):
    ingestion = DataIngestion(config={})

    async def fail_fetch(*args, **kwargs):
        raise RuntimeError("Simulated failure")

    # Patch fetchers to raise errors
    ingestion.market_fetcher.fetch = fail_fetch
    ingestion.alt_fetcher.fetch = fail_fetch
    ingestion.onchain_fetcher.fetch = fail_fetch

    market = await ingestion.fetch_market_data("BTC/USDT", "1m")
    alt = await ingestion.fetch_alt_data("bitcoin")
    onchain = await ingestion.fetch_onchain_data("BTC")

    assert market == []
    assert alt == []
    assert onchain == {}