"""
Integration tests for map_node and traffic_rule components.

These tests verify the interaction between map loading and traffic rule verification.
"""

import os
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from map_node.maploader.loader import MapLoader
from map_node.mapapi import MapManager, Position
from traffic_rule import TrafficRuleVerificationSystem, VehicleState, TrafficRuleConfig


class TestIntegration(unittest.TestCase):
    """Integration tests for the overall system."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from lanelet2.io import Origin
            from lanelet2.core import GPSPoint
            self.lanelet2_available = True
        except ImportError:
            self.lanelet2_available = False
    
    def test_map_loading_and_traffic_rule_integration(self):
        """Test integration between map loading and traffic rule verification."""
        if not self.lanelet2_available:
            self.skipTest("Lanelet2 not installed")
        
        # Check if map file exists
        map_file = Path(__file__).parent.parent.parent / "configs" / "maps" / "Town10HD.osm"
        if not map_file.exists():
            self.skipTest(f"Map file not found: {map_file}")
        
        # Step 1: Load map using MapLoader
        loader = MapLoader()
        success = loader.load_map(str(map_file), coordinate_type="local")
        self.assertTrue(success)
        
        # Step 2: Initialize MapManager with map data
        map_manager = MapManager()
        map_data = loader.get_map_data()
        map_manager.initialize(map_data=map_data)
        self.assertTrue(map_manager.is_loaded())
        
        # Step 3: Initialize TrafficRuleVerificationSystem
        config_path = Path(__file__).parent.parent.parent / "configs" / "traffic_rule_config.yaml"
        try:
            config = TrafficRuleConfig.load_from_file(str(config_path))
        except FileNotFoundError:
            config = TrafficRuleConfig()
        
        system = TrafficRuleVerificationSystem(config)
        self.assertTrue(system.initialize())
        
        # Step 4: Create test vehicle states
        states = []
        for i in range(5):
            # Use coordinates from the map
            state = VehicleState(
                timestamp=float(i),
                speed=15.0,  # ~54 km/h
                local_x=-113.86 + i * 2.0,  # Move along x axis
                local_y=10.49 + i * 0.5,    # Move along y axis
                local_heading=1.57,         # East direction
                acceleration=0.0,
                lane_id=None,  # Will be determined by map
                altitude=0.0,
                use_local_coords=True
            )
            states.append(state)
        
        # Step 5: Verify states using the traffic rule system
        report = system.verify_states(states)
        
        # Step 6: Verify that the system processed the states
        self.assertIsNotNone(report)
        self.assertEqual(len(report.vehicle_states), len(states))
        
        # Step 7: Cleanup
        system.shutdown()
    
    def test_map_api_position_queries(self):
        """Test MapAPI position queries with real coordinates."""
        if not self.lanelet2_available:
            self.skipTest("Lanelet2 not installed")
        
        # Check if map file exists
        map_file = Path(__file__).parent.parent.parent / "configs" / "maps" / "Town10HD.osm"
        if not map_file.exists():
            self.skipTest(f"Map file not found: {map_file}")
        
        # Load map
        loader = MapLoader()
        success = loader.load_map(str(map_file), coordinate_type="local")
        self.assertTrue(success)
        
        # Initialize MapManager
        map_manager = MapManager()
        map_data = loader.get_map_data()
        map_manager.initialize(map_data=map_data)
        self.assertTrue(map_manager.is_loaded())
        
        # Test position query with local coordinates
        test_position = Position(latitude=0.0, longitude=0.0)  # Using (0,0) as origin
        lanelet = map_manager.get_lanelet(test_position)
        
        # The result might be None if (0,0) is not on a lanelet, which is fine
        # We're just testing that the query doesn't crash
        self.assertTrue(True)  # If we get here, the query worked
    
    def test_config_loading(self):
        """Test configuration loading for traffic rules."""
        config_path = Path(__file__).parent.parent.parent / "configs" / "traffic_rule_config.yaml"
        
        try:
            config = TrafficRuleConfig.load_from_file(str(config_path))
            self.assertIsNotNone(config)
        except FileNotFoundError:
            # If config file doesn't exist, create default config
            config = TrafficRuleConfig()
            self.assertIsNotNone(config)


def run_tests():
    """Run all integration tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()