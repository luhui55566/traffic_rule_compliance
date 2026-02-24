"""
Test script for LocalMapConstruct module with visualization.

This script tests and visualizes local_map_construct module by:
1. Loading Town10HD.osm map
2. Selecting 10 random points from the map
3. Constructing local maps at each point
4. Visualizing the local maps for manual verification

Visualizations are saved to: src/map_node/local_map_construct/test_output/
"""

import logging
import random
import sys
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np

# Set matplotlib to use non-interactive backend before importing
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from map_node.maploader.loader_local import LocalMapLoader
from map_node.maploader.visualization import MapVisualizer
from map_node.mapapi.api import MapAPI
from map_node.map_common.base import Position
from common.local_map.local_map_data import Pose, Point3D
from map_node.local_map_construct import (
    LocalMapConstructor,
    LocalMapConstructConfig,
    CacheConfig,
    LocalMapVisualizer
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output directory for test visualizations
OUTPUT_DIR = Path(__file__).parent / "test_output"
OUTPUT_DIR.mkdir(exist_ok=True)


class LocalMapConstructVisualTest:
    """Test class for LocalMapConstruct module with visualization."""

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

    def visualize_test_points(self, test_points: List[Tuple[float, float]],
                         test_headings: List[float]) -> None:
        """
        Visualize test points on the original map.

        Args:
            test_points: List of (x, y) tuples representing test positions
            test_headings: List of heading values in radians for each test point
        """
        logger.info("\nVisualizing test points on original map...")

        # Create visualizer for the original map
        viz = MapVisualizer(figsize=(14, 12))

        # Visualize map with test points
        viz.visualize_map(
            self.map_loader.lanelet_map,
            title="Original Map with 10 Random Test Points",
            show_lanelets=True,
            show_areas=False,
            show_points=True,
            save_path=None,
            use_builtin=False
        )

        # Add test points as directional arrows with heading
        for i, ((x, y), heading) in enumerate(zip(test_points, test_headings)):
            dx = 10 * np.cos(heading)
            dy = 10 * np.sin(heading)

            # Draw arrow from test point in heading direction
            viz.ax.arrow(x, y, dx, dy,
                        head_width=3, head_length=3,
                        fc='red', ec='red',
                        linewidth=2, zorder=10,
                        length_includes_head=True)

            # Add point marker at the start
            viz.ax.scatter(x, y, c='red', s=80, marker='o',
                          edgecolors='white', linewidths=2, zorder=11)

            # Add label with position info
            viz.ax.text(x + 3, y + 3,
                       f"P{i+1}\n({x:.1f}, {y:.1f})\nH:{np.degrees(heading):.1f}°",
                       fontsize=8, fontweight='bold', color='red',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                       zorder=12)

        # Update legend
        from matplotlib.lines import Line2D
        handles = [Line2D([0], [0], marker='o', color='red', linestyle='None',
                         markersize=8, markeredgecolor='white', markeredgewidth=2,
                         label='Test Point')]
        viz.ax.legend(handles=handles, loc='upper right', fontsize=10)

        # Save and show
        plt.savefig(str(OUTPUT_DIR / "00_original_map.png"), dpi=100, bbox_inches='tight')
        logger.info(f"Saved: {OUTPUT_DIR / '00_original_map.png'}")
        plt.close()

    def test_and_visualize_local_map(self, test_points: List[Tuple[float, float]],
                                   test_headings: List[float]) -> dict:
        """
        Test local map construction at given points and visualize results.

        Args:
            test_points: List of (x, y) tuples representing test positions
            test_headings: List of heading values in radians for each test point

        Returns:
            Dictionary with test results
        """
        logger.info(f"\n{'='*60}")
        logger.info("Testing local map construction with visualization...")
        logger.info(f"{'='*60}\n")

        results = {
            'total_tests': len(test_points),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }

        for i, ((x, y), heading) in enumerate(zip(test_points, test_headings)):
            logger.info(f"\nTest {i+1}/{len(test_points)}: Position ({x:.2f}, {y:.2f}), Heading {np.degrees(heading):.1f}°")

            # Create ego pose with random heading
            ego_pose = Pose(
                position=Point3D(x=x, y=y, z=0.0),
                heading=heading,
                pitch=0.0,
                roll=0.0
            )

            # Construct local map
            result = self.constructor.construct_local_map(self.map_api, ego_pose)

            if result.success and result.local_map:
                results['successful'] += 1

                # Verify local map
                verification = self._verify_local_map(result.local_map)

                detail = {
                    'test_num': i + 1,
                    'position': (x, y),
                    'heading': heading,
                    'success': True,
                    'build_time_ms': result.build_time_ms,
                    'num_lanes': len(result.local_map.lanes),
                    'num_traffic_lights': len(result.local_map.traffic_lights),
                    'num_traffic_signs': len(result.local_map.traffic_signs),
                    'verification': verification,
                    'local_map': result.local_map
                }

                logger.info(f"  ✓ Success: {len(result.local_map.lanes)} lanes, "
                           f"{len(result.local_map.traffic_signs)} signs, "
                           f"{result.build_time_ms:.2f}ms")

                if not verification['valid']:
                    logger.warning(f"  ⚠ Verification warnings: {verification['warnings']}")

                # Visualize this local map (without ego position)
                self._visualize_single_local_map(result.local_map, i + 1)

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

    def _visualize_single_local_map(
        self,
        local_map,
        test_num: int
    ) -> None:
        """
        Visualize a single local map.

        Args:
            local_map: LocalMap to visualize
            test_num: Test number
        """
        logger.info(f"  Visualizing local map for test {test_num}...")

        # Create visualizer
        viz = LocalMapVisualizer(figsize=(14, 12))

        # Visualize local map (without ego position - it's meaningless in local coordinates)
        viz.visualize_local_map(
            local_map,
            title=f"Local Map - Test {test_num}",
            show_lanes=True,
            show_centerlines=True,
            show_traffic_elements=True,
            show_ego_position=False,  # Don't show ego position in local map
            ego_points=None,
            save_path=str(OUTPUT_DIR / f"{test_num:02d}_local_map.png")
        )

        # Save and close
        plt.savefig(str(OUTPUT_DIR / f"{test_num:02d}_local_map.png"), dpi=100, bbox_inches='tight')
        logger.info(f"Saved: {OUTPUT_DIR / f'{test_num:02d}_local_map.png'}")
        plt.close()

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

        # Check if lanes exist
        if not local_map.lanes:
            verification['valid'] = False
            verification['warnings'].append("No lanes in local map")

        # Check if ego position is set
        if local_map.metadata.ego_vehicle_x == 0 and local_map.metadata.ego_vehicle_y == 0:
            verification['warnings'].append("Ego position not set")

        return verification

    def print_summary(self, results: dict):
        """
        Print test summary.

        Args:
            results: Dictionary with test results
        """
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}\n")

        logger.info(f"Total tests:      {results['total_tests']}")
        logger.info(f"Successful:       {results['successful']} ({results['successful']/results['total_tests']*100:.1f}%)")
        logger.info(f"Failed:           {results['failed']} ({results['failed']/results['total_tests']*100:.1f}%)")

        if results['details']:
            total_build_time = sum(d['build_time_ms'] for d in results['details'])
            avg_build_time = total_build_time / len(results['details'])
            total_lanes = sum(d['num_lanes'] for d in results['details'])
            avg_lanes = total_lanes / len(results['details'])
            total_signs = sum(d['num_traffic_signs'] for d in results['details'])
            avg_signs = total_signs / len(results['details'])

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

    def run_test(self, num_points: int = 10, visualize: bool = True) -> bool:
        """
        Run the complete test.

        Args:
            num_points: Number of random points to test
            visualize: Whether to show visualizations

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

        # Generate random headings for each test point
        test_headings = [random.uniform(0, 2 * np.pi) for _ in test_points]

        # Visualize test points on original map with headings
        if visualize:
            self.visualize_test_points(test_points, test_headings)

        # Run tests with headings
        results = self.test_and_visualize_local_map(test_points, test_headings)

        # Print summary
        self.print_summary(results)

        # Return success status
        return results['failed'] == 0


def main():
    """Main function."""
    logger.info("Starting LocalMapConstruct test with visualization...")

    # Create test instance
    test = LocalMapConstructVisualTest(map_file="configs/maps/Town10HD.osm")

    # Run test with 10 random points and visualization enabled
    success = test.run_test(num_points=10, visualize=True)

    # Exit with appropriate code
    if success:
        logger.info("✓ All tests passed!")
        sys.exit(0)
    else:
        logger.error("✗ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
