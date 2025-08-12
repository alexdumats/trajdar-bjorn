#!/usr/bin/env python3
"""
Redis-Based Caching Service
Implements caching layers for price data, indicators, configuration, and portfolio state
"""

import redis
import json
import logging
import os
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        """Initialize Redis connection for caching"""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_CACHE_DB", 1))  # Use different DB for cache
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.fallback_mode = False
        self.redis_client = None
        
        # In-memory cache configuration
        self.memory_cache = {}  # In-memory cache for fallback mode
        self.max_cache_size = int(os.getenv("FALLBACK_MAX_CACHE_SIZE", 1000))
        self.cleanup_interval = int(os.getenv("FALLBACK_CLEANUP_INTERVAL", 300))  # 5 minutes
        self.last_cleanup_time = datetime.now()
        
        # Cache metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Connected to Redis cache")
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to Redis cache: {e}")
            logger.warning("⚠️ Using in-memory fallback cache")
            self.fallback_mode = True
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            # Check if cleanup is needed
            self._check_cleanup()
            
            if self.fallback_mode:
                # Use in-memory cache in fallback mode
                if key in self.memory_cache:
                    value_data, expiry = self.memory_cache.get(key, (None, None))
                    # Check if the value has expired
                    if expiry and datetime.now() > expiry:
                        # Value has expired, remove it
                        del self.memory_cache[key]
                        self.misses += 1
                        return None
                    # Valid cache hit
                    self.hits += 1
                    return value_data
                # Cache miss
                self.misses += 1
                return None
            else:
                # Use Redis if client is available
                if self.redis_client:
                    value = self.redis_client.get(key)
                    if value:
                        # Try to parse as JSON, fallback to raw string
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            return value
                else:
                    logger.warning(f"⚠️ Redis client not available for get operation on key: {key}")
                return None
        except Exception as e:
            logger.error(f"❌ Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Process value for storage
            if isinstance(value, (dict, list)):
                processed_value = value  # Store as-is in memory cache
                value_str = json.dumps(value)  # For Redis
            else:
                processed_value = value
                value_str = str(value)
            
            if self.fallback_mode:
                # Use in-memory cache in fallback mode
                
                # Check if we need to evict entries due to size limit
                if len(self.memory_cache) >= self.max_cache_size:
                    self._evict_entries()
                
                expiry = datetime.now() + timedelta(seconds=ttl)
                self.memory_cache[key] = (processed_value, expiry)
                logger.debug(f"💾 Cached {key} in memory for {ttl} seconds")
                return True
            else:
                # Use Redis if client is available
                if self.redis_client:
                    result = self.redis_client.setex(key, ttl, value_str)
                    if result:
                        logger.debug(f"💾 Cached {key} in Redis for {ttl} seconds")
                    return bool(result)
                else:
                    logger.warning(f"⚠️ Redis client not available for set operation on key: {key}")
                    # Fall back to in-memory cache
                    expiry = datetime.now() + timedelta(seconds=ttl)
                    self.memory_cache[key] = (processed_value, expiry)
                    logger.debug(f"💾 Cached {key} in memory for {ttl} seconds (Redis fallback)")
                    return True
        except Exception as e:
            logger.error(f"❌ Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.fallback_mode:
                # Use in-memory cache in fallback mode
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
            else:
                # Use Redis if client is available
                if self.redis_client:
                    result = self.redis_client.delete(key)
                    return bool(result)
                else:
                    logger.warning(f"⚠️ Redis client not available for delete operation on key: {key}")
                    return False
        except Exception as e:
            logger.error(f"❌ Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            if self.fallback_mode:
                # Use in-memory cache in fallback mode
                if key in self.memory_cache:
                    value_data, expiry = self.memory_cache.get(key, (None, None))
                    # Check if the value has expired
                    if expiry and datetime.now() > expiry:
                        # Value has expired, remove it
                        del self.memory_cache[key]
                        return False
                    return True
                return False
            else:
                # Use Redis if client is available
                if self.redis_client:
                    return bool(self.redis_client.exists(key))
                else:
                    logger.warning(f"⚠️ Redis client not available for exists operation on key: {key}")
                    return False
        except Exception as e:
            logger.error(f"❌ Cache exists error for key {key}: {e}")
            return False
    
    def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached price data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDC")
            
        Returns:
            Dict with price data or None if not cached
        """
        key = f"price:{symbol}"
        return self.get(key)
    
    def set_price_data(self, symbol: str, price_data: Dict[str, Any], ttl: int = 300) -> bool:
        """
        Cache price data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDC")
            price_data: Price data dictionary
            ttl: Time to live in seconds (default 5 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"price:{symbol}"
        return self.set(key, price_data, ttl)
    
    def get_indicator_data(self, symbol: str, indicator: str, timeframe: str = "1m") -> Optional[Dict[str, Any]]:
        """
        Get cached indicator data
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDC")
            indicator: Indicator name (e.g., "RSI", "MACD")
            timeframe: Timeframe (e.g., "1m", "5m", "1h")
            
        Returns:
            Dict with indicator data or None if not cached
        """
        key = f"indicator:{symbol}:{indicator}:{timeframe}"
        return self.get(key)
    
    def set_indicator_data(self, symbol: str, indicator: str, timeframe: str, indicator_data: Dict[str, Any], ttl: int = 600) -> bool:
        """
        Cache indicator data
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDC")
            indicator: Indicator name (e.g., "RSI", "MACD")
            timeframe: Timeframe (e.g., "1m", "5m", "1h")
            indicator_data: Indicator data dictionary
            ttl: Time to live in seconds (default 10 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"indicator:{symbol}:{indicator}:{timeframe}"
        return self.set(key, indicator_data, ttl)
    
    def get_config(self, config_name: str) -> Optional[Any]:
        """
        Get cached configuration
        
        Args:
            config_name: Configuration name
            
        Returns:
            Configuration value or None if not cached
        """
        key = f"config:{config_name}"
        return self.get(key)
    
    def set_config(self, config_name: str, config_value: Any, ttl: int = 3600) -> bool:
        """
        Cache configuration
        
        Args:
            config_name: Configuration name
            config_value: Configuration value
            ttl: Time to live in seconds (default 1 hour)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"config:{config_name}"
        return self.set(key, config_value, ttl)
    
    def get_portfolio_state(self) -> Optional[Dict[str, Any]]:
        """
        Get cached portfolio state
        
        Returns:
            Dict with portfolio state or None if not cached
        """
        return self.get("portfolio:state")
    
    def set_portfolio_state(self, portfolio_state: Dict[str, Any], ttl: int = 60) -> bool:
        """
        Cache portfolio state
        
        Args:
            portfolio_state: Portfolio state dictionary
            ttl: Time to live in seconds (default 1 minute)
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.set("portfolio:state", portfolio_state, ttl)
    
    def warmup_cache(self, symbols: List[str]) -> bool:
        """
        Warm up cache with critical data
        
        Args:
            symbols: List of trading symbols to warm up
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Warm up configuration
            self.set_config("cache_warmed", True, 3600)
            logger.info("🔥 Cache warmup completed")
            return True
        except Exception as e:
            logger.error(f"❌ Cache warmup failed: {e}")
            return False
    
    def _check_cleanup(self):
        """Check if cache cleanup is needed and perform it if necessary"""
        if not self.fallback_mode:
            return
            
        current_time = datetime.now()
        if (current_time - self.last_cleanup_time).total_seconds() > self.cleanup_interval:
            self._cleanup_expired()
            self.last_cleanup_time = current_time
    
    def _cleanup_expired(self):
        """Remove all expired entries from the cache"""
        if not self.fallback_mode:
            return
            
        current_time = datetime.now()
        expired_keys = []
        
        # Find all expired keys
        for key, (_, expiry) in list(self.memory_cache.items()):
            if expiry and current_time > expiry:
                expired_keys.append(key)
        
        # Remove expired keys
        for key in expired_keys:
            del self.memory_cache[key]
            
        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
    
    def _evict_entries(self):
        """Evict entries based on LRU policy when cache is full"""
        if not self.fallback_mode or len(self.memory_cache) < self.max_cache_size:
            return
            
        # Find the oldest entries (based on expiry time)
        entries = [(k, v[1]) for k, v in self.memory_cache.items()]
        # Sort by expiry time (oldest first)
        entries.sort(key=lambda x: x[1])
        
        # Remove 10% of entries or at least one
        to_remove = max(1, len(entries) // 10)
        for i in range(to_remove):
            if i < len(entries):
                del self.memory_cache[entries[i][0]]
                self.evictions += 1
        
        logger.info(f"♻️ Evicted {to_remove} cache entries due to size limit")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict with cache statistics
        """
        try:
            if self.fallback_mode:
                # Basic stats for in-memory cache
                # Count expired items
                current_time = datetime.now()
                active_keys = 0
                expired_keys = 0
                
                for key, (_, expiry) in list(self.memory_cache.items()):
                    if expiry and current_time > expiry:
                        expired_keys += 1
                    else:
                        active_keys += 1
                
                # Calculate hit rate
                total_ops = self.hits + self.misses
                hit_rate = self.hits / total_ops if total_ops > 0 else 0
                
                return {
                    "cache_type": "in-memory (fallback)",
                    "active_keys": active_keys,
                    "expired_keys": expired_keys,
                    "total_keys": len(self.memory_cache),
                    "max_size": self.max_cache_size,
                    "hits": self.hits,
                    "misses": self.misses,
                    "evictions": self.evictions,
                    "hit_rate": hit_rate,
                    "last_cleanup": self.last_cleanup_time.isoformat(),
                    "memory_usage": "N/A"
                }
            else:
                # Redis stats if client is available
                if self.redis_client:
                    info = self.redis_client.info()
                    return {
                        "cache_type": "redis",
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory": info.get("used_memory_human", "0B"),
                        "total_commands_processed": info.get("total_commands_processed", 0),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0),
                        "hit_rate": info.get("keyspace_hits", 0) / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) if info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1) > 0 else 0
                    }
                else:
                    logger.warning("⚠️ Redis client not available for stats operation")
                    return {
                        "cache_type": "redis (unavailable)",
                        "error": "Redis client not available"
                    }
        except Exception as e:
            logger.error(f"❌ Cache stats error: {e}")
            return {"cache_type": "unknown", "error": str(e)}

# Global cache instance
cache = CacheService()

if __name__ == "__main__":
    # Example usage
    cache_service = CacheService()
    
    # Test price data caching
    price_data = {
        "symbol": "BTCUSDC",
        "price": 50000.0,
        "timestamp": datetime.now().isoformat()
    }
    cache_service.set_price_data("BTCUSDC", price_data, 300)
    
    cached_price = cache_service.get_price_data("BTCUSDC")
    print(f"Cached price: {cached_price}")
    
    # Test indicator data caching
    rsi_data = {
        "value": 65.5,
        "timestamp": datetime.now().isoformat()
    }
    cache_service.set_indicator_data("BTCUSDC", "RSI", "1m", rsi_data, 600)
    
    cached_rsi = cache_service.get_indicator_data("BTCUSDC", "RSI", "1m")
    print(f"Cached RSI: {cached_rsi}")
    
    # Test configuration caching
    config_value = {"max_position_size": 0.1, "stop_loss": 0.05}
    cache_service.set_config("risk_management", config_value, 3600)
    
    cached_config = cache_service.get_config("risk_management")
    print(f"Cached config: {cached_config}")
    
    # Test cache stats
    stats = cache_service.get_cache_stats()
    print(f"Cache stats: {stats}")