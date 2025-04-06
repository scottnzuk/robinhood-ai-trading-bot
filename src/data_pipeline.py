import os
import redis.asyncio as redis
import json
import time

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def save_interaction(prompt, response, label=None, feedback=None, metadata=None):
    entry = {
        "timestamp": time.time(),
        "prompt": prompt,
        "response": response,
        "label": label,
        "feedback": feedback,
        "metadata": metadata or {}
    }
    await redis_client.rpush("mcp:data", json.dumps(entry))

async def get_dataset(limit=1000):
    data = await redis_client.lrange("mcp:data", -limit, -1)
    dataset = [json.loads(d) for d in data]
    return dataset

async def export_dataset(filename="dataset.jsonl", limit=10000):
    dataset = await get_dataset(limit)
    with open(filename, "w") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")

async def label_interaction(index_from_end, label):
    """
    Label a specific interaction by index (from end, e.g., -1 is latest)
    """
    data = await redis_client.lindex("mcp:data", index_from_end)
    if not data:
        return False
    item = json.loads(data)
    item["label"] = label
    await redis_client.lset("mcp:data", index_from_end, json.dumps(item))
    return True