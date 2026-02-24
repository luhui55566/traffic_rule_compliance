"""
Test suite for MapLoader module.
"""

import os
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from map_node.map_common.base import Position, BoundingBox, MapInfo
from map_node.maploader.utils import UtmProjectorWrapper
from map_node.maploader.loader import MapLoader


class TestPosition(unittest.TestCase):
    """Test cases for Position class."""
    
    def test_position_creation(self):
        """Test Position object creation."""
        pos = Position(latitude=39.9042, longitude=116.4074)
        self.assertEqual(pos.latitude, 39.9042)
        self.assertEqual(pos.longitude, 116.4074)
        self.assertIsNone(pos.altitude)
    
    def test_position_with_altitude(self):
        """Test Position with altitude."""
        pos = Position(latitude=39.9042, longitude=116.4074, altitude=50.0)
        self.assertEqual(pos.altitude, 50.0)
    
    def test_position_to_tuple(self):
        """Test Position to_tuple method."""
        pos = Position(latitude=39.9042, longitude=116.4074, altitude=50.0)
        result = pos.to_tuple()
        self.assertEqual(result, (39.9042, 116.4074, 50.0))


class TestBoundingBox(unittest.TestCase):
    """Test cases for BoundingBox class."""
    
    def test_bounding_box_creation(self):
        """Test BoundingBox object creation."""
        bbox = BoundingBox(
            min_lat=39.0,
            max_lat=40.0,
            min_lon=116.0,
            max_lon=117.0
        )
        self.assertEqual(bbox.min_lat, 39.0)
        self.assertEqual(bbox.max_lat, 40.0)
        self.assertEqual(bbox.min_lon, 116.0)
        self.assertEqual(bbox.max_lon, 117.0)
    
    def test_bounding_box_contains(self):
        """Test BoundingBox contains method."""
        bbox = BoundingBox(
            min_lat=39.0,
            max_lat=40.0,
            min_lon=116.0,
            max_lon=117.0
        )
        
        # Position inside
        pos_inside = Position(latitude=39.5, longitude=116.5)
        self.assertTrue(bbox.contains(pos_inside))
        
        # Position outside
        pos_outside = Position(latitude=38.5, longitude=116.5)
        self.assertFalse(bbox.contains(pos_outside))
        
        # Position on boundary
        pos_boundary = Position(latitude=39.0, longitude=116.0)
        self.assertTrue(bbox.contains(pos_boundary))


class TestMapInfo(unittest.TestCase):
    """Test cases for MapInfo class."""
    
    def test_map_info_creation(self):
        """Test MapInfo object creation."""
        bbox = BoundingBox(
            min_lat=39.0,
            max_lat=40.0,
            min_lon=116.0,
            max_lon=117.0
        )
        map_info = MapInfo(
            map_type="osm",
            file_path="test.osm",
            num_lanelets=100,
            bounds=bbox,
            coordinate_system="WGS84"
        )
        
        self.assertEqual(map_info.map_type, "osm")
        self.assertEqual(map_info.file_path, "test.osm")
        self.assertEqual(map_info.num_lanelets, 100)
        self.assertEqual(map_info.coordinate_system, "WGS84")
        self.assertFalse(map_info.is_loaded)


class TestUtmProjectorWrapper(unittest.TestCase):
    """Test cases for UtmProjectorWrapper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from lanelet2.io import Origin
            from lanelet2.core import GPSPoint
            gps_point = GPSPoint(lat=39.9042, lon=116.4074)
            self.origin = Origin(gps_point)
            self.projector = UtmProjectorWrapper(self.origin)
        except ImportError:
            self.skipTest("Lanelet2 not installed")
    
    def test_forward_projection(self):
        """Test forward projection (GPS to map coordinates)."""
        pos = Position(latitude=39.9042, longitude=116.4074)
        point = self.projector.forward(pos)
        
        # Check that point is not None
        self.assertIsNotNone(point)
        # Check that coordinates are reasonable (UTM coordinates)
        # Note: The origin point itself will project to (0, 0)
        # So we test with a different point
        pos2 = Position(latitude=39.9142, longitude=116.4174)
        point2 = self.projector.forward(pos2)
        self.assertGreater(abs(point2.x), 0)
        self.assertGreater(abs(point2.y), 0)
    
    def test_reverse_projection(self):
        """Test reverse projection (map to GPS coordinates)."""
        pos = Position(latitude=39.9042, longitude=116.4074)
        point = self.projector.forward(pos)
        
        # Convert back
        pos_back = self.projector.reverse(point)
        
        # Check that we get approximately the same position
        self.assertAlmostEqual(pos_back.latitude, pos.latitude, places=5)
        self.assertAlmostEqual(pos_back.longitude, pos.longitude, places=5)


class TestMapLoader(unittest.TestCase):
    """Test cases for MapLoader class."""
    
    def test_loader_creation(self):
        """Test MapLoader object creation."""
        try:
            loader = MapLoader()
            self.assertIsNotNone(loader)
            self.assertFalse(loader.is_loaded())
        except ImportError:
            self.skipTest("Lanelet2 not installed")
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        try:
            loader = MapLoader()
            success = loader.load_map("nonexistent.osm", coordinate_type="local")
            self.assertFalse(success)
        except ImportError:
            self.skipTest("Lanelet2 not installed")
    
    def test_load_town10hd_map(self):
        """Test loading Town10HD.osm map."""
        try:
            # Check if map file exists
            map_file = Path(__file__).parent.parent.parent.parent / "configs" / "maps" / "Town10HD.osm"
            if not map_file.exists():
                self.skipTest(f"Map file not found: {map_file}")
            
            loader = MapLoader()
            success = loader.load_map(str(map_file), coordinate_type="local")
            self.assertTrue(success)
            self.assertTrue(loader.is_loaded())
            
            # Check map info
            map_info = loader.get_map_info()
            self.assertIsNotNone(map_info)
            self.assertEqual(map_info.map_type, "osm")
            self.assertTrue(map_info.is_loaded)
            self.assertGreater(map_info.num_lanelets, 0)
            
        except ImportError:
            self.skipTest("Lanelet2 not installed")


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
