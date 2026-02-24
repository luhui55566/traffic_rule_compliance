# Traffic Rule System Debug Guide

## Overview

This guide helps you debug and test the traffic rule compliance verification system.

## Prerequisites

1. **Python Environment**: Python 3.8+
2. **Lanelet2** (for full map-based testing):
   ```bash
   sudo apt-get install liblanelet2-dev python3-lanelet2
   ```

## Debugging Options

### Option 1: Simple Test (No Map Required)

Run the simple test that doesn't require Lanelet2:

```bash
cd lanelet_test
python examples/traffic_rule_simple_test.py
```

**What this tests:**
- Data structures (VehicleState, Violation, ViolationReport)
- Configuration loading
- Traffic rule initialization
- State history management

**Expected Output:**
```
============================================================
TRAFFIC RULE SYSTEM - SIMPLE TEST (No Map)
============================================================

Configuration:
  Speed limit rule: False
  Continuous lane change rule: True
  Fishbone rule: False
  Construction sign rule: False
  Wrong way rule: False

Creating test vehicle states...
Created 11 vehicle states

First 3 states:
  [0] t=0.0, pos=(39.904200, 116.407400), speed=15.0m/s, lane=lane_1
  [1] t=1.0, pos=(39.904300, 116.407500), speed=15.0m/s, lane=lane_1
  [2] t=2.0, pos=(39.904400, 116.407600), speed=15.0m/s, lane=lane_1

------------------------------------------------------------
NOTE: Full verification requires map loading.
This test demonstrates data structures and configuration.

To run full test with map:
  1. Install Lanelet2: sudo apt-get install liblanelet2-dev python3-lanelet2
  2. Run: python examples/traffic_rule_example.py
------------------------------------------------------------
```

### Option 2: Full Test with Map

Run the complete example with map loading:

```bash
cd lanelet_test
python examples/traffic_rule_example.py
```

**What this tests:**
- Map loading via MapLoader
- MapManager initialization
- All traffic rules
- Full verification pipeline

**Expected Output:**
```
============================================================
Traffic Rule Compliance Verification System - Example
============================================================

[Step 1] Loading configuration...
Configuration loaded from: configs/traffic_rule_config.yaml

[Step 2] Initializing system...
Initializing TrafficRuleVerificationSystem...
Loading OSM map from: Town10HD.osm
Map loaded: MapInfo(type=osm, file=Town10HD.osm, lanelets=XXX, loaded=True)
Map manager initialized
Speed limit rule enabled
Continuous lane change rule enabled
Fishbone rule enabled
Construction sign rule enabled
Wrong way rule enabled
Total rules initialized: 5
TrafficRuleVerificationSystem initialized successfully
System initialized successfully

System Status:
  Initialized: True
  Map Loaded: True
  Rules Enabled: 5/5
  Active Rules: ['R001', 'R002', 'R003', 'R004', 'R005']

[Step 3] Creating sample vehicle states...
Created 11 vehicle states

[Step 4] Verifying vehicle states...
Verifying 11 vehicle states...
Verification complete: X violations detected

============================================================
TRAFFIC RULE COMPLIANCE REPORT
============================================================

Timestamp: 2026-01-30 07:XX:XX.XXXXXX
States Processed: 11
Total Violations: X
Is Compliant: YES/NO

--- Violations by Severity ---
  MAJOR: X
  MINOR: X

--- Violations by Rule ---
  R001: X
  R002: X

============================================================

[Step 5] Shutting down system...
System shutdown complete
```

## Common Issues and Solutions

### Issue 1: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'traffic_rule'
```

**Solution:**
Make sure you're running from the correct directory:
```bash
cd lanelet_test
python examples/traffic_rule_example.py
```

Or add the src directory to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python examples/traffic_rule_example.py
```

### Issue 2: Lanelet2 Not Installed

**Error:**
```
ImportError: Lanelet2 is not installed. Please install it first:
  sudo apt-get install liblanelet2-dev python3-lanelet2
```

**Solution:**
Install Lanelet2:
```bash
sudo apt-get update
sudo apt-get install liblanelet2-dev python3-lanelet2
```

### Issue 3: Map File Not Found

**Error:**
```
Map file not found: Town10HD.osm
```

**Solution:**
Check the map file path in configuration:
```bash
ls -la lanelet_test/Town10HD.osm
```

Or update the config file path:
```yaml
map:
  osm_file: "/path/to/your/map.osm"
```

### Issue 4: Configuration File Not Found

**Error:**
```
Config file not found: configs/traffic_rule_config.yaml
```

**Solution:**
The example will fall back to default configuration. To use custom config:
```bash
cp lanelet_test/configs/traffic_rule_config.yaml lanelet_test/config.yaml
```

## VSCode Configuration

The `.vscode/settings.json` file contains Python environment settings. You can keep it as-is or update it:

```json
{
    "python-envs.defaultEnvManager": "ms-python.python:conda",
    "python-envs.defaultPackageManager": "ms-python.python:conda",
    "python-envs.pythonProjects": []
}
```

**Recommendation:** Keep the current settings if they work for your environment.

## Debugging Tips

### 1. Enable Verbose Logging

Edit the logging level in `src/traffic_rule/traffic_rule_verification_system.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Test Individual Components

Test specific components:

```python
# Test configuration loading
from traffic_rule import TrafficRuleConfig
config = TrafficRuleConfig.load_from_file('configs/traffic_rule_config.yaml')
print(config.to_dict())

# Test vehicle state creation
from traffic_rule import VehicleState
state = VehicleState(
    timestamp=0.0,
    latitude=39.9042,
    longitude=116.4074,
    speed=15.0,
    heading=1.57
)
print(state)
```

### 3. Use Python Debugger

Run with pdb:

```bash
python -m pdb examples/traffic_rule_simple_test.py
```

Or use VSCode debugger with breakpoints.

## Project Structure Reference

```
lanelet_test/
├── src/traffic_rule/          # Main module
│   ├── __init__.py
│   ├── traffic_rule_verification_system.py  # TrafficRuleVerificationSystem
│   ├── types.py              # Data structures
│   ├── config.py             # Configuration
│   └── rules/                # Rule implementations
├── configs/
│   └── traffic_rule_config.yaml
└── examples/
    ├── traffic_rule_example.py      # Full test with map
    └── traffic_rule_simple_test.py # Simple test without map
```

## Next Steps

1. Run the simple test first to verify basic functionality
2. Install Lanelet2 if needed for full testing
3. Run the full example with map
4. Check the violation report output
5. Modify configuration as needed
6. Add custom rules if required
