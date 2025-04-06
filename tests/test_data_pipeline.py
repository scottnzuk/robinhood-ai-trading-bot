import pytest
import asyncio
from src import data_pipeline

import types
import json as jsonlib

@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    # In-memory list to simulate Redis list
    redis_list = []

    class FakeRedis:
        async def rpush(self, key, value):
            redis_list.append(value)

        async def lrange(self, key, start, end):
            # Redis lrange end is inclusive
            if end == -1:
                end = len(redis_list) - 1
            return redis_list[start:end+1]

        async def lindex(self, key, index):
            try:
                return redis_list[index]
            except IndexError:
                return None

        async def lset(self, key, index, value):
            redis_list[index] = value

    fake_client = FakeRedis()
    monkeypatch.setattr(data_pipeline, "redis_client", fake_client)

@pytest.mark.asyncio
async def test_save_interaction():
    await data_pipeline.save_interaction("prompt", "response", label="test", feedback="good", metadata={"meta": "data"})

@pytest.mark.asyncio
async def test_get_dataset():
    dataset = await data_pipeline.get_dataset(limit=5)
    assert isinstance(dataset, list) or dataset is None

@pytest.mark.asyncio
async def test_export_dataset(tmp_path):
    filename = tmp_path / "dataset.jsonl"
    await data_pipeline.export_dataset(str(filename), limit=5)
    assert filename.exists()

@pytest.mark.asyncio
async def test_label_interaction():
    await data_pipeline.label_interaction(1, "label")