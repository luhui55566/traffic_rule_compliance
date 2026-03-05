"""
Test script for generating local maps at two GPS calibration points.

This script uses the two GPS points from shiftCal.py and projCal.py:
- Point 1: lat=30.9679435, lon=121.8847213, alt=19.586 -> xodr (5444.33, -6820.50, 17.89)
- Point 2: lat=30.9500814, lon=121.8856283, alt=30.048 -> xodr (5519.30, -8700.16, 29.01)

It generates and visualizes local maps centered at these two positions.
"""

import sys
import os
import math
from pathlib import Path
from datetime import datetime
from pyproj import Proj

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from common.local_map.local_map_data import LocalMap, Pose, Point3D
from common.local_map.local_map_api import LocalMapAPI
from map_node.localmap.xodrconvert.constructor import LocalMapConstructor
from map_node.localmap.xodrconvert.config_types import ConversionConfig


# GPS calibration points from shiftCal.py and projCal.py
GPS_POINTS = [
    {
        "name": "Point1",
        "ins_data": {
            "latitude": 30.9679435,
            "longitude": 121.8847213,
            "altitude": 19.586,
            "heading": 172.353515625
        },
        "expected_xodr": {'x': 5444.33, 'y': -6820.50, 'z': 17.89}
    },
    {
        "name": "Point2",
        "ins_data": {
            "latitude": 30.9500814,
            "longitude": 121.8856283,
            "altitude": 30.048,
            "heading": -178.17626953125
        },
        "expected_xodr": {'x': 5519.30, 'y': -8700.16, 'z': 29.01}
    }
]


def calculate_offset():
    """
    Calculate coordinate offset between GPS/UTM and xodr local coordinates.
    
    Offset formula: offset = xodr - UTM
    Conversion formula: xodr = UTM + offset
    
    Returns:
        tuple: (offset dict, proj object)
    """
    # UTM projection for zone 51N (Shanghai area)
    proj = Proj(proj='utm', zone=51, ellps='WGS84')
    
    # Calculate offsets from both calibration points
    offsets_x = []
    offsets_y = []
    offsets_z = []
    
    for point in GPS_POINTS:
        ins_data = point['ins_data']
        expected = point['expected_xodr']
        
        # Convert GPS to UTM
        utm_x, utm_y = proj(ins_data['longitude'], ins_data['latitude'])
        
        # Calculate offset: offset = xodr - UTM
        offsets_x.append(expected['x'] - utm_x)
        offsets_y.append(expected['y'] - utm_y)
        offsets_z.append(expected['z'] - ins_data['altitude'])
    
    # Average the offsets
    offset = {
        'x': sum(offsets_x) / len(offsets_x),
        'y': sum(offsets_y) / len(offsets_y),
        'z': sum(offsets_z) / len(offsets_z),
        'headingx': 0.0,
        'headingy': 0.0,
        'headingz': 0.0
    }
    
    return offset, proj


def convert_gps_to_xodr(latitude, longitude, altitude, heading, offset, proj):
    """
    Convert GPS coordinates to xodr local coordinates.
    
    Args:
        latitude: GPS latitude in degrees
        longitude: GPS longitude in degrees
        altitude: GPS altitude in meters
        heading: GPS heading in degrees (0=North, clockwise)
        offset: Offset dict with x, y, z offsets
        proj: pyproj Proj object for UTM conversion
    
    Returns:
        dict: {'x': xodr_x, 'y': xodr_y, 'z': xodr_z, 'heading': xodr_heading}
    """
    # Convert GPS to UTM
    utm_x, utm_y = proj(longitude, latitude)
    
    # Apply offset to get xodr coordinates
    xodr_x = utm_x + offset['x']
    xodr_y = utm_y + offset['y']
    xodr_z = altitude + offset['z']
    
    # Convert heading: GPS (0=North, clockwise) to xodr (0=East, counter-clockwise)
    xodr_heading = 90.0 - heading
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


def generate_local_map_for_point(point_info, offset, proj, xodr_file, output_dir):
    """
    Generate and visualize a local map for a single GPS point.
    
    Args:
        point_info: Dict containing GPS point information
        offset: Coordinate offset dict
        proj: pyproj Proj object
        xodr_file: Path to the xodr file
        output_dir: Output directory for visualizations
    
    Returns:
        bool: True if successful, False otherwise
    """
    name = point_info['name']
    ins_data = point_info['ins_data']
    expected = point_info['expected_xodr']
    
    print("\n" + "=" * 70)
    print(f"Processing {name}")
    print("=" * 70)
    
    # Convert GPS to xodr coordinates
    xodr_coord = convert_gps_to_xodr(
        ins_data['latitude'],
        ins_data['longitude'],
        ins_data['altitude'],
        ins_data['heading'],
        offset,
        proj
    )
    
    print(f"GPS Coordinates:")
    print(f"  Latitude:  {ins_data['latitude']:.7f}°")
    print(f"  Longitude: {ins_data['longitude']:.7f}°")
    print(f"  Altitude:  {ins_data['altitude']:.3f} m")
    print(f"  Heading:   {ins_data['heading']:.4f}°")
    
    print(f"\nConverted xodr Coordinates:")
    print(f"  X: {xodr_coord['x']:.4f} m (expected: {expected['x']:.2f} m)")
    print(f"  Y: {xodr_coord['y']:.4f} m (expected: {expected['y']:.2f} m)")
    print(f"  Z: {xodr_coord['z']:.4f} m (expected: {expected['z']:.2f} m)")
    print(f"  Heading:   {math.degrees(xodr_coord['heading']):.2f}°")
    
    # Calculate conversion error
    error_x = abs(xodr_coord['x'] - expected['x'])
    error_y = abs(xodr_coord['y'] - expected['y'])
    error_z = abs(xodr_coord['z'] - expected['z'])
    total_error = math.sqrt(error_x**2 + error_y**2 + error_z**2)
    
    print(f"\nConversion Errors:")
    print(f"  X Error: {error_x:.4f} m")
    print(f"  Y Error: {error_y:.4f} m")
    print(f"  Z Error: {error_z:.4f} m")
    print(f"  Total Error: {total_error:.4f} m")
    
    # Create conversion configuration
    config = ConversionConfig(
        eps=0.5,  # 0.5m sampling resolution
        map_range=100.0,  # 100m map range
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
        return False
    
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
    
    # Visualize and save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"localmap_{name}_{timestamp}.png"
    
    api.visualize(
        title=f"Local Map at {name} (GPS: {ins_data['latitude']:.4f}, {ins_data['longitude']:.4f})",
        show_lanes=True,
        show_centerlines=True,
        show_traffic_elements=True,
        show_ego_position=True,
        show_road_ids=True,
        ego_points=[Point3D(x=0.0, y=0.0, z=0.0)],  # Ego at origin in local coords
        save_path=str(output_path),
        dpi=300
    )
    
    print(f"\nVisualization saved to: {output_path}")
    
    return True


def main():
    """Main function for GPS point local map generation."""
    
    # Configuration
    xodr_file = "configs/maps/lgdd.xodr"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("GPS Point Local Map Generation Test")
    print("=" * 70)
    print(f"XODR file: {xodr_file}")
    print(f"Output directory: {output_dir}")
    
    # Calculate offset
    print("\n" + "=" * 70)
    print("Calculating coordinate offset...")
    print("=" * 70)
    
    offset, proj = calculate_offset()
    
    print(f"Calculated Offset:")
    print(f"  X Offset: {offset['x']:.4f} m")
    print(f"  Y Offset: {offset['y']:.4f} m")
    print(f"  Z Offset: {offset['z']:.4f} m")
    
    # Process each GPS point
    success_count = 0
    for point_info in GPS_POINTS:
        if generate_local_map_for_point(point_info, offset, proj, xodr_file, output_dir):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Processed {len(GPS_POINTS)} GPS points")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(GPS_POINTS) - success_count}")
    
    if success_count == len(GPS_POINTS):
        print("\nAll local maps generated successfully!")
    else:
        print("\nSome local maps failed to generate.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
