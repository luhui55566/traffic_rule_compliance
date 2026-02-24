"""
Simple debug script to test Position class availability.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

# Try importing Position
try:
    from common.local_map.local_map_data import Point3D
    print("✓ Successfully imported Point3D from common.local_map.local_map_data")
except ImportError as e:
    print(f"✗ Failed to import Point3D: {e}")
    sys.exit(1)
