import asyncio
import aioredis
import json
from typing import Any, AsyncGenerator

class AsyncioQueueBus:
    def __init__(self, maxsize=10000):
        self.queue = asyncio.Queue(maxsize=maxsize)

    async def publish(self, topic: str, message_bytes: bytes):
        await self.queue.put((topic, message_bytes))

    async def subscribe(self, topic: str) -> AsyncGenerator[bytes, None]:
        while True:
            t, msg_bytes = await self.queue.get()
            if t == topic:
                yield msg_bytes

class RedisStreamBus:
    def __init__(self, redis_url="redis://localhost", consumer_group="analytics", consumer_name="worker1"):
        self.redis_url = redis_url
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.redis = None

    async def connect(self):
        self.redis = await aioredis.from_url(self.redis_url)
        try:
            await self.redis.xgroup_create("trades_stream", self.consumer_group, id='0', mkstream=True)
        except aioredis.ResponseError:
            pass  # group exists

    async def publish(self, topic: str, message: dict):
        await self.redis.xadd(f"{topic}_stream", {"data": json.dumps(message)})

    async def subscribe(self, topic: str) -> AsyncGenerator[dict, None]:
        stream = f"{topic}_stream"
        while True:
            resp = await self.redis.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_name,
                streams={stream: '>'},
                count=100,
                block=1000
            )
            for _, msgs in resp:
                for msg_id, msg_data in msgs:
                    data = json.loads(msg_data[b"data"].decode())
                    yield data
                    await self.redis.xack(stream, self.consumer_group, msg_id)