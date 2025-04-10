import asyncio
import json
import websockets
import time
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field, confloat
from clickhouse_connect import get_client
import pluggy
from prometheus_client import start_http_server, Summary, Gauge, Counter
import logging
from src.pluginspec import IngestionSpec
from src.plugins.anomaly_detector import AnomalyDetectorPlugin
from src.plugins.resilience_plugin import ResiliencePlugin
from src.databus import AsyncioQueueBus

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("ingestion")

# --- Prometheus metrics ---
start_http_server(8000)
ingest_latency = Summary('ingest_latency_seconds', 'Time spent ingesting batches')
queue_size_gauge = Gauge('ingest_queue_size', 'Current ingestion queue size')
trade_counter = Counter('trades_ingested_total', 'Total trades ingested')

# --- Pluggy setup ---
pm = pluggy.PluginManager("ingestion")
pm.add_hookspecs(IngestionSpec)
pm.register(AnomalyDetectorPlugin())
pm.register(ResiliencePlugin())
pm.load_setuptools_entrypoints("ingestion")

# --- Data Bus ---
bus = AsyncioQueueBus()

async def ingestion_pipeline(symbols_binance: List[str], symbols_kraken: List[str]):
    queue = asyncio.Queue(maxsize=10000)
    adapters = [
        BinanceWebSocketAdapter(symbols_binance),
        KrakenWebSocketAdapter(symbols_kraken)
    ]
    await asyncio.gather(*(a.connect() for a in adapters))

    async def produce(adapter):
        async for trade in adapter.listen(queue):
            pass  # adapter.listen pushes to queue internally

    async def consume(consumer_id):
        batch = []
        max_batch = 100
        while True:
            queue_size_gauge.set(queue.qsize())
            trade = await queue.get()
            batch.append(trade)
            trade_counter.inc()
            # Publish to bus
            await bus.publish("trades", trade.dict())
            # Adaptive batch sizing
            if len(batch) >= max_batch or queue.qsize() > 5000:
                start = time.time()
                try:
                    await clickhouse_ingest(batch)
                except Exception as e:
                    logger.error(json.dumps({"event": "ingest_error", "error": str(e)}))
                duration = time.time() - start
                ingest_latency.observe(duration)
                logger.info(json.dumps({
                    "event": "batch_ingested",
                    "consumer": consumer_id,
                    "batch_size": len(batch),
                    "duration_sec": duration
                }))
                # Adjust batch size based on latency
                if duration > 0.5 and max_batch > 10:
                    max_batch = max(10, max_batch // 2)
                elif duration < 0.1 and max_batch < 1000:
                    max_batch = min(1000, max_batch * 2)
                batch.clear()

    consumers = [consume(i) for i in range(4)]  # 4 parallel consumers
    await asyncio.gather(*(produce(a) for a in adapters), *consumers)

# --- Entry point ---
if __name__ == "__main__":
    asyncio.run(ingestion_pipeline(
        symbols_binance=["btcusdt", "ethusdt"],
        symbols_kraken=["XBT/USD", "ETH/USD"]
    ))