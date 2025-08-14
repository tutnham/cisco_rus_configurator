"""
Cache Manager for improving performance of frequently accessed data
"""

import time
import threading
import logging
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta

class CacheManager:
    """
    Simple in-memory cache manager with TTL (Time To Live) support.
    
    Provides caching functionality for command results, device information,
    and other frequently accessed data to improve application performance.
    """
    
    def __init__(self, default_ttl: int = 300) -> None:
        """
        Initialize the Cache Manager.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self.lock:
            if key in self.cache:
                value, expiry_time = self.cache[key]
                if datetime.now() < expiry_time:
                    self.logger.debug(f"Cache hit for key: {key}")
                    return value
                else:
                    # Remove expired entry
                    del self.cache[key]
                    self.logger.debug(f"Cache expired for key: {key}")
            
            self.logger.debug(f"Cache miss for key: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
            
        expiry_time = datetime.now() + timedelta(seconds=ttl)
        
        with self.lock:
            self.cache[key] = (value, expiry_time)
            self.logger.debug(f"Cached value for key: {key}, TTL: {ttl}s")
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.logger.debug(f"Deleted cache entry for key: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.logger.info(f"Cleared {count} cache entries")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of entries removed
        """
        current_time = datetime.now()
        expired_keys = []
        
        with self.lock:
            for key, (value, expiry_time) in self.cache.items():
                if current_time >= expiry_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
        
        if expired_keys:
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            total_entries = len(self.cache)
            
            # Count expired entries
            current_time = datetime.now()
            expired_count = 0
            for value, expiry_time in self.cache.values():
                if current_time >= expiry_time:
                    expired_count += 1
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_count,
                'active_entries': total_entries - expired_count,
                'default_ttl': self.default_ttl
            }

class CommandResultCache(CacheManager):
    """
    Specialized cache for SSH command results.
    """
    
    def __init__(self, default_ttl: int = 180) -> None:
        """
        Initialize command result cache.
        
        Args:
            default_ttl: Default TTL for command results (3 minutes)
        """
        super().__init__(default_ttl)
        
    def cache_command_result(self, host: str, command: str, result: str, ttl: Optional[int] = None) -> None:
        """
        Cache a command result.
        
        Args:
            host: Device hostname/IP
            command: Executed command
            result: Command result
            ttl: Time-to-live in seconds
        """
        cache_key = f"cmd:{host}:{command}"
        self.set(cache_key, result, ttl)
    
    def get_command_result(self, host: str, command: str) -> Optional[str]:
        """
        Get cached command result.
        
        Args:
            host: Device hostname/IP
            command: Command to look up
            
        Returns:
            Cached result if available, None otherwise
        """
        cache_key = f"cmd:{host}:{command}"
        return self.get(cache_key)
    
    def invalidate_host_cache(self, host: str) -> int:
        """
        Invalidate all cache entries for a specific host.
        
        Args:
            host: Device hostname/IP
            
        Returns:
            Number of entries invalidated
        """
        prefix = f"cmd:{host}:"
        keys_to_delete = []
        
        with self.lock:
            for key in self.cache.keys():
                if key.startswith(prefix):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
        
        if keys_to_delete:
            self.logger.info(f"Invalidated {len(keys_to_delete)} cache entries for host: {host}")
        
        return len(keys_to_delete)

# Global cache instances
_command_cache = CommandResultCache()
_general_cache = CacheManager()

def get_command_cache() -> CommandResultCache:
    """Get the global command result cache instance."""
    return _command_cache

def get_general_cache() -> CacheManager:
    """Get the global general cache instance."""
    return _general_cache