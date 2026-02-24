"""
Type definitions and configuration classes for LocalMapConstruct module.

This module defines the configuration classes used throughout the LocalMapConstruct
module, including cache configuration and main constructor configuration.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CacheConfig:
    """
    Cache configuration for LocalMapConstruct.

    Attributes:
        enabled: Whether caching is enabled
        max_size: Maximum number of cached entries (LRU eviction when exceeded)
        ttl_seconds: Time-to-live for cache entries in seconds
        position_tolerance: Position tolerance in meters for cache key generation
    """
    enabled: bool = True
    max_size: int = 10
    ttl_seconds: float = 1.0
    position_tolerance: float = 5.0  # meters


@dataclass
class LocalMapConstructConfig:
    """
    Main configuration for LocalMapConstructor.

    Attributes:
        map_range: Local map range in meters (radius around ego vehicle)
        update_threshold: Distance threshold in meters for triggering map updates
        cache_config: Cache configuration
        coordinate_precision: Precision threshold for coordinate transformation (meters)
        enable_boundary_sharing: Whether to enable boundary segment sharing between lanes
        include_road_markings: Whether to include road markings in local map
        include_crosswalks: Whether to include crosswalks in local map
        include_intersections: Whether to include intersections in local map
    """
    map_range: float = 200.0
    update_threshold: float = 50.0
    cache_config: Optional[CacheConfig] = None
    coordinate_precision: float = 0.01
    enable_boundary_sharing: bool = True
    include_road_markings: bool = True
    include_crosswalks: bool = True
    include_intersections: bool = True

    def __post_init__(self):
        """Initialize default cache config if not provided."""
        if self.cache_config is None:
            self.cache_config = CacheConfig()


@dataclass
class TransformResult:
    """
    Result of a coordinate transformation operation.

    Attributes:
        success: Whether the transformation was successful
        point: The transformed point (if successful)
        error: Error message (if unsuccessful)
    """
    success: bool
    point: Optional['Point3D'] = None
    error: Optional[str] = None


@dataclass
class ConversionResult:
    """
    Result of a map conversion operation.

    Attributes:
        success: Whether the conversion was successful
        data: The converted data (if successful)
        warnings: List of warning messages during conversion
        errors: List of error messages during conversion
    """
    success: bool
    data: Optional[object] = None
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)


@dataclass
class BuildResult:
    """
    Result of a local map build operation.

    Attributes:
        success: Whether the build was successful
        local_map: The built local map (if successful)
        build_time_ms: Time taken to build the map in milliseconds
        stats: Statistics about the build operation
    """
    success: bool
    local_map: Optional['LocalMap'] = None
    build_time_ms: float = 0.0
    stats: dict = field(default_factory=dict)
