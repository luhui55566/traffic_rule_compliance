"""
Simple test for traffic rule system without map dependency.

This script demonstrates the traffic rule system without requiring
Lanelet2 to be installed. It uses mock data for testing.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from traffic_rule import TrafficRuleVerificationSystem, VehicleState, TrafficRuleConfig
from traffic_rule.types import ViolationSeverity


def create_test_states(use_local_coords: bool = False):
    """
    Create test vehicle states.
    
    Args:
        use_local_coords: If True, use local coordinates (x, y, heading with origin at 0,0)
                        If False, use global coordinates (latitude, longitude, heading)
    
    Returns:
        List of VehicleState objects
    """
    states = []
    
    # Simulate a vehicle driving over 10 seconds
    for i in range(11):
        timestamp = float(i)
        
        # Simulate driving with some violations
        if i < 3:
            # Normal driving
            speed = 15.0  # ~54 km/h
            lane_id = "lane_1"
        elif i < 6:
            # Speeding (exceeds 50 km/h limit)
            speed = 20.0  # ~72 km/h
            lane_id = "lane_1"
        elif i < 8:
            # Lane change
            speed = 15.0
            lane_id = "lane_2" if i % 2 == 0 else "lane_1"
        else:
            # Back to normal
            speed = 15.0
            lane_id = "lane_2"
        
        if use_local_coords:
            # Use local coordinates (origin at 0,0)
            state = VehicleState(
                timestamp=timestamp,
                speed=speed,
                local_x=i * 10.0,  # Move 10 meters per second in x direction
                local_y=0.0,
                local_heading=0.0,  # East direction (0 radians)
                acceleration=0.5 if i < 5 else -0.5,
                lane_id=lane_id,
                altitude=50.0,
                use_local_coords=True
            )
        else:
            # Use global coordinates (latitude, longitude)
            state = VehicleState(
                timestamp=timestamp,
                speed=speed,
                latitude=39.9042 + i * 0.0001,
                longitude=116.4074 + i * 0.0001,
                heading=1.57,  # East direction
                acceleration=0.5 if i < 5 else -0.5,
                lane_id=lane_id,
                altitude=50.0,
                use_local_coords=False
            )
        states.append(state)
    
    return states


def test_without_map():
    """Test traffic rule system without map loading."""
    print("=" * 60)
    print("TRAFFIC RULE SYSTEM - SIMPLE TEST (No Map)")
    print("=" * 60)
    
    # Create default configuration
    config = TrafficRuleConfig()
    
    # Disable map-dependent rules for this test
    config.speed_limit.enabled = False
    config.fishbone.enabled = False
    config.construction_sign.enabled = False
    config.wrong_way.enabled = False
    config.continuous_lane_change.enabled = True
    
    print("\nConfiguration:")
    print(f"  Speed limit rule: {config.speed_limit.enabled}")
    print(f"  Continuous lane change rule: {config.continuous_lane_change.enabled}")
    print(f"  Fishbone rule: {config.fishbone.enabled}")
    print(f"  Construction sign rule: {config.construction_sign.enabled}")
    print(f"  Wrong way rule: {config.wrong_way.enabled}")
    
    # Create test states
    print("\nCreating test vehicle states...")
    # Use global coordinates by default (set use_local_coords=True for local coordinates)
    states = create_test_states(use_local_coords=False)
    print(f"Created {len(states)} vehicle states")
    print(f"Coordinate system: {'Local (x, y, heading)' if states[0].use_local_coords else 'Global (latitude, longitude, heading)'}")
    
    # Print first few states
    print("\nFirst 3 states:")
    for i, state in enumerate(states[:3]):
        if state.use_local_coords:
            print(f"  [{i}] t={state.timestamp:.1f}, "
                  f"local_pos=({state.local_x:.2f}, {state.local_y:.2f}), "
                  f"local_heading={state.local_heading:.2f}rad, "
                  f"speed={state.speed:.1f}m/s, lane={state.lane_id}")
        else:
            print(f"  [{i}] t={state.timestamp:.1f}, "
                  f"pos=({state.latitude:.6f}, {state.longitude:.6f}), "
                  f"heading={state.heading:.2f}rad, "
                  f"speed={state.speed:.1f}m/s, lane={state.lane_id}")
    
    # Note: Without map, we can't run full verification
    print("\n" + "-" * 60)
    print("NOTE: Full verification requires map loading.")
    print("This test demonstrates the data structures and configuration.")
    print("\nTo run full test with map:")
    print("  1. Install Lanelet2: sudo apt-get install liblanelet2-dev python3-lanelet2")
    print("  2. Run: python examples/traffic_rule_example.py")
    print("-" * 60)
    
    return 0


def main():
    """Main function."""
    return test_without_map()


if __name__ == "__main__":
    sys.exit(main())
