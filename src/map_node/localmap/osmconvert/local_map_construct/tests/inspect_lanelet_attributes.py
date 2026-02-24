#!/usr/bin/env python3
"""Script to inspect lanelet attributes in the map."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from map_node.maploader.loader_local import LocalMapLoader
from lanelet2.core import Lanelet
from lanelet2.io import Origin

def inspect_lanelet_attributes(map_file):
    """Inspect lanelet attributes in the map."""
    
    # Load map
    print(f"Loading map from: {map_file}")
    loader = LocalMapLoader()
    if not loader.load_map(map_file):
        print("Failed to load map")
        return
    
    map_data = loader.get_map_data()
    lanelet_map = map_data['lanelet_map']
    
    print(f"\n{'='*80}")
    print("LANELET ATTRIBUTES INSPECTION")
    print(f"{'='*80}")
    
    # Get all lanelets
    lanelets = list(lanelet_map.laneletLayer)
    print(f"\nTotal lanelets: {len(lanelets)}")
    
    # Inspect first few lanelets
    for i, lanelet in enumerate(lanelets[:5]):
        print(f"\n{'-'*80}")
        print(f"Lanelet {i+1} (ID: {lanelet.id})")
        print(f"{'-'*80}")
        
        # Print all attributes
        print(f"\nAttributes:")
        for key in lanelet.attributes:
            value = lanelet.attributes[key]
            print(f"  {key}: {value}")
        
        # Check left and right boundaries
        print(f"\nLeft boundary points: {len(lanelet.leftBound)}")
        if lanelet.leftBound:
            print(f"  First point: ({lanelet.leftBound[0].x:.2f}, {lanelet.leftBound[0].y:.2f}, {lanelet.leftBound[0].z:.2f})")
            print(f"  Last point: ({lanelet.leftBound[-1].x:.2f}, {lanelet.leftBound[-1].y:.2f}, {lanelet.leftBound[-1].z:.2f})")
            
            # Check left boundary attributes
            print(f"  Left boundary attributes:")
            for key in lanelet.leftBound.attributes:
                value = lanelet.leftBound.attributes[key]
                print(f"    {key}: {value}")
        
        print(f"\nRight boundary points: {len(lanelet.rightBound)}")
        if lanelet.rightBound:
            print(f"  First point: ({lanelet.rightBound[0].x:.2f}, {lanelet.rightBound[0].y:.2f}, {lanelet.rightBound[0].z:.2f})")
            print(f"  Last point: ({lanelet.rightBound[-1].x:.2f}, {lanelet.rightBound[-1].y:.2f}, {lanelet.rightBound[-1].z:.2f})")
            
            # Check right boundary attributes
            print(f"  Right boundary attributes:")
            for key in lanelet.rightBound.attributes:
                value = lanelet.rightBound.attributes[key]
                print(f"    {key}: {value}")
        
        # Check regulatory elements
        print(f"\nRegulatory elements: {len(lanelet.regulatoryElements)}")
        for reg_elem in lanelet.regulatoryElements:
            print(f"  Type: {type(reg_elem).__name__}")
            print(f"  ID: {reg_elem.id}")
            for key in reg_elem.attributes:
                value = reg_elem.attributes[key]
                print(f"    {key}: {value}")
    
    # Collect all unique attribute keys
    print(f"\n{'='*80}")
    print("ALL UNIQUE ATTRIBUTE KEYS")
    print(f"{'='*80}")
    
    all_keys = set()
    for lanelet in lanelets:
        all_keys.update(lanelet.attributes.keys())
        if lanelet.leftBound:
            all_keys.update(lanelet.leftBound.attributes.keys())
        if lanelet.rightBound:
            all_keys.update(lanelet.rightBound.attributes.keys())
        for reg_elem in lanelet.regulatoryElements:
            all_keys.update(reg_elem.attributes.keys())
    
    print(f"\nTotali unique attribute keys: {len(all_keys)}")
    for key in sorted(all_keys):
        print(f"  {key}")
    
    # Collect all unique values for specific keys
    print(f"\n{'='*80}")
    print("ATTRIBUTE VALUES FOR COMMON KEYS")
    print(f"{'='*80}")
    
    keys_of_interest = ['type', 'subtype', 'speed_limit', 'maxspeed', 'location', 'one_way', 'width']
    
    for key in keys_of_interest:
        if key in all_keys:
            print(f"\n{key}:")
            values = set()
            for lanelet in lanelets:
                if key in lanelet.attributes:
                    values.add(lanelet.attributes[key])
                if lanelet.leftBound and key in lanelet.leftBound.attributes:
                    values.add(lanelet.leftBound.attributes[key])
                if lanelet.rightBound and key in lanelet.rightBound.attributes:
                    values.add(lanelet.rightBound.attributes[key])
                for reg_elem in lanelet.regulatoryElements:
                    if key in reg_elem.attributes:
                        values.add(reg_elem.attributes[key])
            for value in sorted(values):
                print(f"  {value}")
        else:
            print(f"\n{key}: NOT FOUND")

def main():
    """Main function."""
    map_file = "configs/maps/Town10HD.osm"
    inspect_lanelet_attributes(map_file)

if __name__ == "__main__":
    main()
