"""
Example usage of LocalMapConstruct module.

This script demonstrates how to use the LocalMapConstruct module to
build local maps from MapAPI data.
"""

import logging
from map_node.maploader.loader_local import LocalMapLoader
from map_node.mapapi.api import MapAPI
from map_node.map_common.base import Position
from common.local_map.local_map_data import Pose, Point3D
from map_node.local_map_construct import (
    LocalMapConstructor,
    LocalMapConstructConfig,
    CacheConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function demonstrating LocalMapConstruct usage."""

    # Step 1: Load map data
    logger.info("Loading map data...")
    map_loader = LocalMapLoader()

    map_file = "configs/maps/Town10HD.osm"
    if not map_loader.load_map(map_file):
        logger.error(f"Failed to load map from {map_file}")
        return

    # Get map data for MapAPI
    map_data = {
        'lanelet_map': map_loader.lanelet_map,
        'projector': map_loader.projector,
        'map_info': map_loader.map_info
    }

    # Step 2: Initialize MapAPI
    logger.info("Initializing MapAPI...")
    map_api = MapAPI(map_data)

    # Step 3: Configure LocalMapConstructor
    cache_config = CacheConfig(
        enabled=True,
        max_size=10,
        ttl_seconds=1.0,
        position_tolerance=5.0
    )

    config = LocalMapConstructConfig(
        map_range=200.0,
        update_threshold=50.0,
        cache_config=cache_config,
        coordinate_precision=0.01
    )

    # Step 4: Initialize LocalMapConstructor
    logger.info("Initializing LocalMapConstructor...")
    constructor = LocalMapConstructor(config)

    # Step 5: Define ego vehicle pose
    ego_pose = Pose(
        position=Point3D(x=0.0, y=0.0, z=0.0),
        heading=0.0,
        pitch=0.0,
        roll=0.0
    )

    # Step 6: Construct local map
    logger.info("Constructing local map...")
    result = constructor.construct_local_map(map_api, ego_pose)

    if result.success and result.local_map:
        logger.info(f"Successfully built local map!")
        logger.info(f"  - Lanes: {len(result.local_map.lanes)}")
        logger.info(f"  - Traffic lights: {len(result.local_map.traffic_lights)}")
        logger.info(f"  - Traffic signs: {len(result.local_map.traffic_signs)}")
        logger.info(f"  - Build time: {result.build_time_ms:.2f}ms")

        # Print lane information
        for i, lane in enumerate(result.local_map.lanes[:5]):  # Show first 5 lanes
            logger.info(f"  Lane {i}: ID={lane.lane_id}, "
                       f"Type={lane.lane_type.name}, "
                       f"Centerline points={len(lane.centerline_points)}")
    else:
        logger.error(f"Failed to build local map: {result.stats}")

    # Step 7: Update local map with new ego pose
    logger.info("\nUpdating local map with new ego pose...")
    new_ego_pose = Pose(
        position=Point3D(x=10.0, y=5.0, z=0.0),
        heading=0.1,
        pitch=0.0,
        roll=0.0
    )

    update_result = constructor.update_local_map(map_api, new_ego_pose)

    if update_result.success and update_result.local_map:
        source = update_result.stats.get('source', 'unknown')
        logger.info(f"Local map updated (source: {source})")

    # Step 8: Get cache statistics
    cache_stats = constructor.get_cache_stats()
    logger.info(f"\nCache statistics:")
    logger.info(f"  - Enabled: {cache_stats['enabled']}")
    logger.info(f"  - Size: {cache_stats['current_size']}/{cache_stats['max_size']}")
    logger.info(f"  - Hit count: {cache_stats['hit_count']}")
    logger.info(f"  - Miss count: {cache_stats['miss_count']}")
    logger.info(f"  - Hit rate: {cache_stats['hit_rate']:.2%}")

    # Step 9: Get constructor statistics
    stats = constructor.get_stats()
    logger.info(f"\nConstructor statistics:")
    logger.info(f"  - Map range: {stats['config']['map_range']}m")
    logger.info(f"  - Update threshold: {stats['config']['update_threshold']}m")
    logger.info(f"  - Has local map: {stats['has_local_map']}")


if __name__ == "__main__":
    main()
