"""Tests for the reports dashboard."""
import pytest
from db.pool import ConnectionPool
from reports.dashboard import get_dashboard_data


@pytest.fixture
def isolated_pool():
    """Tests use their own pool, separate from the production one."""
    return ConnectionPool(max_connections=10)


@pytest.mark.asyncio
async def test_dashboard_returns_all_shards():
    """Dashboard should fan out across all 5 shards and aggregate."""
    data = await get_dashboard_data()
    assert len(data["shards"]) == 5
    assert data["total_rows"] == 500


@pytest.mark.asyncio
async def test_dashboard_shard_ids_are_correct():
    data = await get_dashboard_data()
    shard_ids = sorted(r["shard"] for r in data["shards"])
    assert shard_ids == [0, 1, 2, 3, 4]
