"""
Caching utilities for AI Trends Analyzer
"""
import json
import redis
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps
from config import Config

logger = logging.getLogger(__name__)

class CacheManager:
    """Centralized cache management with Redis and in-memory fallback"""
    
    def __init__(self):
        self.config = Config()
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection with fallback to memory cache"""
        try:
            import redis
            # Try to connect to Redis if available
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats['hits'] += 1
                    return json.loads(value)
            else:
                # Memory cache fallback
                cache_entry = self.memory_cache.get(key)
                if cache_entry and cache_entry['expires'] > datetime.utcnow():
                    self.cache_stats['hits'] += 1
                    return cache_entry['value']
                elif cache_entry:
                    # Expired entry
                    del self.memory_cache[key]
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds"""
        try:
            if self.redis_client:
                serialized = json.dumps(value, default=str)
                result = self.redis_client.setex(key, ttl, serialized)
                if result:
                    self.cache_stats['sets'] += 1
                    return True
            else:
                # Memory cache fallback
                expires = datetime.utcnow() + timedelta(seconds=ttl)
                self.memory_cache[key] = {
                    'value': value,
                    'expires': expires
                }
                self.cache_stats['sets'] += 1
                return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.cache_stats['errors'] += 1
            
        return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                return self.memory_cache.pop(key, None) is not None
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        cleared = 0
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    cleared = self.redis_client.delete(*keys)
            else:
                # Memory cache pattern matching
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    cleared += 1
            
            logger.info(f"Cleared {cleared} cache keys matching pattern: {pattern}")
            return cleared
            
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_type': 'redis' if self.redis_client else 'memory',
            'memory_cache_size': len(self.memory_cache)
        }

# Global cache manager instance
cache_manager = CacheManager()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            
            # Include relevant args in key
            for arg in args:
                if isinstance(arg, (str, int, float)):
                    key_parts.append(str(arg))
                elif hasattr(arg, 'id'):
                    key_parts.append(f"{type(arg).__name__}_{arg.id}")
            
            # Include kwargs in key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}_{v}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}: {cache_key}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str):
    """Invalidate cache entries matching pattern"""
    return cache_manager.clear_pattern(pattern)