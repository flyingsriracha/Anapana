"""Reports dashboard endpoint.

Aggregates metrics across 5 database shards in parallel.
"""
import asyncio
from db.pool import pool


SHARDS = [0, 1, 2, 3, 4]


async def fetch_metric_shard(shard_id):
    """Fetch metrics from a single shard. Fast in isolation (~0.5s)."""
    async with pool.acquire() as conn:
        # Simulated SQL query against this shard
        await asyncio.sleep(0.5)
        return {"shard": shard_id, "conn_id": conn["id"], "rows": 100}


async def get_dashboard_data():
    """Aggregate metrics across all shards in parallel."""
    results = await asyncio.gather(*[fetch_metric_shard(s) for s in SHARDS])
    return {
        "shards": results,
        "total_rows": sum(r["rows"] for r in results),
    }
