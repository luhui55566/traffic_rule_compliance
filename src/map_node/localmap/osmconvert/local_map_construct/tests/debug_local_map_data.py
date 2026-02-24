#!/usr/bin/env python3
"""
Debug script to print detailed local map data for inspection.
This helps identify if the issue is with data conversion or visualization.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

from map_node.maploader.loader_local import LocalMapLoader
from map_node.mapapi.api import MapAPI
from map_node.map_common.base import Position
from common.local_map.local_map_data import Pose, Point3D
from map_node.local_map_construct import LocalMapConstructor, LocalMapConstructConfig, CacheConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def print_local_map_data(local_map):
    """Print detailed information about local map data."""
    print("\n" + "="*80)
    print("LOCAL MAP DATA INSPECTION")
    print("="*80)

    # Metadata
    if local_map.metadata:
        print(f"\n[Metadata]")
        print(f"  Ego Vehicle Position: ({local_map.metadata.ego_vehicle_x:.2f}, {local_map.metadata.ego_vehicle_y:.2f})")
        print(f"  Ego Vehicle Heading: {local_map.metadata.ego_vehicle_heading:.2f} rad ({local_map.metadata.ego_vehicle_heading * 180 / 3.14159:.2f}°)")
        print(f"  Map Range: x={local_map.metadata.map_range_x:.2f}m, y={local_map.metadata.map_range_y:.2f}m")

    # Lanes
    print(f"\n[Lanes] Total: {len(local_map.lanes)}")
    if local_map.lanes:
        # Print first 3 lanes in detail
        for i, lane in enumerate(local_map.lanes[:3]):
            print(f"\n  Lane {i+1} (ID: {lane.lane_id}):")
            print(f"    Type: {lane.lane_type.name}")
            print(f"    Direction: {lane.lane_direction.name}")
            print(f"    Left boundary indices: {lane.left_boundary_segment_indices}")
            print(f"    Right boundary indices: {lane.right_boundary_segment_indices}")
            print(f"    Centerline points: {len(lane.centerline_points)}")
            if lane.centerline_points:
                first_pt = lane.centerline_points[0]
                last_pt = lane.centerline_points[-1]
                print(f"      Centerline range: x=[{first_pt.x:.2f}, {last_pt.x:.2f}], y=[{first_pt.y:.2f}, {last_pt.y:.2f}]")
            print(f"    Speed limits: {len(lane.speed_limits)}")

        if len(local_map.lanes) > 3:
            print(f"\n  ... and {len(local_map.lanes) - 3} more lanes")

    # Boundary Segments
    print(f"\n[Boundary Segments] Total: {len(local_map.boundary_segments)}")
    if local_map.boundary_segments:
        # Print first 5 boundary segments in detail
        for i, segment in enumerate(local_map.boundary_segments[:5]):
            print(f"\n  Boundary Segment {i} (ID: {segment.segment_id}):")
            print(f"    Type: {segment.boundary_type.name}")
            print(f"    Points: {len(segment.boundary_points)}")
            if segment.boundary_points:
                first_pt = segment.boundary_points[0]
                last_pt = segment.boundary_points[-1]
                print(f"      Range: x=[{first_pt.x:.2f}, {last_pt.x:.2f}], y=[{first_pt.y:.2f}, {last_pt.y:.2f}]")
                # Print first few points
                print(f"      First 3 points: {[(p.x, p.y) for p in segment.boundary_points[:3]]}")

        if len(local_map.boundary_segments) > 5:
            print(f"\n  ... and {len(local_map.boundary_segments) - 5} more boundary segments")

        # Calculate overall boundary ranges
        all_boundary_x = []
        all_boundary_y = []
        for segment in local_map.boundary_segments:
            for pt in segment.boundary_points:
                all_boundary_x.append(pt.x)
                all_boundary_y.append(pt.y)
        if all_boundary_x:
            print(f"\n  Overall boundary range:")
            print(f"    x: [{min(all_boundary_x):.2f}, {max(all_boundary_x):.2f}] (span: {max(all_boundary_x) - min(all_boundary_x):.2f}m)")
            print(f"    y: [{min(all_boundary_y):.2f}, {max(all_boundary_y):.2f}] (span: {max(all_boundary_y) - min(all_boundary_y):.2f}m)")

    # Traffic Elements
    print(f"\n[Traffic Lights] Total: {len(local_map.traffic_lights)}")
    for i, light in enumerate(local_map.traffic_lights[:3]):
        print(f"  Traffic Light {i}: pos=({light.position.x:.2f}, {light.position.y:.2f}), color={light.color.name}")

    print(f"\n[Traffic Signs] Total: {len(local_map.traffic_signs)}")
    for i, sign in enumerate(local_map.traffic_signs[:3]):
        print(f"  Traffic Sign {i}: pos=({sign.position.x:.2f}, {sign.position.y:.2f}), type={sign.sign_type.name}")

    print("\n" + "="*80)


def main():
    """Main debug function."""
    print("\n" + "="*80)
    print("LOCAL MAP DATA DEBUG SCRIPT")
    print("="*80)

    # Load map
    print("\n[1] Loading map...")
    loader = LocalMapLoader()
    map_file = Path(__file__).parent.parent.parent.parent / "configs/maps/Town10HD.osm"
    if not loader.load_map(str(map_file)):
        logger.error("Failed to load map")
        return

    map_info = loader.get_map_info()
    logger.info(f"Map loaded: {map_info}")

    # Initialize MapAPI
    print("\n[2] Initializing MapAPI...")
    map_data = loader.get_map_data()
    map_api = MapAPI(map_data)

    # Initialize LocalMapConstructor
    print("\n[3] Initializing LocalMapConstructor...")
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

    # Pick a test point (use first test point from test_with_visualization.py)
    print("\n[4] Constructing local map at test point...")
    test_x, test_y = -45.06, -88.96  # First test point
    test_heading = 25.0 * 3.14159 / 180.0  # Convert to radians
    test_pose = Pose(
        position=Point3D(x=test_x, y=test_y, z=0.0),
        heading=test_heading,
        pitch=0.0,
        roll=0.0
    )

    print(f"  Test position: ({test_x:.2f}, {test_y:.2f})")
    print(f"  Test heading: {test_heading * 180 / 3.14159:.2f}°")

    # Construct local map
    result = constructor.construct_local_map(map_api, test_pose)

    if result.local_map is None:
        logger.error(f"Failed to construct local map: {result.stats.get('error', 'Unknown error')}")
        return

    print(f"\n[5] Local map constructed successfully!")
    print(f"  Build time: {result.build_time_ms:.2f}ms")
    print(f"  Lanes: {len(result.local_map.lanes)}")
    print(f"  Boundary segments: {len(result.local_map.boundary_segments)}")
    print(f"  Traffic lights: {len(result.local_map.traffic_lights)}")
    print(f"  Traffic signs: {len(result.local_map.traffic_signs)}")

    # Print detailed data
    print_local_map_data(result.local_map)

    print("\n[6] Done!")


if __name__ == "__main__":
    main()
