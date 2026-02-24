"""
Simple test script for LocalMapConstruct module.
"""

import logging
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from map_node.maploader.loader_local import LocalMapLoader
from map_node.mapapi.api import MapAPI
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
    """Main function."""
    logger.info("Starting simple LocalMapConstruct test...")

    # Load map
    logger.info("Loading map...")
    map_loader = LocalMapLoader()
    if not map_loader.load_map("configs/maps/Town10HD.osm"):
        logger.error("Failed to load map")
        return False

    logger.info(f"Map loaded: {map_loader.map_info}")

    # Initialize MapAPI
    map_data = {
        'lanelet_map': map_loader.lanelet_map,
        'projector': None,
        'map_info': map_loader.map_info
    }
    map_api = MapAPI(map_data)

    # Configure LocalMapConstructor
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

    constructor = LocalMapConstructor(config)

    logger.info("LocalMapConstructor initialized")

    # Test with a single point
    logger.info("Testing with a single point...")
    ego_pose = Pose(
        position=Point3D(x=0.0, y=0.0, z=0.0),
        heading=0.0,
        pitch=0.0,
        roll=0.0
    )

    logger.info("Constructing local map at (0, 0)...")
    result = constructor.construct_local_map(map_api, ego_pose)

    if result.success:
        logger.info(f"✓ Success: {len(result.local_map.lanes)} lanes, "
                   f"{len(result.local_map.traffic_signs)} signs, "
                   f"{result.build_time_ms:.2f}ms")
        return True
    else:
        logger.error(f"✗ Failed: {result.stats.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
