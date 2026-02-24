"""
MapManager - Singleton pattern for unified map API access.
"""

import logging
from typing import Optional, List

from map_node.map_common.base import Position, MapInfo
from map_node.maploader.utils import Projector
from .api import MapAPI
from .types import Lanelet, TrafficSign, FishboneLine, ConstructionSign, RampInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapManager:
    """
    Map Manager - Singleton pattern for unified map API access.
    
    This class provides a single entry point for all map queries in the
    traffic rule compliance system. It uses the singleton pattern to ensure
    only one instance exists throughout the application.
    
    Usage:
        # From MapLoader (for ROS distributed nodes)
        loader = MapLoader()
        loader.load_map("map.osm", coordinate_type="local")
        map_data = loader.get_map_data()
        map_manager.initialize(map_data)
        
        # Query map data
        lanelet = map_manager.get_lanelet(position)
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("MapManager singleton instance created")
        return cls._instance
    
    def __init__(self):
        """Initialize map manager."""
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.api: Optional[MapAPI] = None
        self._initialized = True
        logger.info("MapManager initialized")
    
    def initialize(self, map_data: dict) -> None:
        """
        Initialize MapAPI with map data.
        
        Args:
            map_data: Dictionary containing lanelet_map, projector, and map_info.
                      This parameter-based approach is suitable for ROS distributed nodes.
        """
        try:
            self.api = MapAPI(map_data=map_data)
            
            if self.api.is_loaded():
                logger.info("MapAPI initialized successfully with loaded map")
            else:
                logger.warning("MapAPI initialized but no map is loaded")
                
        except ImportError as e:
            logger.error(f"Failed to initialize MapAPI: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing MapAPI: {e}")
            raise
    
    def set_projector(self, projector: Projector) -> None:
        """
        Set projector for coordinate transformation.
        
        This updates the projector in the API instance.
        
        Args:
            projector: Projector instance
        """
        if self.api is not None:
            self.api.projector = projector
        logger.info(f"Projector updated")
    
    def set_map_info(self, map_info: MapInfo) -> None:
        """
        Set map information.
        
        This updates the map info in the API instance.
        
        Args:
            map_info: MapInfo instance
        """
        if self.api is not None:
            self.api.map_info = map_info
        logger.info(f"Map info updated")
    
    # ==================== Basic Query Methods ====================
    
    def get_lanelet(self, position: Position, use_local_coords: bool = None) -> Optional[Lanelet]:
        """
        Get the lanelet at the given position.
        
        Args:
            position: Position (GPS or local coordinates)
            use_local_coords: Whether position uses local coordinates (x, y)
            
        Returns:
            Lanelet information, or None if not on any lanelet
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return None
        return self.api.get_lanelet(position, use_local_coords)
    
    def get_lanelet_by_id(self, lanelet_id: str, use_local_coords: bool = None) -> Optional[Lanelet]:
        """
        Get the lanelet by ID.
        
        Args:
            lanelet_id: Lanelet ID
            use_local_coords: Whether to use local coordinates for position conversion
            
        Returns:
            Lanelet information, or None if not found
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return None
        return self.api.get_lanelet_by_id(lanelet_id, use_local_coords)
    
    def get_speed_limit(self, position: Position, use_local_coords: bool = None) -> Optional[float]:
        """
        Get the speed limit at the given position.
        
        Args:
            position: Position (GPS or local coordinates)
            use_local_coords: Whether position uses local coordinates (x, y)
            
        Returns:
            Speed limit in km/h, or None if no limit
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return None
        return self.api.get_speed_limit(position, use_local_coords)
    
    def get_traffic_signs(self, position: Position, radius: float = 100.0,
                         use_local_coords: bool = None) -> List[TrafficSign]:
        """
        Get traffic signs within a radius of the given position.
        
        Args:
            position: Center position (GPS or local coordinates)
            radius: Search radius in meters
            use_local_coords: Whether position uses local coordinates (x, y)
            
        Returns:
            List of traffic signs
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return []
        return self.api.get_traffic_signs(position, radius, use_local_coords)
    
    def get_nearby_lanelets(self, position: Position, radius: float = 50.0,
                           max_count: int = 10, use_local_coords: bool = None) -> List[Lanelet]:
        """
        Get nearby lanelets within a radius.
        
        Args:
            position: Center position (GPS or local coordinates)
            radius: Search radius in meters
            max_count: Maximum number of lanelets to return
            use_local_coords: Whether position uses local coordinates (x, y)
            
        Returns:
            List of nearby lanelets
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return []
        return self.api.get_nearby_lanelets(position, radius, max_count, use_local_coords)
    
    def get_lanelet_topology(self, lanelet_id: str) -> dict:
        """
        Get lanelet topology information.
        
        Args:
            lanelet_id: Lanelet ID
            
        Returns:
            Dictionary with 'left', 'right', 'following', 'preceding' keys
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return {}
        return self.api.get_lanelet_topology(lanelet_id)
    
    def get_map_info(self) -> Optional[MapInfo]:
        """
        Get map information.
        
        Returns:
            Map information, or None if not available
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return None
        return self.api.get_map_info()
    
    def is_loaded(self) -> bool:
        """
        Check if map is loaded.
        
        Returns:
            True if map is loaded
        """
        if self.api is None:
            return False
        return self.api.is_loaded()
    
    # ==================== Cache Management ====================
    
    def clear_cache(self) -> None:
        """Clear the lanelet cache."""
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return
        self.api.clear_cache()
    
    def enable_cache(self, enabled: bool = True) -> None:
        """
        Enable or disable caching.
        
        Args:
            enabled: Whether to enable caching
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return
        self.api.enable_cache(enabled)
    
    # ==================== Custom Query Methods ====================
    
    def query_ramp_info(self, position: Position, use_local_coords: bool = None) -> Optional[RampInfo]:
        """
        Query ramp information at the given position.
        
        This is a custom query method for identifying ramps (entry/exit lanes).
        
        Args:
            position: Position (GPS or local coordinates)
            use_local_coords: Whether position uses local coordinates (x, y)
            
        Returns:
            Ramp information, or None if not on a ramp
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return None
        return self.api.query_ramp_info(position, use_local_coords)
    
    def query_structured_road(self, position: Position, use_local_coords: bool = None) -> bool:
        """
        Query if the position is on a structured road.
        
        This is a custom query method for identifying structured roads
        (highways, main roads with clear lane markings).
        
        Args:
            position: Position (GPS or local coordinates)
            use_local_coords: Whether position uses local coordinates (x, y)
            
        Returns:
            True if on a structured road
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return False
        return self.api.query_structured_road(position, use_local_coords)
    
    def query_fishbone_lines(self, position: Position, radius: float = 100.0,
                            use_local_coords: bool = None) -> List[FishboneLine]:
        """
        Query fishbone lines near the given position.
        
        This is a custom query method for identifying fishbone lines
        (deceleration markings on highways).
        
        Args:
            position: Center position (GPS or local coordinates)
            radius: Search radius in meters
            use_local_coords: Whether position uses local coordinates (x, y)
            
        Returns:
            List of fishbone lines
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return []
        return self.api.query_fishbone_lines(position, radius, use_local_coords)
    
    def query_construction_signs(self, position: Position, radius: float = 200.0,
                                 use_local_coords: bool = None) -> List[ConstructionSign]:
        """
        Query construction signs near the given position.
        
        This is a custom query method for identifying construction zones.
        
        Args:
            position: Center position (GPS or local coordinates)
            radius: Search radius in meters
            use_local_coords: Whether position uses local coordinates (x, y)
            
        Returns:
            List of construction signs
        """
        if self.api is None:
            logger.warning("MapAPI not initialized. Call initialize() first.")
            return []
        return self.api.query_construction_signs(position, radius, use_local_coords)
    
    # ==================== Utility Methods ====================
    
    def reset(self) -> None:
        """Reset the MapManager (clear API instance)."""
        self.api = None
        logger.info("MapManager reset")
    
    def get_status(self) -> dict:
        """
        Get the current status of the MapManager.
        
        Returns:
            Dictionary with status information
        """
        return {
            'initialized': self.api is not None,
            'map_loaded': self.is_loaded(),
            'cache_enabled': self.api._cache_enabled if self.api else False,
            'cache_size': len(self.api._lanelet_cache) if self.api else 0
        }


# Convenience function for getting the singleton instance
def get_map_manager() -> MapManager:
    """
    Get the MapManager singleton instance.
    
    Returns:
        MapManager instance
    """
    return MapManager()
