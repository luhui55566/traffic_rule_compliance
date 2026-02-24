"""
LocalMap constructor module for LocalMapConstruct.

This module provides the main LocalMapConstructor class that coordinates
all components to build local maps from MapAPI data.
"""

import logging
from typing import Optional, List, Dict, Any

from common.local_map.local_map_data import LocalMap, Pose, Point3D
from map_node.mapapi.api import MapAPI
from map_node.map_common.base import Position

from .config_types import LocalMapConstructConfig, BuildResult
from .transformer import CoordinateTransformer
from .converter import MapConverter
from .cache import CacheManager
from .builder import LocalMapBuilder

logger = logging.getLogger(__name__)


class LocalMapConstructor:
    """
    Local map constructor - main class for building local maps.

    This class coordinates all components (transformer, converter, cache, builder)
    to construct local maps from MapAPI data. It provides caching for performance
    and handles updates when the ego vehicle moves.
    """

    def __init__(self, config: LocalMapConstructConfig):
        """
        Initialize the local map constructor.

        Args:
            config: Configuration for the local map constructor
        """
        self.config = config

        # Initialize components
        self.transformer: Optional[CoordinateTransformer] = None
        self.converter: Optional[MapConverter] = None
        self.cache_manager = CacheManager(config.cache_config)
        self.builder = LocalMapBuilder()

        # Current state
        self.current_ego_pose: Optional[Pose] = None
        self.current_local_map: Optional[LocalMap] = None

        logger.info(f"LocalMapConstructor initialized with map_range={config.map_range}m")

    def construct_local_map(
        self,
        map_api: MapAPI,
        ego_pose: Pose,
        force_rebuild: bool = False
    ) -> BuildResult:
        """
        Construct a local map from MapAPI data.

        Args:
            map_api: MapAPI instance for querying map data
            ego_pose: Ego vehicle pose
            force_rebuild: If True, force rebuild even if cache is valid

        Returns:
            BuildResult with the constructed LocalMap or error information
        """
        try:
            # Update ego pose
            self.current_ego_pose = ego_pose

            # Initialize transformer with new ego pose
            self.transformer = CoordinateTransformer(
                ego_pose,
                self.config.coordinate_precision
            )

            # Initialize converter
            self.converter = MapConverter(self.transformer)

            # Generate cache key
            cache_key = self._generate_cache_key(ego_pose)

            # Check cache if not forcing rebuild
            if not force_rebuild:
                cached_map = self.cache_manager.get(cache_key)
                if cached_map is not None:
                    logger.debug(f"Using cached local map for key: {cache_key}")
                    self.current_local_map = cached_map
                    return BuildResult(
                        success=True,
                        local_map=cached_map,
                        build_time_ms=0.0,
                        stats={'source': 'cache'}
                    )

            # Build new local map
            logger.debug(f"Building new local map for key: {cache_key}")
            result = self._build_local_map(map_api, ego_pose)

            if result.success and result.local_map is not None:
                # Cache the result
                self.cache_manager.set(cache_key, result.local_map)
                self.current_local_map = result.local_map

            return result

        except Exception as e:
            logger.error(f"Error constructing local map: {e}")
            return BuildResult(
                success=False,
                local_map=None,
                build_time_ms=0.0,
                stats={'error': str(e)}
            )

    def update_local_map(
        self,
        map_api: MapAPI,
        new_ego_pose: Pose,
        ego_velocity: float = 0.0
    ) -> BuildResult:
        """
        Update the local map for a new ego pose.

        This method checks if the ego vehicle has moved beyond the update
        threshold. If so, it constructs a new local map.

        Args:
            map_api: MapAPI instance for querying map data
            new_ego_pose: New ego vehicle pose
            ego_velocity: Ego vehicle velocity

        Returns:
            BuildResult with the updated LocalMap or error information
        """
        try:
            # Check if we need to update
            if not self._should_update(new_ego_pose):
                # Just update metadata
                if self.current_local_map is not None:
                    self.builder.update_metadata(
                        self.current_local_map,
                        new_ego_pose,
                        ego_velocity
                    )
                    return BuildResult(
                        success=True,
                        local_map=self.current_local_map,
                        build_time_ms=0.0,
                        stats={'source': 'metadata_update'}
                    )
                else:
                    # No current map, need to build
                    return self.construct_local_map(map_api, new_ego_pose)

            # Ego moved beyond threshold, rebuild map
            logger.debug(f"Ego moved beyond threshold, rebuilding local map")
            return self.construct_local_map(map_api, new_ego_pose)

        except Exception as e:
            logger.error(f"Error updating local map: {e}")
            return BuildResult(
                success=False,
                local_map=None,
                build_time_ms=0.0,
                stats={'error': str(e)}
            )

    def _build_local_map(
        self,
        map_api: MapAPI,
        ego_pose: Pose
    ) -> BuildResult:
        """
        Internal method to build a local map from MapAPI data.

        Args:
            map_api: MapAPI instance for querying map data
            ego_pose: Ego vehicle pose

        Returns:
            BuildResult with the constructed LocalMap or error information
        """
        try:
            # Create ego position for MapAPI query
            ego_position = Position(
                latitude=ego_pose.position.x,  # Use x as latitude for local coords
                longitude=ego_pose.position.y,  # Use y as longitude for local coords
                altitude=ego_pose.position.z
            )

            # Get nearby lanelets
            lanelets = map_api.get_nearby_lanelets(
                ego_position,
                radius=self.config.map_range,
                max_count=50,
                use_local_coords=True
            )

            # Convert lanelets to lanes and collect boundary segments
            if lanelets:
                lane_conversion = self.converter.convert_lanelets_to_lanes(
                    lanelets, ego_pose
                )
                if lane_conversion.success and isinstance(lane_conversion.data, dict):
                    lanes = lane_conversion.data.get('lanes', [])
                    all_boundary_segments = lane_conversion.data.get('boundary_segments', [])
                else:
                    lanes = []
                    all_boundary_segments = []
            else:
                lanes = []
                all_boundary_segments = []

            # Get traffic signs
            traffic_signs = map_api.get_traffic_signs(
                ego_position,
                radius=self.config.map_range,
                use_local_coords=True
            )

            # Convert traffic signs
            if traffic_signs:
                sign_conversion = self.converter.convert_traffic_signs(
                    traffic_signs, ego_pose
                )
                converted_signs = sign_conversion.data if sign_conversion.success else []
            else:
                converted_signs = []

            # Get traffic lights (placeholder)
            light_conversion = self.converter.convert_traffic_lights(
                ego_position,
                self.config.map_range,
                ego_pose
            )
            traffic_lights = light_conversion.data if light_conversion.success else []

            # Build local map with boundary segments
            result = self.builder.build_local_map(
                lanes=lanes,
                traffic_lights=traffic_lights,
                traffic_signs=converted_signs,
                ego_pose=ego_pose,
                map_range=self.config.map_range,
                boundary_segments=all_boundary_segments if all_boundary_segments else None
            )

            return result

        except Exception as e:
            logger.error(f"Error in _build_local_map: {e}")
            return BuildResult(
                success=False,
                local_map=None,
                build_time_ms=0.0,
                stats={'error': str(e)}
            )

    def _should_update(self, new_ego_pose: Pose) -> bool:
        """
        Check if local map should be updated based on ego pose change.

        Args:
            new_ego_pose: New ego vehicle pose

        Returns:
            True if update is needed, False otherwise
        """
        if self.current_ego_pose is None:
            return True

        if self.current_local_map is None:
            return True

        # Calculate distance from last update position
        dx = new_ego_pose.position.x - self.current_ego_pose.position.x
        dy = new_ego_pose.position.y - self.current_ego_pose.position.y
        distance = (dx * dx + dy * dy) ** 0.5

        return distance > self.config.update_threshold

    def _generate_cache_key(self, ego_pose: Pose) -> str:
        """
        Generate a cache key based on ego pose.

        Args:
            ego_pose: Ego vehicle pose

        Returns:
            Cache key string
        """
        return self.transformer.generate_cache_key(
            ego_pose,
            self.config.cache_config.position_tolerance
        ) if self.transformer else "default"

    def get_current_local_map(self) -> Optional[LocalMap]:
        """
        Get the current local map.

        Returns:
            Current local map or None if not built
        """
        return self.current_local_map

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        return self.cache_manager.get_stats()

    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cache_manager.clear()
        logger.debug("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get constructor statistics.

        Returns:
            Dictionary containing constructor statistics
        """
        return {
            'config': {
                'map_range': self.config.map_range,
                'update_threshold': self.config.update_threshold,
                'coordinate_precision': self.config.coordinate_precision,
            },
            'cache_stats': self.get_cache_stats(),
            'current_ego_pose': self.current_ego_pose,
            'has_local_map': self.current_local_map is not None
        }
