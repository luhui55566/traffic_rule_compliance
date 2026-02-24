"""
Test script for XODR to LocalMap conversion at a lane point.

This script selects a point on a lane from the XODR map, converts it
to a local map, and saves a visualization.
"""

import sys
import os
import math
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from common.local_map.local_map_data import LocalMap, Pose, Point3D
from common.local_map.local_map_api import LocalMapAPI
from map_node.localmap.xodrconvert.constructor import LocalMapConstructor
from map_node.localmap.xodrconvert.config_types import ConversionConfig
from map_node.maploader.loader_xodr import XODRLoader


def test_lane_point_conversion():
    """
    Test XODR to LocalMap conversion at a selected lane point.
    
    This function:
    1. Loads the XODR map
    2. Selects a point on a lane centerline
    3. Converts to LocalMap with that point as ego position
    4. Visualizes and saves the result
    """

    # Configuration
    xodr_file = "configs/maps/Town10HD.xodr"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Load XODR map
    print("=" * 60)
    print("Loading XODR map...")
    print("=" * 60)

    loader = XODRLoader()
    if not loader.load_map(xodr_file):
        print(f"Failed to load XODR map: {xodr_file}")
        return

    odr_map = loader.odr_map
    roads = odr_map.get_roads()
    print(f"Loaded XODR map with {len(roads)} roads")

    # Select a specific road (first road)
    print("\n" + "=" * 60)
    print("Selecting a road and lane...")
    print("=" * 60)

    road = roads[0]
    road_id = road.id.decode() if isinstance(road.id, bytes) else road.id
    print(f"Selected Road ID: {road_id}")
    print(f"Road Length: {road.length:.2f}m")

    # Get lane sections
    lanesections = road.get_lanesections()
    print(f"Number of Lane Sections: {len(lanesections)}")

    if not lanesections:
        print("No lane sections found!")
        return

    # Get first lane section
    lanesection = lanesections[0]
    s_start = lanesection.s0 if hasattr(lanesection, 's0') else 0.0
    s_end = road.get_lanesection_end(lanesection)
    print(f"Lane Section s range: [{s_start:.2f}, {s_end:.2f}]")

    # Get lanes from this section
    lanes = lanesection.get_lanes()
    print(f"Number of Lanes in section: {len(lanes)}")

    if not lanes:
        print("No lanes found!")
        return

    # Find a driving lane (lane_id > 0)
    driving_lane = None
    for lane in lanes:
        lane_id = lane.id if hasattr(lane, 'id') else lane.lane_id
        if lane_id > 0:  # Driving lanes have positive ID
            driving_lane = lane
            break

    if driving_lane is None:
        print("No driving lane found, using first lane")
        driving_lane = lanes[0]

    lane_id = driving_lane.id if hasattr(driving_lane, 'id') else driving_lane.lane_id
    print(f"Selected Lane ID: {lane_id}")

    # Get a point on the lane centerline (middle of lane section)
    s = (s_start + s_end) / 2
    t = 0.0  # Center of the lane

    print(f"\nSelected point on lane centerline:")
    print(f"  s = {s:.2f}m")
    print(f"  t = {t:.2f}m")

    # Get 3D position at (s, t, h=0)
    pos = road.get_xyz(s, t, 0.0)
    ego_x = pos.array[0]
    ego_y = pos.array[1]
    ego_z = pos.array[2]

    # Calculate heading by getting position at s+delta
    delta = 1.0  # 1 meter ahead
    if s + delta < s_end:
        pos_ahead = road.get_xyz(s + delta, t, 0.0)
        heading = math.atan2(pos_ahead.array[1] - pos.array[1], pos_ahead.array[0] - pos.array[0])
    else:
        # At end of road, use s-delta
        pos_behind = road.get_xyz(s - delta, t, 0.0)
        heading = math.atan2(pos.array[1] - pos_behind.array[1], pos.array[0] - pos_behind.array[0])

    print(f"  Position: ({ego_x:.2f}, {ego_y:.2f}, {ego_z:.2f})")
    print(f"  Heading: {math.degrees(heading):.2f}°")

    # Create conversion configuration with selected ego position
    config = ConversionConfig(
        eps=1,  # 10cm sampling resolution
        map_range=200.0,  # 200m map range
        include_junction_lanes=True,
        include_road_objects=True,
        include_traffic_signals=True,
        include_road_markings=True,
        ego_x=ego_x,
        ego_y=ego_y,
        ego_heading=heading,
        map_source_id="Town10HD"
    )

    print("\n" + "=" * 60)
    print("Converting to LocalMap...")
    print("=" * 60)

    # Create constructor and convert
    constructor = LocalMapConstructor(config=config)
    result = constructor.convert(xodr_file)

    if not result.success:
        print(f"Conversion failed!")
        print(f"Errors: {result.errors}")
        return

    local_map = result.data
    print("Conversion successful!")

    # Create LocalMapAPI for visualization
    api = LocalMapAPI(local_map)

    # Print statistics
    stats = api.get_statistics()
    if stats and 'counts' in stats:
        print(f"\nLocalMap Statistics:")
        print(f"  Lanes: {stats['counts']['lanes']}")
        print(f"  Traffic Signs: {stats['counts']['traffic_signs']}")
        print(f"  Traffic Lights: {stats['counts']['traffic_lights']}")

    # Visualize and save with timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"lane_point_conversion_road_{road_id}_lane_{lane_id}_{timestamp}.png"
    api.visualize(
        title=f"Lane Point Conversion: Road {road_id}, Lane {lane_id}",
        show_lanes=True,  # 显示车道边界（带颜色和线型）
        show_centerlines=True,  # 显示中心线
        show_traffic_elements=True,
        show_ego_position=True,
        ego_points=[Point3D(x=ego_x, y=ego_y, z=ego_z)],
        save_path=str(output_path),
        dpi=150
    )

    print(f"\nVisualization saved to: {output_path}")
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_lane_point_conversion()
