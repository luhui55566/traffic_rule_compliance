#!/usr/bin/env python3
"""
Multi-module integration test.

This script demonstrates the integration of:
1. veh_status module - extracts vehicle state data from pkl files
2. xodrconvert module - loads and processes map data
3. Local map visualization - visualizes the first and last vehicle state points with trajectory

Reference: src/map_node/localmap/xodrconvert/test/test_gps_point_localmap.py
"""

import sys
import math
from pathlib import Path
from datetime import datetime
from pyproj import Proj
from typing import Optional, Tuple, List

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from veh_status.veh_status import VehStatusReader, EgoVehicleState
from common.local_map.local_map_data import LocalMap, Pose, Point3D
from common.local_map.local_map_api import LocalMapAPI
from map_node.localmap.xodrconvert.constructor import LocalMapConstructor
from map_node.localmap.xodrconvert.config_types import ConversionConfig


# GPS calibration points for coordinate conversion
# Optimized using road constraints from optimize_offset.md
# - First frame on road 1034/769 rightmost driving lane
# - Last frame on road 530 leftmost driving lane
# - Frame ~500 on rightmost lane
#
# Calculated offset values:
#   offset_x:     -368810.882003
#   offset_y:     -3435507.781697
#   offset_z:     -1.365000
#   headingz:     0.321622°
#   rotation_rad: 0.005613

GPS_CALIBRATION_POINTS = [
    {
        "ins_data": {
            "latitude": 30.9686550,
            "longitude": 121.8846087,
            "altitude": 19.702,
        },
        "expected_xodr": {'x': 5427.88, 'y': -6691.35, 'z': 18.34}
    },
    {
        "ins_data": {
            "latitude": 30.9430940,
            "longitude": 121.8851240,
            "altitude": 30.398,
        },
        "expected_xodr": {'x': 5464.64, 'y': -9524.70, 'z': 29.03}
    }
]


def calculate_offset() -> Tuple[dict, Proj]:
    """
    Calculate coordinate offset between GPS/UTM and xodr local coordinates.
    
    Uses a 2-point calibration to determine:
    1. Rotation angle between UTM and xodr coordinate systems
    2. Translation offset (applied after rotation)
    
    Conversion formula: xodr = R * UTM + T
    Where R is rotation matrix, T is translation vector
    
    Returns:
        tuple: (offset dict, proj object)
    """
    # UTM projection for zone 51N (Shanghai area)
    proj = Proj(proj='utm', zone=51, ellps='WGS84')
    
    # Convert calibration points to UTM
    utm_points = []
    for point in GPS_CALIBRATION_POINTS:
        ins_data = point['ins_data']
        expected = point['expected_xodr']
        utm_x, utm_y = proj(ins_data['longitude'], ins_data['latitude'])
        utm_points.append({
            'utm_x': utm_x,
            'utm_y': utm_y,
            'utm_z': ins_data['altitude'],
            'xodr_x': expected['x'],
            'xodr_y': expected['y'],
            'xodr_z': expected['z']
        })
    
    # Calculate rotation angle between coordinate systems
    # Using the vector from point 0 to point 1 in both coordinate systems
    rotation_angle = 0.0
    if len(utm_points) >= 2:
        # Vector in UTM coordinates
        utm_dx = utm_points[1]['utm_x'] - utm_points[0]['utm_x']
        utm_dy = utm_points[1]['utm_y'] - utm_points[0]['utm_y']
        utm_angle = math.atan2(utm_dy, utm_dx)
        
        # Vector in xodr coordinates
        xodr_dx = utm_points[1]['xodr_x'] - utm_points[0]['xodr_x']
        xodr_dy = utm_points[1]['xodr_y'] - utm_points[0]['xodr_y']
        xodr_angle = math.atan2(xodr_dy, xodr_dx)
        
        # Rotation angle: how much to rotate UTM to align with xodr
        rotation_angle = xodr_angle - utm_angle
        
        print(f"  UTM vector angle: {math.degrees(utm_angle):.6f}°")
        print(f"  Xodr vector angle: {math.degrees(xodr_angle):.6f}°")
        print(f"  Calculated rotation angle: {math.degrees(rotation_angle):.6f}°")
    
    # Calculate translation offsets AFTER applying rotation
    # Formula: offset = xodr - rotated_utm
    cos_r = math.cos(rotation_angle)
    sin_r = math.sin(rotation_angle)
    
    offsets_x = []
    offsets_y = []
    offsets_z = []
    
    for utm_pt in utm_points:
        # Apply rotation to UTM coordinates
        rotated_x = utm_pt['utm_x'] * cos_r - utm_pt['utm_y'] * sin_r
        rotated_y = utm_pt['utm_x'] * sin_r + utm_pt['utm_y'] * cos_r
        
        # Calculate offset: offset = xodr - rotated_utm
        offsets_x.append(utm_pt['xodr_x'] - rotated_x)
        offsets_y.append(utm_pt['xodr_y'] - rotated_y)
        offsets_z.append(utm_pt['xodr_z'] - utm_pt['utm_z'])
    
    # Average the offsets
    offset = {
        'x': sum(offsets_x) / len(offsets_x),
        'y': sum(offsets_y) / len(offsets_y),
        'z': sum(offsets_z) / len(offsets_z),
        'headingx': 0.0,
        'headingy': 0.0,
        'headingz': math.degrees(rotation_angle),  # Store rotation in degrees
        'rotation_rad': rotation_angle  # Store rotation in radians for computation
    }
    
    # Verify calibration accuracy
    print(f"\n  Calibration verification:")
    for i, utm_pt in enumerate(utm_points):
        rotated_x = utm_pt['utm_x'] * cos_r - utm_pt['utm_y'] * sin_r
        rotated_y = utm_pt['utm_x'] * sin_r + utm_pt['utm_y'] * cos_r
        calc_x = rotated_x + offset['x']
        calc_y = rotated_y + offset['y']
        error_x = calc_x - utm_pt['xodr_x']
        error_y = calc_y - utm_pt['xodr_y']
        print(f"  Point {i}: error_x={error_x:.4f}m, error_y={error_y:.4f}m")
    
    return offset, proj


def convert_gps_to_xodr(state: EgoVehicleState, offset: dict, proj: Proj) -> dict:
    """
    Convert GPS coordinates to xodr local coordinates.
    
    Applies both translation offset and rotation correction.
    
    Args:
        state: EgoVehicleState object containing GPS data
        offset: Offset dict with x, y, z offsets and rotation_rad
        proj: pyproj Proj object for UTM conversion
    
    Returns:
        dict: {'x': xodr_x, 'y': xodr_y, 'z': xodr_z, 'heading': xodr_heading}
    """
    # Convert GPS to UTM
    utm_x, utm_y = proj(state.longitude, state.latitude)
    
    # Get rotation angle (default to 0 if not present)
    rotation_rad = offset.get('rotation_rad', 0.0)
    
    # Apply rotation to UTM coordinates first
    # Rotation around origin: x' = x*cos(θ) - y*sin(θ), y' = x*sin(θ) + y*cos(θ)
    cos_r = math.cos(rotation_rad)
    sin_r = math.sin(rotation_rad)
    rotated_x = utm_x * cos_r - utm_y * sin_r
    rotated_y = utm_x * sin_r + utm_y * cos_r
    
    # Apply translation offset to get xodr coordinates
    xodr_x = rotated_x + offset['x']
    xodr_y = rotated_y + offset['y']
    xodr_z = state.altitude + offset['z']
    
    # Convert heading: GPS (0=North, clockwise) to xodr (0=East, counter-clockwise)
    xodr_heading = 90.0 - state.heading
    # Normalize to [0, 360)
    while xodr_heading < 0:
        xodr_heading += 360
    while xodr_heading >= 360:
        xodr_heading -= 360
    
    # Convert to radians
    xodr_heading_rad = math.radians(xodr_heading)
    
    return {
        'x': xodr_x,
        'y': xodr_y,
        'z': xodr_z,
        'heading': xodr_heading_rad
    }


def convert_trajectory_to_local_coords(
    states: List[EgoVehicleState],
    ego_xodr_x: float,
    ego_xodr_y: float,
    ego_heading: float,
    offset: dict,
    proj: Proj,
    map_range: float = 100.0
) -> List[Point3D]:
    """
    Convert all state points to local coordinates relative to ego position.
    
    Only includes points that fall within the map_range.
    
    Args:
        states: List of EgoVehicleState objects
        ego_xodr_x: Ego x position in xodr coordinates
        ego_xodr_y: Ego y position in xodr coordinates
        ego_heading: Ego heading in radians
        offset: Coordinate offset dict
        proj: pyproj Proj object
        map_range: Maximum distance from ego to include points
    
    Returns:
        List of Point3D objects in local coordinates
    """
    local_points = []
    cos_h = math.cos(-ego_heading)  # Negative for rotation
    sin_h = math.sin(-ego_heading)
    
    for state in states:
        # Convert GPS to xodr coordinates
        xodr_coord = convert_gps_to_xodr(state, offset, proj)
        
        # Calculate offset from ego in xodr coordinates
        dx = xodr_coord['x'] - ego_xodr_x
        dy = xodr_coord['y'] - ego_xodr_y
        
        # Check if within map range
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > map_range:
            continue
        
        # Rotate to local coordinates (ego-centric)
        local_x = cos_h * dx - sin_h * dy
        local_y = sin_h * dx + cos_h * dy
        
        local_points.append(Point3D(x=local_x, y=local_y, z=0.0))
    
    return local_points


def generate_local_map_for_state(
    state: EgoVehicleState,
    states: List[EgoVehicleState],
    offset: dict,
    proj: Proj,
    xodr_file: str,
    output_dir: Path,
    map_range: float = 300.0
) -> Optional[LocalMap]:
    """
    Generate and visualize a local map for a single vehicle state with trajectory.
    
    Args:
        state: EgoVehicleState containing the ego position
        states: Full list of vehicle states for trajectory
        offset: Coordinate offset dict
        proj: pyproj Proj object
        xodr_file: Path to the xodr file
        output_dir: Output directory for visualizations
        map_range: Map range in meters
    
    Returns:
        LocalMap object if successful, None otherwise
    """
    name = f"{state.frame_name}"
    
    print("\n" + "=" * 70)
    print(f"Processing {name}")
    print("=" * 70)
    
    # Convert GPS to xodr coordinates
    xodr_coord = convert_gps_to_xodr(state, offset, proj)
    
    print(f"GPS Coordinates:")
    print(f"  Latitude:  {state.latitude:.7f}°")
    print(f"  Longitude: {state.longitude:.7f}°")
    print(f"  Altitude:  {state.altitude:.3f} m")
    print(f"  Heading:   {state.heading:.4f}°")
    
    print(f"\nConverted xodr Coordinates:")
    print(f"  X: {xodr_coord['x']:.4f} m")
    print(f"  Y: {xodr_coord['y']:.4f} m")
    print(f"  Z: {xodr_coord['z']:.4f} m")
    print(f"  Heading:   {math.degrees(xodr_coord['heading']):.2f}°")
    
    # Create conversion configuration
    config = ConversionConfig(
        eps=0.5,  # 0.5m sampling resolution
        map_range=map_range,
        include_junction_lanes=True,
        include_road_objects=True,
        include_traffic_signals=True,
        include_road_markings=True,
        ego_x=xodr_coord['x'],
        ego_y=xodr_coord['y'],
        ego_heading=xodr_coord['heading'],
        map_source_id="lgdd"
    )
    
    print(f"\nLocalMap Configuration:")
    print(f"  Ego Position: ({xodr_coord['x']:.2f}, {xodr_coord['y']:.2f})")
    print(f"  Ego Heading: {math.degrees(xodr_coord['heading']):.2f}°")
    print(f"  Map Range: {config.map_range} meters")
    
    # Create constructor and convert
    print("\nConverting to LocalMap...")
    constructor = LocalMapConstructor(config=config)
    result = constructor.convert(xodr_file)
    
    if not result.success:
        print(f"Conversion failed!")
        print(f"Errors: {result.errors}")
        return None
    
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
    
    # Convert trajectory to local coordinates
    print(f"\nConverting trajectory to local coordinates...")
    trajectory_points = convert_trajectory_to_local_coords(
        states,
        xodr_coord['x'],
        xodr_coord['y'],
        xodr_coord['heading'],
        offset,
        proj,
        map_range
    )
    print(f"  Points within map range: {len(trajectory_points)}")
    
    # Visualize and save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"localmap_{name.replace('.pkl', '')}_{timestamp}.png"
    
    api.visualize(
        title=f"Local Map at {name} (GPS: {state.latitude:.4f}, {state.longitude:.4f})\nTrajectory: {len(trajectory_points)} points",
        show_lanes=True,
        show_centerlines=True,
        show_traffic_elements=True,
        show_ego_position=True,
        show_road_ids=True,
        ego_points=[Point3D(x=0.0, y=0.0, z=0.0)],  # Ego at origin in local coords
        trajectory_points=trajectory_points,  # Add trajectory
        save_path=str(output_path),
        dpi=300
    )
    
    print(f"\nVisualization saved to: {output_path}")
    
    return local_map


def main():
    """Main function for multi-module integration test."""
    
    print("=" * 70)
    print("Multi-Module Integration Test")
    print("=" * 70)
    
    # Configuration
    pkl_directory = "datas/pkl"
    xodr_file = "configs/maps/lgdd.xodr"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Frame indices to plot (0-based)
    # Use -1 to indicate the last frame
    frame_indices = [0, 46, 100, 200, 400, 600, 800, 920, 1040, 1110, -1]  # Frame 1, 47, 1111, and last
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    print(f"\nConfiguration:")
    print(f"  PKL Directory: {project_root / pkl_directory}")
    print(f"  XODR File: {project_root / xodr_file}")
    print(f"  Output Directory: {output_dir}")
    print(f"  Frame indices to plot: {frame_indices}")
    
    # Step 1: Extract vehicle states using veh_status module
    print("\n" + "=" * 70)
    print("Step 1: Extracting vehicle states using veh_status module")
    print("=" * 70)
    
    # Create configuration for VehStatusReader
    config = {
        'vehicle': {
            'pkl_directory': pkl_directory
        }
    }
    
    reader = VehStatusReader(config)
    if not reader.init():
        print("Error: Failed to initialize VehStatusReader")
        return
    
    print(f"Found {reader.get_frame_count()} pkl files")
    
    # Extract all vehicle states for trajectory
    states = reader.process()
    print(f"Extracted {len(states)} vehicle state entries")
    
    # Resolve frame indices (convert -1 to last index)
    resolved_indices = []
    for idx in frame_indices:
        if idx == -1:
            resolved_indices.append(reader.get_frame_count() - 1)
        else:
            resolved_indices.append(idx)
    
    # Validate indices and get states
    max_idx = reader.get_frame_count() - 1
    valid_entries = []
    for orig_idx, resolved_idx in zip(frame_indices, resolved_indices):
        if resolved_idx < 0 or resolved_idx > max_idx:
            print(f"Warning: Frame index {orig_idx} is out of range (0-{max_idx}), skipping")
            continue
        
        state = reader.get_frame_by_index(resolved_idx)
        if state:
            valid_entries.append((orig_idx, resolved_idx, state))
            print(f"\nFrame {orig_idx} (index {resolved_idx}): {state.frame_name}")
            print(f"  Latitude: {state.latitude}")
            print(f"  Longitude: {state.longitude}")
            print(f"  Heading: {state.heading}")
    
    if not valid_entries:
        print("Error: No valid frame indices")
        return
    
    # Step 2: Calculate coordinate offset
    print("\n" + "=" * 70)
    print("Step 2: Calculating coordinate offset")
    print("=" * 70)
    
    offset, proj = calculate_offset()
    # Manual fine-tuning offsets (if needed after rotation correction)
    # offset['x'] += 0
    # offset['y'] += 0
    # offset['z'] += 0
    print(f"Calculated Offset:")
    print(f"  X Offset: {offset['x']:.4f} m")
    print(f"  Y Offset: {offset['y']:.4f} m")
    print(f"  Z Offset: {offset['z']:.4f} m")
    print(f"  Rotation: {offset['headingz']:.6f}° ({offset['rotation_rad']:.8f} rad)")
    
    # Step 3: Generate local maps for specified frames with trajectory
    print("\n" + "=" * 70)
    print("Step 3: Generating local maps for specified vehicle states")
    print("=" * 70)
    
    xodr_path = project_root / xodr_file
    
    # Process each specified frame
    results = []
    for orig_idx, resolved_idx, state in valid_entries:
        print(f"\n--- Processing Frame {orig_idx} (index {resolved_idx}) ---")
        local_map = generate_local_map_for_state(
            state, states, offset, proj, str(xodr_path), output_dir
        )
        results.append({
            'orig_idx': orig_idx,
            'resolved_idx': resolved_idx,
            'state': state,
            'success': local_map is not None
        })
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total pkl files processed: {reader.get_frame_count()}")
    print(f"Frames processed: {len(results)}")
    
    for r in results:
        status = 'Success' if r['success'] else 'Failed'
        print(f"  Frame {r['orig_idx']} (index {r['resolved_idx']}): {status}")
    
    all_success = all(r['success'] for r in results)
    if all_success:
        print("\nIntegration test completed successfully!")
    else:
        print("\nIntegration test completed with some failures.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
