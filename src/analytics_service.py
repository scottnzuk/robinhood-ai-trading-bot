import asyncio
import polars as pl
from datetime import datetime
from typing import List
from src.databus import AsyncioQueueBus
from src.features_pb2 import FeatureSet, Signal
import onnxruntime as ort

bus = AsyncioQueueBus()  # Or RedisStreamBus()

session = ort.InferenceSession("model.onnx", providers=["CPUExecutionProvider"])

async def feature_extraction(trades: List[dict]) -> FeatureSet:
    df = pl.DataFrame(trades)
    df = df.with_columns([
        pl.col("price").ewm_mean(alpha=0.2).alias("ema_fast"),
        pl.col("price").ewm_mean(alpha=0.05).alias("ema_slow"),
        pl.col("price").std().alias("volatility")
    ])
    fdict = df.tail(1).to_dicts()[0]
    feature_msg = FeatureSet(
        symbol=fdict["symbol"],
        ema_fast=fdict["ema_fast"],
        ema_slow=fdict["ema_slow"],
        volatility=fdict["volatility"],
        timestamp_ms=int(datetime.utcnow().timestamp() * 1000)
    )
    return feature_msg

async def ai_inference(features: FeatureSet) -> Signal:
    inputs = {
        "ema_fast": [features.ema_fast],
        "ema_slow": [features.ema_slow],
        "volatility": [features.volatility]
    }
    ort_inputs = {k: v for k, v in inputs.items()}
    ort_outs = session.run(None, ort_inputs)
    action_idx = int(ort_outs[0][0])
    confidence = float(ort_outs[1][0])

    action_map = {0: "hold", 1: "long", 2: "short"}
    signal_msg = Signal(
        symbol=features.symbol,
        action=action_map.get(action_idx, "hold"),
        confidence=confidence,
        expiry_ms=int(datetime.utcnow().timestamp() * 1000) + 60000,
        timestamp_ms=int(datetime.utcnow().timestamp() * 1000)
    )
    return signal_msg

async def analytics_worker():
    trade_buffer = []
    async for msg_bytes in bus.subscribe("trades"):
        feature = FeatureSet()
        feature.ParseFromString(msg_bytes)
        trade_buffer.append({
            "symbol": feature.symbol,
            "price": feature.ema_fast,  # use ema_fast as proxy price for now
            "ema_fast": feature.ema_fast,
            "ema_slow": feature.ema_slow,
            "volatility": feature.volatility
        })
        if len(trade_buffer) >= 100:
            feature_msg = await feature_extraction(trade_buffer)
            signal_msg = await ai_inference(feature_msg)
            await bus.publish("signals", signal_msg.SerializeToString())
            trade_buffer.clear()

if __name__ == "__main__":
    asyncio.run(analytics_worker())