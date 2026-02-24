# Traffic Rule Compliance Verification System

## Overview

The Traffic Rule Compliance Verification System is the main entry point for analyzing vehicle behavior against traffic rules. It integrates map loading, map API queries, and traffic rule checking to provide comprehensive compliance verification.

## Features

- **Map Integration**: Loads OSM format maps using Lanelet2
- **Multiple Traffic Rules**: Supports various traffic rule checks:
  - Speed limit violation detection
  - Continuous lane change detection
  - Fishbone line deceleration checking
  - Construction sign deceleration checking
  - Wrong way driving detection
- **Configuration Management**: YAML-based configuration for easy customization
- **Comprehensive Reporting**: Detailed violation reports with position, time, and severity information

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│         TrafficRuleVerificationSystem (Main Entry)          │
├─────────────────────────────────────────────────────────────────┤
│  Input: VehicleState (ego vehicle state)                │
│  Output: ViolationReport (compliance results)             │
├─────────────────────────────────────────────────────────────────┤
│  Components:                                             │
│  ├─ MapLoader (load OSM map)                            │
│  ├─ MapManager (map query API)                            │
│  └─ Traffic Rules (violation detection)                     │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Basic Usage

```python
from traffic_rule import TrafficRuleVerificationSystem, VehicleState, TrafficRuleConfig

# Load configuration
config = TrafficRuleConfig.load_from_file('configs/traffic_rule_config.yaml')

# Initialize system
system = TrafficRuleVerificationSystem(config)
system.initialize()

# Create vehicle state
state = VehicleState(
    timestamp=0.0,
    latitude=39.9042,
    longitude=116.4074,
    speed=15.0,  # m/s
    heading=1.57,  # radians
    lane_id="lane_1"
)

# Verify state
violation = system.verify_state(state)
if violation:
    print(f"Violation detected: {violation.rule_name}")
```

### 2. Batch Processing

```python
# Process multiple states
states = [
    VehicleState(timestamp=0.0, latitude=39.9042, longitude=116.4074, speed=15.0, heading=1.57),
    VehicleState(timestamp=1.0, latitude=39.9043, longitude=116.4075, speed=20.0, heading=1.57),
    # ... more states
]

# Get comprehensive report
report = system.verify_states(states)

# Print summary
print(report.get_summary())
```

## Data Structures

### VehicleState

Represents ego vehicle state:

```python
@dataclass
class VehicleState:
    timestamp: float           # Timestamp in seconds
    latitude: float           # Latitude in degrees
    longitude: float          # Longitude in degrees
    speed: float             # Speed in m/s
    heading: float           # Heading angle in radians
    acceleration: Optional[float]   # Acceleration in m/s²
    yaw_rate: Optional[float]      # Yaw rate in rad/s
    lane_id: Optional[str]         # Current lane ID
    altitude: Optional[float]       # Altitude in meters
```

### Violation

Represents a detected traffic rule violation:

```python
@dataclass
class Violation:
    rule_id: str            # Rule identifier (e.g., "R001")
    rule_name: str          # Human-readable rule name
    severity: ViolationSeverity  # Severity level
    description: str        # Description of violation
    
    # Position information
    latitude: float         # Latitude where violation occurred
    longitude: float        # Longitude where violation occurred
    lane_id: Optional[str]  # Lane ID where violation occurred
    
    # Time interval
    start_time: float      # Start time of violation (seconds)
    end_time: Optional[float]  # End time of violation (seconds)
    
    # Additional details
    details: Dict[str, Any]  # Additional violation details
```

### ViolationReport

Comprehensive report containing all violations:

```python
@dataclass
class ViolationReport:
    timestamp: datetime              # Report generation time
    vehicle_states: List[VehicleState]  # All states processed
    violations: List[Violation]         # All detected violations
    
    def get_summary() -> Dict[str, Any]:
        """Get summary statistics"""
    
    def get_violations_by_severity(severity) -> List[Violation]:
        """Filter violations by severity"""
    
    def get_violations_by_rule(rule_id) -> List[Violation]:
        """Filter violations by rule ID"""
```

## Configuration

The system uses YAML configuration files. See [`configs/traffic_rule_config.yaml`](../../configs/traffic_rule_config.yaml) for the default configuration.

### Configuration Structure

```yaml
# Map configuration
map:
  osm_file: "Town10HD.osm"
  origin:
    latitude: 39.9042
    longitude: 116.4074

# Speed limit rule
speed_limit:
  enabled: true
  tolerance: 5.0  # km/h

# Continuous lane change rule
continuous_lane_change:
  enabled: true
  time_window: 10.0  # seconds
  max_changes: 2

# Fishbone line rule
fishbone:
  enabled: true
  required_deceleration: 2.0  # m/s²
  trigger_distance: 100.0  # meters
  max_speed_to_trigger: 40.0  # km/h

# Construction sign rule
construction_sign:
  enabled: true
  required_deceleration: 1.5  # m/s²
  distance_threshold: 200.0  # meters

# Wrong way rule
wrong_way:
  enabled: true
  heading_tolerance: 45.0  # degrees

# System configuration
history_window: 10.0  # seconds
cache_enabled: true
```

## Traffic Rules

### R001: Speed Limit Rule

Checks if vehicle exceeds the speed limit at its current location.

**Parameters:**
- `tolerance`: Speed tolerance in km/h (default: 5 km/h)

**Severity:** MAJOR

### R002: Continuous Lane Change Rule

Detects if vehicle changes lanes too frequently within a time window.

**Parameters:**
- `time_window`: Time window in seconds (default: 10s)
- `max_changes`: Maximum allowed lane changes (default: 2)

**Severity:** MINOR

### R003: Fishbone Line Rule

Checks if vehicle decelerates sufficiently when approaching fishbone lines.

**Parameters:**
- `required_deceleration`: Required deceleration in m/s² (default: 2.0)
- `trigger_distance`: Distance to trigger in meters (default: 100m)
- `max_speed_to_trigger`: Max speed to trigger in km/h (default: 40 km/h)

**Severity:** MAJOR

### R004: Construction Sign Rule

Checks if vehicle decelerates sufficiently when approaching construction signs.

**Parameters:**
- `required_deceleration`: Required deceleration in m/s² (default: 1.5)
- `distance_threshold`: Distance threshold in meters (default: 200m)

**Severity:** MAJOR

### R005: Wrong Way Rule

Detects if vehicle is driving in the wrong direction on a lane.

**Parameters:**
- `heading_tolerance`: Heading tolerance in degrees (default: 45°)

**Severity:** CRITICAL

## API Reference

### TrafficRuleVerificationSystem

Main class for traffic rule compliance verification.

#### Methods

##### `initialize() -> bool`
Initialize the system by loading map and setting up rules.

##### `verify_state(state: VehicleState) -> Optional[Violation]`
Verify a single vehicle state against all traffic rules.

##### `verify_states(states: List[VehicleState]) -> ViolationReport`
Verify multiple vehicle states and generate a comprehensive report.

##### `add_rule(rule: TrafficRuleBase) -> None`
Add a custom traffic rule to the system.

##### `remove_rule(rule_id: str) -> bool`
Remove a traffic rule by ID.

##### `list_rules() -> List[str]`
List all registered rule IDs.

##### `get_status() -> Dict[str, Any]`
Get current system status.

##### `reset() -> None`
Reset system state (clears history).

##### `shutdown() -> None`
Shutdown system and release resources.

## Example

See [`examples/traffic_rule_example.py`](../../examples/traffic_rule_example.py) for a complete working example.

## Integration with CARLA

To integrate with CARLA simulation:

```python
import carla

# Connect to CARLA
client = carla.Client('localhost', 2000)
world = client.get_world()

# Get ego vehicle
ego_vehicle = world.get_actors().filter('vehicle.*')[0]

# Get vehicle state
transform = ego_vehicle.get_transform()
velocity = ego_vehicle.get_velocity()

state = VehicleState(
    timestamp=world.get_snapshot().timestamp.elapsed_seconds,
    latitude=transform.location.latitude,
    longitude=transform.location.longitude,
    speed=velocity.length(),
    heading=math.radians(transform.rotation.yaw),
    lane_id=get_lane_id(ego_vehicle)  # Custom function
)

# Verify compliance
violation = system.verify_state(state)
```

## Extending the System

### Adding Custom Rules

Create a new rule by inheriting from `TrafficRuleBase`:

```python
from traffic_rule.rules.base import TrafficRuleBase
from traffic_rule.types import VehicleState, Violation, ViolationSeverity

class CustomRule(TrafficRuleBase):
    def __init__(self):
        super().__init__("R006", "Custom Rule", enabled=True)
    
    def check(self, current_state, history, environment_data):
        # Implement your rule logic here
        if violation_detected:
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=ViolationSeverity.WARNING,
                description="Custom violation",
                latitude=current_state.latitude,
                longitude=current_state.longitude,
                start_time=current_state.timestamp,
                end_time=current_state.timestamp
            )
        return None

# Add to system
system.add_rule(CustomRule())
```

## Dependencies

- Python 3.8+
- Lanelet2 (for map loading)
- PyYAML (for configuration)
- Existing map and mapapi modules

## License

See project root for license information.
