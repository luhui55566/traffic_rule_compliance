"""
Test script for XODR map loader.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from map_node.maploader import create_loader, XODRLoader, XODRMapData

def test_xodr_loader():
    """Test loading XODR map."""
    print("=" * 60)
    print("Testing XODR Map Loader")
    print("=" * 60)
    
    # Create XODR loader
    loader = create_loader("xodr")
    print(f"Created loader: {type(loader).__name__}")
    
    # Load the map
    map_path = "configs/maps/Town10HD.xodr"
    print(f"Loading map from: {map_path}")
    
    success = loader.load_map(map_path)
    
    if not success:
        print("ERROR: Failed to load map!")
        return False
    
    print("SUCCESS: Map loaded successfully!")
    
    # Get map info
    map_info = loader.get_map_info()
    print(f"\nMap Info:")
    print(f"  Type: {map_info.map_type}")
    print(f"  File: {map_info.file_path}")
    print(f"  Num Lanelets: {map_info.num_lanelets}")
    print(f"  Coordinate System: {map_info.coordinate_system}")
    print(f"  Is Loaded: {map_info.is_loaded}")
    
    # Get map data
    map_data = loader.get_map_data()
    
    if isinstance(map_data, XODRMapData):
        print(f"\nXODR Map Data:")
        roads = map_data.get_roads()
        print(f"  Number of roads: {len(roads)}")
        
        # Show first few roads
        for i, road in enumerate(roads[:5]):
            road_id = road.id.decode() if isinstance(road.id, bytes) else road.id
            print(f"  Road {i+1}: ID={road_id}, Length={road.length:.2f}m")
        
        if len(roads) > 5:
            print(f"  ... and {len(roads) - 5} more roads")
        
        # Get lane sections for first road
        if len(roads) > 0:
            first_road = roads[0]
            lanesections = map_data.get_lanesections(first_road)
            print(f"\nFirst road lane sections: {len(lanesections)}")
            
            if len(lanesections) > 0:
                first_lanesection = lanesections[0]
                lanes = map_data.get_lanes(first_lanesection)
                print(f"  First lane section lanes: {len(lanes)}")
                
                for lane in lanes[:3]:
                    lane_id = lane.id.decode() if isinstance(lane.id, bytes) else lane.id
                    print(f"    Lane ID: {lane_id}, Type: {lane.type.decode() if isinstance(lane.type, bytes) else lane.type}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_xodr_loader()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
