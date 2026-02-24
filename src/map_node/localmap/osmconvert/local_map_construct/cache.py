"""
Cache management module for LocalMapConstruct.

This module provides caching functionality for local maps to improve performance
by avoiding repeated construction of the same local map.
"""

import time
import logging
from typing import Optional, Dict, Any
from collections import OrderedDict

from common.local_map.local_map_data import LocalMap, Pose

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Cache manager for local maps.

    Implements an LRU (Least Recently Used) cache with TTL (Time To Live)
    support for storing and retrieving local maps. The cache is keyed by
    ego pose quantized to a specified tolerance.
    """

    def __init__(self, config: 'CacheConfig'):
        """
        Initialize the cache manager.

        Args:
            config: Cache configuration
        """
        self.config = config
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0

    def get(self, cache_key: str) -> Optional[LocalMap]:
        """
        Get a cached local map by key.

        Args:
            cache_key: Cache key generated from ego pose

        Returns:
            Cached LocalMap if found and valid, None otherwise
        """
        if not self.config.enabled:
            return None

        if cache_key not in self._cache:
            self._miss_count += 1
            return None

        entry = self._cache[cache_key]

        # Check if entry has expired
        if time.time() - entry['timestamp'] > self.config.ttl_seconds:
            # Remove expired entry
            del self._cache[cache_key]
            self._miss_count += 1
            logger.debug(f"Cache entry expired for key: {cache_key}")
            return None

        # Move to end (mark as recently used)
        self._cache.move_to_end(cache_key)
        self._hit_count += 1

        logger.debug(f"Cache hit for key: {cache_key}")
        return entry['local_map']

    def set(self, cache_key: str, local_map: LocalMap) -> None:
        """
        Cache a local map.

        Args:
            cache_key: Cache key generated from ego pose
            local_map: LocalMap to cache
        """
        if not self.config.enabled:
            return

        # Check if cache is full and remove oldest entry if needed
        if len(self._cache) >= self.config.max_size:
            if cache_key in self._cache:
                # Update existing entry
                self._cache.move_to_end(cache_key)
            else:
                # Remove oldest entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Cache full, removed oldest entry: {oldest_key}")

        # Add new entry
        self._cache[cache_key] = {
            'local_map': local_map,
            'timestamp': time.time()
        }

        logger.debug(f"Cached local map with key: {cache_key}")

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        logger.debug("Cache cleared")

    def invalidate(self, cache_key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            True if entry was found and removed, False otherwise
        """
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.debug(f"Invalidated cache entry: {cache_key}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests) if total_requests > 0 else 0.0

        return {
            'enabled': self.config.enabled,
            'max_size': self.config.max_size,
            'current_size': len(self._cache),
            'ttl_seconds': self.config.ttl_seconds,
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate': hit_rate,
        }

    def is_cache_valid(
        self,
        cache_key: str,
        ego_pose: Pose,
        position_tolerance: float = 5.0
    ) -> bool:
        """
        Check if a cached entry is still valid for the given ego pose.

        Args:
            cache_key: Cache key to check
            ego_pose: Current ego pose
            position_tolerance: Position tolerance in meters

        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self._cache:
            return False

        entry = self._cache[cache_key]

        # Check TTL
        if time.time() - entry['timestamp'] > self.config.ttl_seconds:
            return False

        # Check if ego position is within tolerance
        cached_map = entry['local_map']
        if cached_map.metadata is None:
            return False

        dx = ego_pose.position.x - cached_map.metadata.ego_vehicle_x
        dy = ego_pose.position.y - cached_map.metadata.ego_vehicle_y
        distance = (dx * dx + dy * dy) ** 0.5

        return distance <= position_tolerance

    def prune_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry['timestamp'] > self.config.ttl_seconds
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Pruned {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_cache_keys(self) -> list:
        """
        Get all cache keys.

        Returns:
            List of cache keys
        """
        return list(self._cache.keys())
