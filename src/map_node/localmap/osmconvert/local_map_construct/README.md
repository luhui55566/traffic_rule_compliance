# LocalMapConstruct Module

The LocalMapConstruct module provides functionality for constructing local maps from MapAPI data. It serves as an intermediate layer between MapAPI and TrafficRule, providing a unified local map representation optimized for local queries.

## Visualization

The module includes visualization capabilities through `LocalMapVisualizer` class, which can visualize:
- Lane boundaries (left/right)
- Lane centerlines
- Boundary segments
- Traffic lights and signs
- Ego vehicle position
- Test points for verification

Use `test_with_visualization.py` to run tests with visualization for manual verification.

## Overview

The LocalMapConstruct module is responsible for:

1. **Coordinate Transformation**: Converting between global (WGS84/local map) coordinates and local (ego-centered) coordinates
2. **Map Conversion**: Transforming MapAPI data structures to LocalMap format
3. **Caching**: Managing local map cache with LRU eviction and TTL support
4. **Local Map Building**: Assembling complete LocalMap data structures
5. **Update Management**: Handling local map updates when ego vehicle moves

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  LocalMapConstructor                      │
│  (Main class coordinating all components)                  │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─── CoordinateTransformer (coordinate conversions)
             │
             ├─── MapConverter (MapAPI → LocalMap conversion)
             │
             ├─── CacheManager (LRU cache with TTL)
             │
             └─── LocalMapBuilder (assemble LocalMap)
```

## Module Structure

```
src/map_node/local_map_construct/
├── __init__.py          # Module exports
├── types.py             # Configuration classes (LocalMapConstructConfig, CacheConfig)
├── transformer.py       # CoordinateTransformer - global/local coordinate conversion
├── converter.py         # MapConverter - MapAPI to LocalMap format conversion
├── cache.py            # CacheManager - local map caching with LRU strategy
├── builder.py          # LocalMapBuilder - assemble LocalMap data structure
├── constructor.py      # LocalMapConstructor - main class coordinating all components
├── visualization.py      # LocalMapVisualizer - visualize LocalMap data
├── example_usage.py    # Example usage demonstration
├── test_local_map_construct.py  # Basic test without visualization
├── test_with_visualization.py  # Test with visualization for manual verification
└── README.md           # This file
```

## Usage Example

```python
from map_node.maploader.loader_local import LocalMapLoader
from map_node.mapapi.api import MapAPI
from common.local_map.local_map_data import Pose, Point3D
from map_node.local_map_construct import (
    LocalMapConstructor,
    LocalMapConstructConfig,
    CacheConfig
)

# Load map data
map_loader = LocalMapLoader()
map_loader.load_map("configs/maps/Town10HD.osm")

# Initialize MapAPI
map_api = MapAPI({
    'lanelet_map': map_loader.lanelet_map,
    'projector': map_loader.projector,
    'map_info': map_loader.map_info
})

# Configure LocalMapConstructor
config = LocalMapConstructConfig(
    map_range=200.0,
    update_threshold=50.0,
    cache_config=CacheConfig(enabled=True, max_size=10, ttl_seconds=1.0)
)

# Initialize constructor
constructor = LocalMapConstructor(config)

# Define ego pose
ego_pose = Pose(
    position=Point3D(x=0.0, y=0.0, z=0.0),
    heading=0.0
)

# Construct local map
result = constructor.construct_local_map(map_api, ego_pose)

if result.success:
    local_map = result.local_map
    print(f"Built local map with {len(local_map.lanes)} lanes")

# Update with new ego pose
new_pose = Pose(position=Point3D(x=10.0, y=5.0, z=0.0), heading=0.1)
update_result = constructor.update_local_map(map_api, new_pose)
```

## Configuration

### LocalMapConstructConfig

| Parameter | Type | Default | Description |
|-----------|-------|----------|-------------|
| `map_range` | float | 200.0 | Local map range in meters (radius around ego vehicle) |
| `update_threshold` | float | 50.0 | Distance threshold in meters for triggering map updates |
| `cache_config` | CacheConfig | None | Cache configuration |
| `coordinate_precision` | float | 0.01 | Precision threshold for coordinate transformation (meters) |
| `enable_boundary_sharing` | bool | True | Whether to enable boundary segment sharing between lanes |
| `include_road_markings` | bool | True | Whether to include road markings in local map |
| `include_crosswalks` | bool | True | Whether to include crosswalks in local map |
| `include_intersections` | bool | True | Whether to include intersections in local map |

### CacheConfig

| Parameter | Type | Default | Description |
|-----------|-------|----------|-------------|
| `enabled` | bool | True | Whether caching is enabled |
| `max_size` | int | 10 | Maximum number of cached entries (LRU eviction) |
| `ttl_seconds` | float | 1.0 | Time-to-live for cache entries in seconds |
| `position_tolerance` | float | 5.0 | Position tolerance in meters for cache key generation |

## API Reference

### LocalMapConstructor

Main class for constructing local maps.

#### Methods

- `construct_local_map(map_api, ego_pose, force_rebuild=False)` - Construct a local map
- `update_local_map(map_api, new_ego_pose, ego_velocity=0.0)` - Update local map for new ego pose
- `get_current_local_map()` - Get the current local map
- `get_cache_stats()` - Get cache statistics
- `clear_cache()` - Clear the cache
- `get_stats()` - Get constructor statistics

### CoordinateTransformer

Handles coordinate transformations between global and local coordinates.

#### Methods

- `global_to_local(global_position)` - Convert global to local coordinates
- `local_to_global(local_point)` - Convert local to global coordinates
- `transform_point_list(points, to_local=True)` - Transform a list of points
- `calculate_distance(pos1, pos2)` - Calculate Euclidean distance between points
- `is_within_range(position, range_meters)` - Check if position is within range
- `generate_cache_key(ego_pose, position_tolerance)` - Generate cache key from ego pose

### MapConverter

Converts MapAPI data structures to LocalMap format.

#### Methods

- `convert_lanelet_to_lane(lanelet, ego_pose)` - Convert a single lanelet
- `convert_lanelets_to_lanes(lanelets, ego_pose)` - Convert multiple lanelets
- `convert_traffic_signs(traffic_signs, ego_pose)` - Convert traffic signs
- `convert_traffic_lights(position, radius, ego_pose)` - Convert traffic lights

### CacheManager

Manages local map caching with LRU eviction and TTL support.

#### Methods

- `get(cache_key)` - Get cached local map
- `set(cache_key, local_map)` - Cache a local map
- `clear()` - Clear all cached entries
- `invalidate(cache_key)` - Invalidate a specific cache entry
- `get_stats()` - Get cache statistics
- `is_cache_valid(cache_key, ego_pose, position_tolerance)` - Check if cache is valid
- `prune_expired()` - Remove expired entries

### LocalMapBuilder

Assembles LocalMap data structures from converted elements.

#### Methods

- `build_local_map(lanes, traffic_lights, traffic_signs, ego_pose, map_range, ...)` - Build complete local map
- `update_metadata(local_map, ego_pose, ego_velocity)` - Update local map metadata
- `add_boundary_segment(boundary_segment)` - Add a boundary segment
- `clear_boundary_segments()` - Clear all boundary segments
- `create_empty_local_map(ego_pose, map_range)` - Create empty local map

### LocalMapVisualizer

Visualizes LocalMap data structures.

#### Methods

- `visualize_local_map(local_map, title, show_lanes, show_boundaries, show_centerlines, show_traffic_elements, show_ego_position, ego_points, save_path, dpi)` - Visualize a local map
- `_plot_lanes(local_map)` - Plot lane boundaries
- `_plot_boundary_segments(local_map)` - Plot boundary segments
- `_plot_centerlines(local_map)` - Plot lane centerlines
- `_plot_traffic_elements(local_map)` - Plot traffic lights and signs
- `_plot_ego_position(local_map)` - Plot ego vehicle position
- `_plot_ego_points(ego_points)` - Plot ego test points
- `auto_scale_axis(local_map)` - Auto-scale axis based on local map content

## Integration with TrafficRule

To integrate LocalMapConstruct with TrafficRuleVerificationSystem:

```python
class TrafficRuleVerificationSystem:
    def __init__(self, config):
        # ... existing initialization ...
        self.local_map_constructor: Optional[LocalMapConstructor] = None
        self.local_map_api: Optional[LocalMapAPI] = None
        self.current_local_map: Optional[LocalMap] = None

    def _initialize_local_map_constructor(self) -> bool:
        config = LocalMapConstructConfig(
            map_range=200.0,
            update_threshold=50.0
        )
        self.local_map_constructor = LocalMapConstructor(config)
        return True

    def _get_environment_data(self, state: VehicleState) -> Dict[str, Any]:
        # Update local map
        ego_pose = Pose(
            position=Point3D(x=state.local_x, y=state.local_y, z=state.altitude),
            heading=state.heading
        )
        result = self.local_map_constructor.update_local_map(
            self.map_manager.api, ego_pose
        )

        if result.success:
            self.current_local_map = result.local_map
            self.local_map_api.update_local_map(self.current_local_map)

        # Use LocalMapAPI for queries
        current_lane = self.local_map_api.find_nearest_lane(ego_pose.position)
        speed_limit = self.local_map_api.get_lane_speed_limit(...)
        # ...
```

## Running the Example

To run the example usage script:

```bash
python src/map_node/local_map_construct/example_usage.py
```

## Running Tests

### Basic Test (No Visualization)

To run the basic test without visualization:

```bash
python src/map_node/local_map_construct/test_local_map_construct.py
```

### Test with Visualization

To run the test with visualization for manual verification:

```bash
python src/map_node/local_map_construct/test_with_visualization.py
```

This will:
1. Load the Town10HD.osm map
2. Generate 10 random test points
3. Show the original map with test points marked (red 'x' markers)
4. For each test point, construct a local map and visualize it
5. First 3 tests will show detailed local map visualizations for manual verification

The visualizations allow you to:
- Compare the original map with the constructed local maps
- Verify that coordinate transformations are correct
- Check that lane boundaries and centerlines are properly converted
- Confirm that ego vehicle position is correctly placed in local coordinates

## Notes

- The module uses a local coordinate system with origin at ego vehicle position
- X-axis points in the direction of ego vehicle heading
- Cache keys are generated by quantizing ego position and heading
- Boundary segments can be shared between adjacent lanes for memory efficiency
- The module is designed to work with both GPS and local coordinate systems

## Future Enhancements

- [ ] Support for incremental map updates
- [ ] Asynchronous map building
- [ ] Spatial indexing for faster queries
- [ ] Support for additional map formats (XODR, Apollo)
- [ ] Traffic light prediction integration
- [ ] Dynamic map range adjustment based on vehicle speed
