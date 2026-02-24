"""
MapAPI Module - Main entry point for map data queries.

This module provides a unified interface for querying map data from shared memory.
It serves as the main entry point for accessing map data in the traffic rule
compliance system.

Usage:
    from mapapi import MapManager, Position
    
    # Get singleton instance
    map_manager = MapManager()
    
    # Initialize (after map is loaded by MapLoader)
    map_manager.initialize()
    
    # Query map data
    position = Position(latitude=39.9042, longitude=116.4074)
    lanelet = map_manager.get_lanelet(position)
    speed_limit = map_manager.get_speed_limit(position)
"""

from .manager import MapManager, get_map_manager
from .api import MapAPI
from .types import (
    Lanelet,
    LaneletType,
    TrafficSign,
    SignType,
    FishboneLine,
    ConstructionSign,
    RampInfo
)

# Re-export base types from map_common.base for convenience
from map_node.map_common.base import Position, MapInfo, BoundingBox

__version__ = "0.1.0"
__all__ = [
    # Manager
    'MapManager',
    'get_map_manager',
    # API
    'MapAPI',
    # Types
    'Lanelet',
    'LaneletType',
    'TrafficSign',
    'SignType',
    'FishboneLine',
    'ConstructionSign',
    'RampInfo',
    # Base types
    'Position',
    'MapInfo',
    'BoundingBox',
]
