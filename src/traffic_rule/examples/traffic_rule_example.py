"""
Example usage of TrafficRuleVerificationSystem.

This script demonstrates how to use the traffic rule compliance
verification system with vehicle state data.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from traffic_rule import TrafficRuleVerificationSystem, VehicleState, TrafficRuleConfig
from traffic_rule.types import ViolationSeverity


def create_sample_vehicle_states():
    """
    Create sample vehicle states for demonstration.
    
    Uses manually specified coordinates from CARLA simulation (Town10HD).
    Note: lane_id is not provided as input - it should be obtained via map API.
    
    Returns:
        List of VehicleState objects with CARLA local coordinates
    """
    states = []
    
    # Manually specified coordinates from CARLA simulation (Town10HD)
    # Position (X, Y, Z), Orientation (Roll, Pitch, Yaw), Speed, Control
    carla_states = [
        # timestamp, x, y, z, yaw, speed, throttle, steer, brake
        (0.0, -113.86, 10.49, 0.00, 90.6, 8.07, 0.501, 0.001, 0.000),
        (0.1, -113.86, 10.90, 0.00, 90.6, 8.11, 0.375, -0.000, 0.000),
        (0.2, -113.87, 11.30, 0.00, 90.6, 8.17, 0.316, 0.001, 0.000),
        (0.3, -113.87, 11.71, 0.00, 90.6, 8.16, 0.239, -0.000, 0.000),
        (0.4, -113.88, 12.12, 0.00, 90.6, 8.16, 0.251, 0.000, 0.000),
        (0.5, -113.88, 12.53, 0.00, 90.6, 8.12, 0.243, 0.000, 0.000),
        (0.6, -113.89, 12.93, 0.00, 90.6, 8.10, 0.311, -0.001, 0.000),
        (0.7, -113.89, 13.34, 0.00, 90.6, 8.05, 0.336, 0.000, 0.000),
        (0.8, -113.90, 13.74, 0.00, 90.6, 8.04, 0.413, 0.000, 0.000),
    ]
    
    for i, (timestamp, x, y, z, yaw, speed, throttle, steer, brake) in enumerate(carla_states):
        # Convert yaw from degrees to radians
        yaw_rad = yaw * (3.14159265359 / 180.0)
        
        # Calculate acceleration (simple difference between consecutive speeds)
        if i > 0:
            prev_speed = carla_states[i-1][5]
            acceleration = (speed - prev_speed) / 0.1  # dt = 0.1s
        else:
            acceleration = 0.0
        
        # Use CARLA local coordinates (x, y, z)
        state = VehicleState(
            timestamp=timestamp,
            speed=speed,
            local_x=x,
            local_y=y,
            local_heading=yaw_rad,
            acceleration=acceleration,
            lane_id=None,  # lane_id should be obtained via map API, not as input
            altitude=z,
            use_local_coords=True
        )
        states.append(state)
    
    return states


def print_report_summary(report):
    """
    Print violation report summary.
    
    Args:
        report: ViolationReport object
    """
    print("\n" + "=" * 60)
    print("TRAFFIC RULE COMPLIANCE REPORT")
    print("=" * 60)
    
    summary = report.get_summary()
    
    print(f"\nTimestamp: {report.timestamp}")
    print(f"States Processed: {summary['states_processed']}")
    print(f"Total Violations: {summary['total_violations']}")
    print(f"Is Compliant: {'YES' if summary['is_compliant'] else 'NO'}")
    
    print("\n--- Violations by Severity ---")
    for severity, count in summary['severity_counts'].items():
        if count > 0:
            print(f"  {severity.upper()}: {count}")
    
    print("\n--- Violations by Rule ---")
    for rule_id, count in summary['rule_counts'].items():
        if count > 0:
            print(f"  {rule_id}: {count}")
    
    if report.violations:
        print("\n--- Violation Details ---")
        for i, violation in enumerate(report.violations, 1):
            print(f"\n[{i}] {violation.rule_name} ({violation.rule_id})")
            print(f"    Severity: {violation.severity.value}")
            print(f"    Description: {violation.description}")
            # Check if any state uses local coordinates
            use_local = any(s.use_local_coords for s in report.vehicle_states)
            if use_local:
                print(f"    Position: (local_x={violation.latitude:.2f}, local_y={violation.longitude:.2f})")
            else:
                print(f"    Position: ({violation.latitude:.6f}, {violation.longitude:.6f})")
            print(f"    Lane: {violation.lane_id}")
            print(f"    Time: [{violation.start_time:.2f}, {violation.end_time:.2f}]")
            if violation.details:
                print(f"    Details: {violation.details}")
    
    print("\n" + "=" * 60)


def main():
    """Main function."""
    print("Traffic Rule Compliance Verification System - Example")
    print("=" * 60)
    
    # Step 1: Load configuration
    print("\n[Step 1] Loading configuration...")
    config_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'configs',
        'traffic_rule_config.yaml'
    )
    
    try:
        config = TrafficRuleConfig.load_from_file(config_path)
        print(f"Configuration loaded from: {config_path}")
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print("Using default configuration...")
        config = TrafficRuleConfig()
    
    # Step 2: Initialize system
    print("\n[Step 2] Initializing system...")
    system = TrafficRuleVerificationSystem(config)
    
    if not system.initialize():
        print("Failed to initialize system!")
        return 1
    
    print("System initialized successfully")
    
    # Print system status
    status = system.get_status()
    print(f"\nSystem Status:")
    print(f"  Initialized: {status['initialized']}")
    print(f"  Map Loaded: {status['map_loaded']}")
    print(f"  Rules Enabled: {status['rules_enabled']}/{status['rules_total']}")
    print(f"  Active Rules: {system.list_rules()}")
    
    # Step 3: Create sample vehicle states
    print("\n[Step 3] Creating sample vehicle states...")
    # Use CARLA's original X, Y, Z coordinates
    states = create_sample_vehicle_states()
    print(f"Created {len(states)} vehicle states")
    print(f"Coordinate system: {'Local (x, y, heading)' if states[0].use_local_coords else 'Global (latitude, longitude, heading)'}")
    
    # Step 4: Verify states
    print("\n[Step 4] Verifying vehicle states...")
    report = system.verify_states(states)
    
    # Step 5: Print report
    print_report_summary(report)
    
    # Step 6: Cleanup
    print("\n[Step 5] Shutting down system...")
    system.shutdown()
    print("System shutdown complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
