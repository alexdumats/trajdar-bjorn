"""
Unit tests for CacheService (src/cache.py)
"""
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


class FakeRedis:
    """A simple fake Redis client for testing Redis-backed behavior."""
    def __init__(self, *args, **kwargs):
        self.storage = {}
        self._info = {
            "connected_clients": 5,
            "used_memory_human": "1.23M",
            "total_commands_processed": 100,
            "keyspace_hits": 30,
            "keyspace_misses": 10,
        }

    # Connection check
    def ping(self):
        return True

    # Basic commands we need
    def setex(self, key, ttl, value):
        # store as string like real redis (decode_responses=True makes get return str)
        self.storage[key] = str(value)
        return True

    def get(self, key):
        return self.storage.get(key)

    def delete(self, key):
        if key in self.storage:
            del self.storage[key]
            return 1
        return 0

    def exists(self, key):
        return 1 if key in self.storage else 0

    def info(self):
        return dict(self._info)


@pytest.fixture
def fallback_cache(monkeypatch):
    """Provide a CacheService instance forced into fallback (in-memory) mode."""
    # Ensure small cache size to test eviction easily
    monkeypatch.setenv("FALLBACK_MAX_CACHE_SIZE", "3")

    # Patch redis.Redis to raise on ping so constructor flips to fallback_mode
    class FailingRedis:
        def __init__(self, *args, **kwargs):
            pass
        def ping(self):
            raise Exception("fail connect")
    
    # Delay import until after patch
    with patch("src.cache.redis.Redis", FailingRedis):
        from src.cache import CacheService  # import here to bind patch in constructor
        cache = CacheService()
        assert cache.fallback_mode is True
        return cache


@pytest.fixture
def redis_cache(monkeypatch):
    """Provide a CacheService instance backed by a fake Redis client."""
    # Patch redis.Redis to our fake client
    with patch("src.cache.redis.Redis", lambda *args, **kwargs: FakeRedis()):
        from src.cache import CacheService
        cache = CacheService()
        assert cache.fallback_mode is False
        assert cache.redis_client is not None
        return cache


class TestCacheServiceFallback:
    """Tests for in-memory fallback mode behavior."""

    def test_set_get_and_hit_miss_accounting(self, fallback_cache):
        key = "test:key"
        value = {"a": 1}

        assert fallback_cache.get(key) is None  # miss
        assert fallback_cache.misses >= 1

        assert fallback_cache.set(key, value, ttl=60) is True
        got = fallback_cache.get(key)
        assert got == value
        assert fallback_cache.hits >= 1

    def test_ttl_expiry_and_exists(self, fallback_cache):
        key = "expiring:key"
        value = {"v": 42}
        assert fallback_cache.set(key, value, ttl=60) is True

        # Force expiry by modifying internal expiry to a past time
        assert key in fallback_cache.memory_cache
        data, _ = fallback_cache.memory_cache[key]
        fallback_cache.memory_cache[key] = (data, datetime.now() - timedelta(seconds=1))

        # Should be treated as expired: get -> None and exists -> False
        assert fallback_cache.get(key) is None
        assert fallback_cache.exists(key) is False

    def test_eviction_when_max_size_reached(self, fallback_cache):
        # Ensure max size is 3 from fixture
        # Insert 3 entries
        for i in range(3):
            assert fallback_cache.set(f"k{i}", {"i": i}, ttl=300)
        # Next insert should trigger eviction of at least 1 entry
        prev_evictions = fallback_cache.evictions
        assert fallback_cache.set("k3", {"i": 3}, ttl=300)
        assert fallback_cache.evictions >= prev_evictions + 1
        # Size should not exceed max_cache_size by much (may be equal after eviction)
        assert len(fallback_cache.memory_cache) <= fallback_cache.max_cache_size

    def test_namespaced_helpers_price_and_indicator(self, fallback_cache):
        price = {"symbol": "BTCUSDT", "price": 50000.0}
        assert fallback_cache.set_price_data("BTCUSDT", price, ttl=120)
        assert fallback_cache.get_price_data("BTCUSDT") == price

        rsi = {"value": 65.5}
        assert fallback_cache.set_indicator_data("BTCUSDT", "RSI", "1m", rsi, ttl=120)
        assert fallback_cache.get_indicator_data("BTCUSDT", "RSI", "1m") == rsi

    def test_get_cache_stats_structure_and_hit_rate(self, fallback_cache):
        # Produce a mix of hits/misses
        fallback_cache.get("missing:key")  # miss
        fallback_cache.set("hit:key", {"x": 1}, ttl=60)
        fallback_cache.get("hit:key")  # hit

        stats = fallback_cache.get_cache_stats()
        assert stats["cache_type"].startswith("in-memory")
        assert "active_keys" in stats
        assert "expired_keys" in stats
        assert "hits" in stats and "misses" in stats
        assert 0.0 <= stats["hit_rate"] <= 1.0

    def test_delete_in_fallback(self, fallback_cache):
        key = "del:key"
        fallback_cache.set(key, {"v": 1}, ttl=60)
        assert fallback_cache.exists(key) is True
        assert fallback_cache.delete(key) is True
        assert fallback_cache.exists(key) is False


class TestCacheServiceRedis:
    """Tests for Redis-backed behavior using a fake client."""

    def test_set_get_uses_json_serialization(self, redis_cache):
        key = "some:key"
        value = {"a": 2}
        assert redis_cache.set(key, value, ttl=100) is True
        # FakeRedis stores string; CacheService.get should json.loads it back to dict
        got = redis_cache.get(key)
        assert got == value

    def test_delete_and_exists_in_redis_mode(self, redis_cache):
        key = "del:redis"
        redis_cache.set(key, {"b": 3}, ttl=50)
        assert redis_cache.exists(key) is True
        assert redis_cache.delete(key) is True
        assert redis_cache.exists(key) is False

    def test_get_cache_stats_redis(self, redis_cache):
        stats = redis_cache.get_cache_stats()
        assert stats["cache_type"] == "redis"
        assert stats["connected_clients"] == 5
        assert stats["used_memory"] == "1.23M"
        assert stats["total_commands_processed"] == 100
        assert stats["hit_rate"] == pytest.approx(30 / (30 + 10))
