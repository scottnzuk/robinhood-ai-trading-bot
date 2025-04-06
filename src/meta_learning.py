import os
import redis.asyncio as redis
import json
import time

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def log_call(agent_name, prompt, response, success, latency, cost=0.0, feedback=None):
    """Log a single agent/tool call"""
    entry = {
        "timestamp": time.time(),
        "agent": agent_name,
        "prompt": prompt,
        "response": response,
        "success": success,
        "latency": latency,
        "cost": cost,
        "feedback": feedback
    }
    await redis_client.rpush("mcp:logs", json.dumps(entry))

async def get_recent_logs(limit=100):
    logs = await redis_client.lrange("mcp:logs", -limit, -1)
    return [json.loads(log) for log in logs]

async def analyze_performance():
    logs = await get_recent_logs(1000)
    stats = {}
    for log in logs:
        agent = log["agent"]
        success = log["success"]
        latency = log["latency"]
        stats.setdefault(agent, {"calls":0, "success":0, "fail":0, "avg_latency":0})
        stats[agent]["calls"] +=1
        if success:
            stats[agent]["success"] +=1
        else:
            stats[agent]["fail"] +=1
        stats[agent]["avg_latency"] += latency
    # Finalize averages
    for agent in stats:
        calls = stats[agent]["calls"]
        stats[agent]["avg_latency"] /= max(calls,1)
    return stats

async def adaptive_routing(prompt, candidate_agents):
    """
    Choose best agent(s) based on recent performance.
    """
    stats = await analyze_performance()
    sorted_agents = sorted(candidate_agents, key=lambda a: -stats.get(a, {}).get("success",0))
    return sorted_agents

async def discover_plugins(plugin_sources):
    """
    Discover new plugins from external sources.
    plugin_sources: list of URLs or APIs
    """
    discovered = {}
    for src in plugin_sources:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(src)
                if r.status_code == 200:
                    plugins = r.json().get("plugins", {})
                    discovered.update(plugins)
        except Exception:
            continue
    # Register discovered plugins
    for name, info in discovered.items():
        await redis_client.hset("mcp:tools", name, json.dumps(info))
    return discovered