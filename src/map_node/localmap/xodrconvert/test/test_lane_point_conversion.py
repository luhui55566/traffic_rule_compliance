"""
Test script for XODR to LocalMap conversion at a lane point.

This script selects a point on a lane from the XODR map, converts it
to a local map, and saves a visualization.
"""

import sys
import os
import math
import random
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from common.local_map.local_map_data import LocalMap, Pose, Point3D
from common.local_map.local_map_api import LocalMapAPI
from map_node.localmap.xodrconvert.constructor import LocalMapConstructor
from map_node.localmap.xodrconvert.config_types import ConversionConfig
from map_node.maploader.loader_xodr import XODRLoader


def test_lane_point_conversion(prefer_junction: bool = False):
    """
    Test XODR to LocalMap conversion at a selected lane point.
    
    This function:
    1. Loads the XODR map
    2. Selects a point on a lane centerline
    3. Converts to LocalMap with that point as ego position
    4. Visualizes and saves the result
    
    Args:
        prefer_junction: If True, prefer selecting a point on a junction road
    """

    # Configuration
    xodr_file = "configs/maps/lgdd.xodr"#lgdd Town10HD
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

    # Select a road (prefer junction road if requested)
    print("\n" + "=" * 60)
    if prefer_junction:
        print("Selecting a JUNCTION road and lane...")
    else:
        print("Randomly selecting a road and lane...")
    print("=" * 60)
    
    # Find junction roads (roads with junction attribute != -1)
    junction_roads = []
    normal_roads = []
    for r in roads:
        junction_attr = r.junction if hasattr(r, 'junction') else -1
        if isinstance(junction_attr, bytes):
            junction_attr = int(junction_attr)
        if junction_attr != -1:
            junction_roads.append(r)
        else:
            normal_roads.append(r)
    
    print(f"Found {len(junction_roads)} junction roads and {len(normal_roads)} normal roads")
    
    # Select road based on preference
    if prefer_junction and junction_roads:
        road = random.choice(junction_roads)
        print(f"Selected a JUNCTION road")
    else:
        road = random.choice(roads)
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

    # Randomly select a point on the lane centerline
    s = random.uniform(s_start, s_end)
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
        map_range=100.0,  # 300m map range
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
    print("Conversion Configuration:")
    print("=" * 60)
    print(f"  Ego Position: ({ego_x:.2f}, {ego_y:.2f})")
    print(f"  Ego Heading: {math.degrees(heading):.2f}°")
    print(f"  Map Range: {config.map_range} meters")
    print(f"  Expected bounds: [{ego_x-config.map_range:.2f}, {ego_x+config.map_range:.2f}] x [{ego_y-config.map_range:.2f}, {ego_y+config.map_range:.2f}]")
    
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
    
    # Check junction lanes and their boundaries
    print("\n" + "=" * 60)
    print("DIAGNOSTIC: Checking junction lanes and boundaries")
    print("=" * 60)
    
    junction_lanes = [lane for lane in local_map.lanes if lane.junction_id is not None]
    normal_lanes = [lane for lane in local_map.lanes if lane.junction_id is None]
    print(f"Junction lanes: {len(junction_lanes)}")
    print(f"Normal lanes: {len(normal_lanes)}")
    
    # Check boundary segments for junction lanes
    junction_boundary_count = 0
    for lane in junction_lanes:
        junction_boundary_count += len(lane.left_boundary_segment_indices)
        junction_boundary_count += len(lane.right_boundary_segment_indices)
    print(f"Boundary indices for junction lanes: {junction_boundary_count}")
    
    # Check actual boundary segments
    junction_boundary_segments = 0
    empty_boundary_segments = 0
    for segment in local_map.boundary_segments:
        # Check if segment has any points
        if segment.boundary_points:
            junction_boundary_segments += 1
        else:
            empty_boundary_segments += 1
    print(f"Total boundary segments with points: {junction_boundary_segments}")
    print(f"Total boundary segments WITHOUT points: {empty_boundary_segments}")
    
    # Sample a few junction lanes to see their boundary info
    print("\nSample junction lanes (first 5):")
    for i, lane in enumerate(junction_lanes[:5]):
        print(f"  Lane {lane.lane_id}:")
        print(f"    Road ID: {lane.road_id}, Junction ID: {lane.junction_id}")
        print(f"    Centerline points: {len(lane.centerline_points)}")
        print(f"    Left boundaries: {len(lane.left_boundary_segment_indices)}")
        print(f"    Right boundaries: {len(lane.right_boundary_segment_indices)}")
    
    # === NEW DIAGNOSTIC: Check segmented boundary data ===
    print("\n" + "=" * 60)
    print("DIAGNOSTIC: Checking segmented boundary data (CRITICAL FOR VISUALIZATION)")
    print("=" * 60)
    
    segments_with_full_data = 0
    segments_with_partial_data = 0
    segments_with_no_segmented_data = 0
    segments_with_points_but_no_data = 0
    
    for i, segment in enumerate(local_map.boundary_segments):
        has_points = len(segment.boundary_points) > 0
        has_color = bool(segment.boundary_colors)
        has_shape = bool(segment.boundary_line_shapes)
        has_thickness = bool(segment.boundary_thicknesses)
        
        if has_points:
            if has_color and has_shape and has_thickness:
                segments_with_full_data += 1
            elif has_color or has_shape or has_thickness:
                segments_with_partial_data += 1
                print(f"  Segment {i}: PARTIAL DATA - points={len(segment.boundary_points)}, "
                      f"color={len(segment.boundary_colors)}, "
                      f"shape={len(segment.boundary_line_shapes)}, "
                      f"thickness={len(segment.boundary_thicknesses)}")
            else:
                segments_with_no_segmented_data += 1
                segments_with_points_but_no_data += 1
                if segments_with_points_but_no_data <= 10:  # Only print first 10
                    print(f"  Segment {i}: HAS POINTS ({len(segment.boundary_points)}) BUT NO PER-POINT DATA - WILL BE SKIPPED IN VISUALIZATION!")
    
    print(f"\nBoundary Segment Summary:")
    print(f"  Segments with full segmented data: {segments_with_full_data}")
    print(f"  Segments with partial segmented data: {segments_with_partial_data}")
    print(f"  Segments with points but NO segmented data: {segments_with_no_segmented_data}")
    print(f"  (These {segments_with_no_segmented_data} segments will be SKIPPED during visualization!)")
    
    # Check if junction lanes' boundary segments have segmented data
    print("\n" + "=" * 60)
    print("DIAGNOSTIC: Junction lane boundary segment details")
    print("=" * 60)
    
    junction_boundary_segment_ids = set()
    for lane in junction_lanes:
        for idx in lane.left_boundary_segment_indices:
            junction_boundary_segment_ids.add(idx)
        for idx in lane.right_boundary_segment_indices:
            junction_boundary_segment_ids.add(idx)
    
    print(f"Total unique boundary segment IDs referenced by junction lanes: {len(junction_boundary_segment_ids)}")
    
    # Find these segments and check their data
    segments_found = 0
    segments_missing_data = 0
    for segment in local_map.boundary_segments:
        if segment.segment_id in junction_boundary_segment_ids:
            segments_found += 1
            has_data = (segment.boundary_colors and
                       segment.boundary_line_shapes and
                       segment.boundary_thicknesses)
            if not has_data:
                segments_missing_data += 1
                if segments_missing_data <= 5:
                    print(f"  Junction boundary segment {segment.segment_id}: "
                          f"points={len(segment.boundary_points)}, "
                          f"colors={len(segment.boundary_colors) if segment.boundary_colors else 0}, "
                          f"shapes={len(segment.boundary_line_shapes) if segment.boundary_line_shapes else 0}, "
                          f"thicknesses={len(segment.boundary_thicknesses) if segment.boundary_thicknesses else 0}")
    
    print(f"\nJunction boundary segments found: {segments_found}")
    print(f"Junction boundary segments MISSING segmented data: {segments_missing_data}")
    # === END NEW DIAGNOSTIC ===

    # === DIAGNOSTIC: Speed Limit Data ===
    print("\n" + "=" * 60)
    print("DIAGNOSTIC: Checking per-point speed limit data")
    print("=" * 60)
    
    lanes_with_speed_limits = 0
    lanes_without_speed_limits = 0
    total_points_with_speed = 0
    total_points_without_speed = 0
    sample_speed_data = []
    
    for lane in local_map.lanes:
        has_speed_limits = len(lane.max_speed_limits) > 0
        if has_speed_limits:
            lanes_with_speed_limits += 1
            total_points_with_speed += len(lane.max_speed_limits)
            # Collect sample data (first 3 lanes with speed limits)
            if len(sample_speed_data) < 3:
                # Get unique speed values
                unique_speeds = set(lane.max_speed_limits)
                sample_speed_data.append({
                    'lane_id': lane.lane_id,
                    'road_id': lane.road_id,
                    'centerline_points': len(lane.centerline_points),
                    'speed_points': len(lane.max_speed_limits),
                    'unique_max_speeds': sorted([f"{s:.1f}" for s in unique_speeds if s > 0]),
                    'has_min_speeds': any(s > 0 for s in lane.min_speed_limits)
                })
        else:
            lanes_without_speed_limits += 1
            total_points_without_speed += len(lane.centerline_points)
    
    print(f"Lanes with speed limits: {lanes_with_speed_limits}")
    print(f"Lanes without speed limits: {lanes_without_speed_limits}")
    print(f"Total centerline points with speed data: {total_points_with_speed}")
    print(f"Total centerline points without speed data: {total_points_without_speed}")
    
    if sample_speed_data:
        print("\nSample lanes with speed limit data:")
        for i, data in enumerate(sample_speed_data):
            print(f"  Sample {i+1}: Lane {data['lane_id']} (Road {data['road_id']})")
            print(f"    Centerline points: {data['centerline_points']}")
            print(f"    Speed limit points: {data['speed_points']}")
            print(f"    Unique max speeds (m/s): {data['unique_max_speeds']}")
            print(f"    Has min speeds: {data['has_min_speeds']}")
    # === END DIAGNOSTIC: Speed Limit Data ===

    # === DIAGNOSTIC: Lane Predecessor/Successor Connections ===
    print("\n" + "=" * 60)
    print("DIAGNOSTIC: Checking lane predecessor/successor connections")
    print("=" * 60)
    
    lanes_with_predecessors = 0
    lanes_with_successors = 0
    lanes_with_both = 0
    lanes_with_neither = 0
    total_predecessor_connections = 0
    total_successor_connections = 0
    
    # Sample lanes with connections
    sample_connected_lanes = []
    sample_unconnected_lanes = []
    
    for lane in local_map.lanes:
        has_pred = len(lane.predecessor_lane_ids) > 0
        has_succ = len(lane.successor_lane_ids) > 0
        
        total_predecessor_connections += len(lane.predecessor_lane_ids)
        total_successor_connections += len(lane.successor_lane_ids)
        
        if has_pred:
            lanes_with_predecessors += 1
        if has_succ:
            lanes_with_successors += 1
        if has_pred and has_succ:
            lanes_with_both += 1
        if not has_pred and not has_succ:
            lanes_with_neither += 1
        
        # Collect samples
        if has_pred or has_succ:
            if len(sample_connected_lanes) < 5:
                sample_connected_lanes.append({
                    'lane_id': lane.lane_id,
                    'road_id': lane.road_id,
                    'original_lane_id': lane.original_lane_id,
                    'predecessor_ids': lane.predecessor_lane_ids,
                    'successor_ids': lane.successor_lane_ids,
                    'is_junction': lane.junction_id is not None
                })
        else:
            if len(sample_unconnected_lanes) < 5 and lane.junction_id is None:
                sample_unconnected_lanes.append({
                    'lane_id': lane.lane_id,
                    'road_id': lane.road_id,
                    'original_lane_id': lane.original_lane_id,
                    'is_junction': lane.junction_id is not None
                })
    
    print(f"Lane connection statistics:")
    print(f"  Total lanes: {len(local_map.lanes)}")
    print(f"  Lanes with predecessors: {lanes_with_predecessors}")
    print(f"  Lanes with successors: {lanes_with_successors}")
    print(f"  Lanes with both: {lanes_with_both}")
    print(f"  Lanes with neither: {lanes_with_neither}")
    print(f"  Total predecessor connections: {total_predecessor_connections}")
    print(f"  Total successor connections: {total_successor_connections}")
    
    if sample_connected_lanes:
        print("\nSample connected lanes (first 5):")
        for data in sample_connected_lanes:
            print(f"  Lane {data['lane_id']} (Road {data['road_id']}, orig_id={data['original_lane_id']}):")
            print(f"    Predecessors: {data['predecessor_ids']}")
            print(f"    Successors: {data['successor_ids']}")
            print(f"    Is junction: {data['is_junction']}")
    
    if sample_unconnected_lanes:
        print("\nSample unconnected lanes (first 5 non-junction):")
        for data in sample_unconnected_lanes:
            print(f"  Lane {data['lane_id']} (Road {data['road_id']}, orig_id={data['original_lane_id']}):")
            print(f"    Is junction: {data['is_junction']}")
    
    # Check road-level predecessor/successor info
    print("\nRoad-level connections:")
    roads_with_pred = sum(1 for r in local_map.roads if r.predecessor_road_id is not None)
    roads_with_succ = sum(1 for r in local_map.roads if r.successor_road_id is not None)
    roads_with_pred_junction = sum(1 for r in local_map.roads if r.predecessor_junction_id is not None)
    roads_with_succ_junction = sum(1 for r in local_map.roads if r.successor_junction_id is not None)
    print(f"  Roads with predecessor_road_id: {roads_with_pred}")
    print(f"  Roads with successor_road_id: {roads_with_succ}")
    print(f"  Roads with predecessor_junction_id: {roads_with_pred_junction}")
    print(f"  Roads with successor_junction_id: {roads_with_succ_junction}")
    # === END DIAGNOSTIC: Lane Predecessor/Successor Connections ===

    # === DIAGNOSTIC LOGS ===
    print("\n" + "=" * 60)
    print("DIAGNOSTIC: Checking actual data range vs expected range")
    print("=" * 60)
    
    # NOTE: Data points are in LOCAL coordinates (ego at origin)
    # So distance from ego is simply sqrt(x^2 + y^2)
    all_points = []
    for lane in local_map.lanes:
        for point in lane.centerline_points:
            # In local coords, ego is at (0,0), so distance is sqrt(x^2 + y^2)
            dist = math.sqrt(point.x**2 + point.y**2)
            all_points.append((point.x, point.y, dist))
    
    for segment in local_map.boundary_segments:
        for point in segment.boundary_points:
            dist = math.sqrt(point.x**2 + point.y**2)
            all_points.append((point.x, point.y, dist))
    
    if all_points:
        xs, ys, dists = zip(*all_points)
        print(f"Ego Position (global): ({ego_x:.2f}, {ego_y:.2f})")
        print(f"Expected range: {config.map_range}m")
        print(f"Actual data bounds (LOCAL coordinates, ego at origin):")
        print(f"  X: [{min(xs):.2f}, {max(xs):.2f}] (span: {max(xs)-min(xs):.2f}m)")
        print(f"  Y: [{min(ys):.2f}, {max(ys):.2f}] (span: {max(ys)-min(ys):.2f}m)")
        print(f"Distance from ego (in local coords):")
        print(f"  Min: {min(dists):.2f}m")
        print(f"  Max: {max(dists):.2f}m")
        print(f"  Points >300m: {sum(1 for d in dists if d > 300)}")
        print(f"  Points >500m: {sum(1 for d in dists if d > 500)}")
        print(f"  Points >1000m: {sum(1 for d in dists if d > 1000)}")
        print(f"  Total points: {len(dists)}")
    
    # Check metadata
    if local_map.metadata:
        print(f"\nLocalMap Metadata:")
        print(f"  map_range_x: {local_map.metadata.map_range_x}")
        print(f"  map_range_y: {local_map.metadata.map_range_y}")
        print(f"  ego_vehicle_x (global): {local_map.metadata.ego_vehicle_x}")
        print(f"  ego_vehicle_y (global): {local_map.metadata.ego_vehicle_y}")
    # === END DIAGNOSTIC LOGS ===

    # Visualize and save with timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"lane_point_conversion_road_{road_id}_lane_{lane_id}_{timestamp}.png"
    api.visualize(
        title=f"Lane Point Conversion: Road {road_id}, Lane {lane_id}",
        show_lanes=True,  # 显示车道边界（带颜色和线型）
        show_centerlines=True,  # 显示中心线
        show_traffic_elements=True,
        show_ego_position=True,
        show_road_ids=True,  # 显示Road ID标签
        # Note: ego_points should be in local coordinates (ego at origin)
        # Since data is in local coords, we pass (0,0,0) to mark ego position
        ego_points=[Point3D(x=0.0, y=0.0, z=0.0)],
        save_path=str(output_path),
        dpi=300  # Higher DPI for better resolution
    )

    print(f"\nVisualization saved to: {output_path}")
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test XODR to LocalMap conversion")
    parser.add_argument("--junction", action="store_true", help="Prefer selecting a junction road")
    args = parser.parse_args()
    
    test_lane_point_conversion(prefer_junction=args.junction)
