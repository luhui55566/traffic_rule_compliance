"""
Example usage of MapAPI module.

This script demonstrates how to use MapAPI module to query map data.
It shows both basic queries and custom queries for traffic rule compliance.

Two usage patterns are demonstrated:
1. Parameter-based (suitable for ROS distributed nodes)
2. Shared memory-based (suitable for single-process scenarios)
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from map_node.maploader.loader import MapLoader
from map_node.maploader.utils import UtmProjectorWrapper
from lanelet2.io import Origin
from lanelet2.core import GPSPoint
from map_node.mapapi import MapManager, Position


def main():
    """Main example function."""
    print("=" * 60)
    print("MapAPI Module - Example Usage")
    print("=" * 60)
    
    # Step 1: Load map using MapLoader
    print("\n[Step 1] Loading map...")
    loader = MapLoader()
    
    # Load map with coordinate_type="local" (uses local_x/local_y tags)
    # For local coordinates, the loader internally uses Origin(0,0) to preserve values
    map_file = "../../../configs/maps/Town10HD.osm"
    success = loader.load_map(map_file, coordinate_type="local")
    
    if not success:
        print(f"Failed to load map: {map_file}")
        return
    
    print(f"Map loaded successfully!")
    map_info = loader.get_map_info()
    print(f"  - Map type: {map_info.map_type}")
    print(f"  - Number of lanelets: {map_info.num_lanelets}")
    print(f"  - Coordinate system: {map_info.coordinate_system}")
    
    # Step 2: Initialize MapManager
    print("\n[Step 2] Initializing MapManager...")
    print("\n" + "=" * 60)
    print("Usage Pattern 1: Parameter-based (ROS distributed nodes)")
    print("=" * 60)
    
    map_manager = MapManager()
    
    # Get map data from loader and pass to MapManager
    # This approach is suitable for ROS distributed nodes
    map_data = loader.get_map_data()
    map_manager.initialize(map_data=map_data)
    
    print("\n" + "=" * 60)
    print("Usage Pattern 2: Shared memory-based (single-process)")
    print("=" * 60)
    print("\nAlternatively, you can use shared memory approach:")
    print("  # MapLoader stores to shared memory")
    print("  # MapManager reads from shared memory")
    print("  map_manager.initialize()  # No parameters needed")
    print("\nNote: For this example, we use Pattern 1 (parameter-based)")
    
    if not map_manager.is_loaded():
        print("Map not loaded in MapManager!")
        return
    
    print("MapManager initialized successfully!")
    
    # Step 3: Basic queries
    print("\n[Step 3] Basic Map Queries")
    print("-" * 60)
    
    # Example position (you may need to adjust this based on your map)
    test_position = Position(latitude=0.0, longitude=0.0)
    print(f"\nQuerying position: {test_position}")
    
    # Get lanelet at position
    lanelet = map_manager.get_lanelet(test_position)
    if lanelet:
        print(f"  Lanelet ID: {lanelet.id}")
        print(f"  Lanelet Type: {lanelet.lanelet_type.value}")
        print(f"  Speed Limit: {lanelet.speed_limit} km/h")
        print(f"  Lanelet Length: {lanelet.length():.2f} m")
        print(f"  Lanelet Width: {lanelet.width():.2f} m")
        print(f"  Left Boundary Points: {len(lanelet.left_bound)}")
        print(f"  Right Boundary Points: {len(lanelet.right_bound)}")
    else:
        print("  No lanelet found at this position")
    
    # Get speed limit
    speed_limit = map_manager.get_speed_limit(test_position)
    print(f"\n  Speed Limit: {speed_limit} km/h")
    
    # Get nearby lanelets
    nearby_lanelets = map_manager.get_nearby_lanelets(test_position, radius=100.0, max_count=5)
    print(f"\n  Nearby lanelets (within 100m): {len(nearby_lanelets)}")
    for i, ll in enumerate(nearby_lanelets[:3], 1):
        print(f"    {i}. ID={ll.id}, Type={ll.lanelet_type.value}")
    
    # Get traffic signs
    traffic_signs = map_manager.get_traffic_signs(test_position, radius=200.0)
    print(f"\n  Traffic signs (within 200m): {len(traffic_signs)}")
    for i, sign in enumerate(traffic_signs[:3], 1):
        print(f"    {i}. Type={sign.sign_type.value}, Value={sign.value}")
    
    # Step 4: Lanelet topology
    print("\n[Step 4] Lanelet Topology")
    print("-" * 60)
    
    if lanelet:
        topology = map_manager.get_lanelet_topology(lanelet.id)
        print(f"\nLanelet {lanelet.id} topology:")
        print(f"  Left neighbors: {topology.get('left', [])}")
        print(f"  Right neighbors: {topology.get('right', [])}")
        print(f"  Following lanelets: {topology.get('following', [])}")
        print(f"  Preceding lanelets: {topology.get('preceding', [])}")
    
    # Step 5: Custom queries for traffic rule compliance
    print("\n[Step 5] Custom Queries for Traffic Rule Compliance")
    print("-" * 60)
    
    # Query ramp info
    ramp_info = map_manager.query_ramp_info(test_position)
    if ramp_info:
        print(f"\n  Ramp detected!")
        print(f"    Type: {ramp_info.ramp_type}")
        print(f"    Length: {ramp_info.length:.2f} m")
        print(f"    Connected lanelets: {len(ramp_info.connected_lanelets)}")
    else:
        print("\n  Not on a ramp")
    
    # Query structured road
    is_structured = map_manager.query_structured_road(test_position)
    print(f"\n  Structured road: {'Yes' if is_structured else 'No'}")
    
    # Query fishbone lines
    fishbone_lines = map_manager.query_fishbone_lines(test_position, radius=200.0)
    print(f"\n  Fishbone lines (within 200m): {len(fishbone_lines)}")
    for i, line in enumerate(fishbone_lines[:3], 1):
        print(f"    {i}. ID={line.id}, Length={line.length:.1f}m")
    
    # Query construction signs
    construction_signs = map_manager.query_construction_signs(test_position, radius=300.0)
    print(f"\n  Construction signs (within 300m): {len(construction_signs)}")
    for i, sign in enumerate(construction_signs[:3], 1):
        print(f"    {i}. ID={sign.id}, Threshold={sign.distance_threshold:.1f}m")
    
    # Step 6: Cache management
    print("\n[Step 6] Cache Management")
    print("-" * 60)
    
    status = map_manager.get_status()
    print(f"\nMapManager status:")
    print(f"  Initialized: {status['initialized']}")
    print(f"  Map loaded: {status['map_loaded']}")
    print(f"  Cache enabled: {status['cache_enabled']}")
    print(f"  Cache size: {status['cache_size']}")
    
    # Clear cache
    map_manager.clear_cache()
    print("\nCache cleared!")
    
    status = map_manager.get_status()
    print(f"Cache size after clear: {status['cache_size']}")
    
    # Step 7: Get lanelet by ID
    print("\n[Step 7] Get Lanelet by ID")
    print("-" * 60)
    
    if lanelet:
        lanelet_by_id = map_manager.get_lanelet_by_id(lanelet.id)
        if lanelet_by_id:
            print(f"\nRetrieved lanelet by ID: {lanelet_by_id.id}")
            print(f"  Type: {lanelet_by_id.lanelet_type.value}")
            print(f"  Speed limit: {lanelet_by_id.speed_limit}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
