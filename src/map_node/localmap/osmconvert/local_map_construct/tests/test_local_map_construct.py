"""
Test script for LocalMapConstruct module.

This script tests the local_map_construct module by:
1. Loading Town10HD.osm map
2. Selecting random points from the map
3. Constructing local maps at each point
4. Verifying that the conversion is complete
"""

import logging
import random
import sys
import os
from typing import List, Tuple

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

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


class LocalMapConstructTest:
    """Test class for LocalMapConstruct module."""

    def __init__(self, map_file: str = "configs/maps/Town10HD.osm"):
        """
        Initialize the test.

        Args:
            map_file: Path to the map file
        """
        self.map_file = map_file
        self.map_loader = None
        self.map_api = None
        self.constructor = None

    def setup(self) -> bool:
        """
        Set up the test environment.

        Returns:
            True if setup succeeded, False otherwise
        """
        logger.info("Setting up test environment...")

        # Load map
        self.map_loader = LocalMapLoader()
        if not self.map_loader.load_map(self.map_file):
            logger.error(f"Failed to load map from {self.map_file}")
            return False

        logger.info(f"Map loaded: {self.map_loader.map_info}")

        # Initialize MapAPI
        # LocalMapLoader uses local_x/local_y tags directly, so projector is None
        map_data = {
            'lanelet_map': self.map_loader.lanelet_map,
            'projector': None,  # No projector needed for local coordinates
            'map_info': self.map_loader.map_info
        }
        self.map_api = MapAPI(map_data)

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

        self.constructor = LocalMapConstructor(config)

        logger.info("Test environment setup complete")
        return True

    def get_random_test_points(self, num_points: int = 10) -> List[Tuple[float, float]]:
        """
        Get random test points from the map.

        Args:
            num_points: Number of random points to generate

        Returns:
            List of (x, y) tuples
        """
        logger.info(f"Generating {num_points} random test points...")

        # Get all lanelets from the map
        lanelet_points = []

        try:
            # Iterate through lanelet layer to get centerline points
            for lanelet in self.map_loader.lanelet_map.laneletLayer:
                # Get centerline points
                left_bound = lanelet.leftBound
                right_bound = lanelet.rightBound

                # Calculate centerline (average of left and right bounds)
                min_len = min(len(left_bound), len(right_bound))
                for i in range(min_len):
                    x = (left_bound[i].x + right_bound[i].x) / 2
                    y = (left_bound[i].y + right_bound[i].y) / 2
                    lanelet_points.append((x, y))

        except Exception as e:
            logger.error(f"Error getting lanelet points: {e}")
            return []

        if not lanelet_points:
            logger.warning("No lanelet points found in map")
            return []

        # Select random points
        num_samples = min(num_points, len(lanelet_points))
        random_points = random.sample(lanelet_points, num_samples)

        logger.info(f"Generated {len(random_points)} random points from {len(lanelet_points)} available")
        return random_points

    def test_local_map_construction(self, test_points: List[Tuple[float, float]]) -> dict:
        """
        Test local map construction at given points.

        Args:
            test_points: List of (x, y) tuples representing test positions

        Returns:
            Dictionary with test results
        """
        logger.info(f"\n{'='*60}")
        logger.info("Testing local map construction...")
        logger.info(f"{'='*60}\n")

        results = {
            'total_tests': len(test_points),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        for i, (x, y) in enumerate(test_points):
            logger.info(f"\nTest {i+1}/{len(test_points)}: Position ({x:.2f}, {y:.2f})")

            # Create ego pose
            ego_pose = Pose(
                position=Point3D(x=x, y=y, z=0.0),
                heading=0.0,
                pitch=0.0,
                roll=0.0
            )

            # Construct local map
            result = self.constructor.construct_local_map(self.map_api, ego_pose)

            if result.success and result.local_map:
                results['successful'] += 1

                # Verify the local map
                verification = self._verify_local_map(result.local_map)

                detail = {
                    'test_num': i + 1,
                    'position': (x, y),
                    'success': True,
                    'build_time_ms': result.build_time_ms,
                    'num_lanes': len(result.local_map.lanes),
                    'num_traffic_lights': len(result.local_map.traffic_lights),
                    'num_traffic_signs': len(result.local_map.traffic_signs),
                    'verification': verification
                }

                logger.info(f"  ✓ Success: {len(result.local_map.lanes)} lanes, "
                           f"{len(result.local_map.traffic_signs)} signs, "
                           f"{result.build_time_ms:.2f}ms")

                if not verification['valid']:
                    logger.warning(f"  ⚠ Verification warnings: {verification['warnings']}")

                results['details'].append(detail)

            else:
                results['failed'] += 1
                error_msg = result.stats.get('error', 'Unknown error')
                results['errors'].append({
                    'test_num': i + 1,
                    'position': (x, y),
                    'error': error_msg
                })

                logger.error(f"  ✗ Failed: {error_msg}")

        return results

    def _verify_local_map(self, local_map) -> dict:
        """
        Verify that a local map is properly constructed.

        Args:
            local_map: LocalMap to verify

        Returns:
            Dictionary with verification results
        """
        verification = {
            'valid': True,
            'warnings': []
        }

        # Check header
        if local_map.header is None:
            verification['valid'] = False
            verification['warnings'].append("Missing header")
        else:
            if local_map.header.frame_id != "ego_vehicle_local":
                verification['warnings'].append(f"Unexpected frame_id: {local_map.header.frame_id}")

        # Check metadata
        if local_map.metadata is None:
            verification['valid'] = False
            verification['warnings'].append("Missing metadata")
        else:
            if local_map.metadata.map_range_x <= 0:
                verification['valid'] = False
                verification['warnings'].append("Invalid map_range_x")

        # Check lanes
        if not local_map.lanes:
            verification['warnings'].append("No lanes in local map")
        else:
            for lane in local_map.lanes:
                if lane.lane_id <= 0:
                    verification['warnings'].append(f"Invalid lane_id: {lane.lane_id}")

        # Check boundary segments
        if not local_map.boundary_segments:
            verification['warnings'].append("No boundary segments in local map")

        return verification

    def print_summary(self, results: dict):
        """
        Print test summary.

        Args:
            results: Test results dictionary
        """
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total tests:      {results['total_tests']}")
        logger.info(f"Successful:       {results['successful']} ({100*results['successful']/results['total_tests']:.1f}%)")
        logger.info(f"Failed:           {results['failed']} ({100*results['failed']/results['total_tests']:.1f}%)")

        if results['errors']:
            logger.info(f"\nErrors:")
            for error in results['errors']:
                logger.info(f"  Test {error['test_num']} at {error['position']}: {error['error']}")

        # Calculate average build time
        successful_details = [d for d in results['details'] if d['success']]
        if successful_details:
            avg_build_time = sum(d['build_time_ms'] for d in successful_details) / len(successful_details)
            avg_lanes = sum(d['num_lanes'] for d in successful_details) / len(successful_details)
            avg_signs = sum(d['num_traffic_signs'] for d in successful_details) / len(successful_details)

            logger.info(f"\nAverage metrics:")
            logger.info(f"  Build time:      {avg_build_time:.2f}ms")
            logger.info(f"  Lanes per map:   {avg_lanes:.1f}")
            logger.info(f"  Signs per map:   {avg_signs:.1f}")

        # Print cache statistics
        cache_stats = self.constructor.get_cache_stats()
        logger.info(f"\nCache statistics:")
        logger.info(f"  Hit count:       {cache_stats['hit_count']}")
        logger.info(f"  Miss count:      {cache_stats['miss_count']}")
        logger.info(f"  Hit rate:         {cache_stats['hit_rate']:.2%}")

        logger.info(f"{'='*60}\n")

    def run_test(self, num_points: int = 10) -> bool:
        """
        Run the complete test.

        Args:
            num_points: Number of random points to test

        Returns:
            True if all tests passed, False otherwise
        """
        # Setup
        if not self.setup():
            return False

        # Get test points
        test_points = self.get_random_test_points(num_points)
        if not test_points:
            logger.error("No test points available")
            return False

        # Run tests
        results = self.test_local_map_construction(test_points)

        # Print summary
        self.print_summary(results)

        # Return success status
        return results['failed'] == 0


def main():
    """Main function."""
    logger.info("Starting LocalMapConstruct test...")

    # Create test instance
    test = LocalMapConstructTest(map_file="configs/maps/Town10HD.osm")

    # Run test with 10 random points
    success = test.run_test(num_points=10)

    # Exit with appropriate code
    if success:
        logger.info("✓ All tests passed!")
        sys.exit(0)
    else:
        logger.error("✗ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
