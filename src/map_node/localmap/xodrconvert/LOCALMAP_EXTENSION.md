# LocalMap Data Structure Extension for XODR Support

## Overview

This document describes the extensions to the LocalMap data structure to support XODR's Road and Junction concepts.

**Purpose:**
- Preserve XODR's topological structure (Road → Junction → Road)
- Enable road-level and junction-level queries
- Support lane-to-lane connections through junctions

---

## 1. New Data Types

### 1.1 Road

```python
@dataclass
class Road:
    """道路 / Road
    
    XODR中Road的概念：包含多个lane section，每个lane section包含多个lane
    XODR Road concept: Contains multiple lane sections, each containing multiple lanes
    """
    road_id: int                           # 道路唯一标识符 / Unique road identifier
    road_name: str                          # 道路名称 / Road name
    road_length: float                       # 道路长度（米）/ Road length (meters)
    road_type: str = ""                      # 道路类型 / Road type (town, rural, etc.)
    
    # 连接关系 / Connection relationships
    predecessor_road_id: Optional[int] = None   # 前继道路ID / Predecessor road ID
    successor_road_id: Optional[int] = None     # 后继道路ID / Successor road ID
    predecessor_junction_id: Optional[int] = None # 前继交叉口ID / Predecessor junction ID
    successor_junction_id: Optional[int] = None   # 后继交叉口ID / Successor junction ID
    
    # 包含的车道 / Contained lanes
    lane_ids: List[int] = field(default_factory=list)  # 此道路包含的所有车道ID列表 / List of all lane IDs in this road
    
    # 几何信息 / Geometry information
    reference_line: List[Point3D] = field(default_factory=list)  # 参考线点集 / Reference line point set
    speed_limit: float = 0.0               # 道路限速（米/秒）/ Road speed limit (m/s)
```

**XODR Mapping:**

| XODR Source | LocalMap Road Field | Notes |
|---------------|---------------------|--------|
| `Road.id` | `road_id` | Direct mapping |
| `Road.name` | `road_name` | Direct mapping |
| `Road.length` | `road_length` | Direct mapping |
| `Road.s_to_type` | `road_type` | Extract from type at s=0 |
| `Road.predecessor.id` | `predecessor_road_id` | If predecessor type is "road" |
| `Road.successor.id` | `successor_road_id` | If successor type is "road" |
| `Road.predecessor.id` | `predecessor_junction_id` | If predecessor type is "junction" |
| `Road.successor.id` | `successor_junction_id` | If successor type is "junction" |
| `Road.ref_line` | `reference_line` | Extract reference line points |
| `Road.s_to_speed` | `speed_limit` | Extract default speed limit |

### 1.2 Junction (Extended)

```python
@dataclass
class Junction:
    """交叉口 / Junction
    
    XODR中Junction的概念：连接多条道路的交叉口区域
    XODR Junction concept: Intersection area connecting multiple roads
    """
    junction_id: int                       # 交叉口唯一标识符 / Unique junction identifier
    junction_name: str                      # 交叉口名称 / Junction name
    junction_type: str = ""                # 交叉口类型 / Junction type
    
    # 连接的道路 / Connected roads
    road_ids: List[int] = field(default_factory=list)  # 连接到此交叉口的所有道路ID列表 / List of all road IDs connected to this junction
    
    # 连接信息 / Connection information
    connection_count: int = 0               # 连接数量 / Number of connections
    has_traffic_light: bool = False          # 是否有信号灯控制 / Whether controlled by traffic light
    controller_ids: List[int] = field(default_factory=list)  # 控制器ID列表 / Controller ID list
    
    # 几何信息 / Geometry information
    polygon_points: List[Point3D] = field(default_factory=list)  # 交叉口多边形顶点 / Junction polygon vertices
    center_point: Point3D = field(default_factory=lambda: Point3D(x=0.0, y=0.0, z=0.0))  # 中心点 / Center point
```

**XODR Mapping:**

| XODR Source | LocalMap Junction Field | Notes |
|---------------|------------------------|--------|
| `Junction.id` | `junction_id` | Direct mapping |
| `Junction.name` | `junction_name` | Direct mapping |
| `Junction.id_to_connection` | `road_ids` | Extract all incoming and connecting road IDs |
| `Junction.id_to_connection` | `connection_count` | Number of connections |
| `Junction.id_to_controller` | `has_traffic_light` | Set to True if controller exists |
| `Junction.id_to_controller` | `controller_ids` | Extract all controller IDs |
| Junction geometry | `polygon_points` | Calculate from connecting roads |
| Junction geometry | `center_point` | Calculate from polygon centroid |

---

## 2. Extended Lane Structure

```python
@dataclass
class Lane:
    """车道 / Lane"""
    
    # ... 现有字段保持不变 ...
    # ... Keep existing fields unchanged ...
    
    # 新增字段 / New fields
    road_id: Optional[int] = None          # 所属道路ID / Belonging road ID
    junction_id: Optional[int] = None       # 所属交叉口ID / Belonging junction ID
    is_junction_lane: bool = False          # 是否为交叉口内部车道 / Whether is junction internal lane
```

**XODR Mapping:**

| XODR Source | LocalMap Lane Field | Notes |
|---------------|-------------------|--------|
| `Lane.key.road_id` | `road_id` | Direct mapping |
| `Road.junction` | `junction_id` | If road.junction != "-1" |
| `Road.junction != "-1"` | `is_junction_lane` | Set to True for junction internal lanes |

---

## 3. Extended LocalMap Structure

```python
@dataclass
class LocalMap:
    """局部地图主结构 / Local Map Main Structure"""
    
    # ... 现有字段保持不变 ...
    # ... Keep existing fields unchanged ...
    
    # 新增字段 / New fields
    roads: List[Road] = field(default_factory=list)      # 道路信息列表 / Road information list
    junctions: List[Junction] = field(default_factory=list)  # 交叉口信息列表 / Junction information list
```

---

## 4. Lane Connection Handling

### 4.1 XODR Connection Hierarchy

```
Road Level:
Road 1 ──successor──> Junction 664
Road 2 ──predecessor─> Junction 664

Junction Level:
Junction 664:
  Connection 0: Road 1 (incoming) ──> Road 675 (connecting)
    laneLink: Lane 1 (from) ──> Lane 1 (to)
  Connection 1: Road 1 (incoming) ──> Road 676 (connecting)
    laneLink: Lane 2 (from) ──> Lane 2 (to)

Lane Level:
Road 1, Lane 1: successor_lane_ids = [Road 675, Lane 1, Road 676, Lane 2]
Road 675, Lane 1: predecessor_lane_ids = [Road 1, Lane 1]
Road 676, Lane 2: predecessor_lane_ids = [Road 1, Lane 2]
```

### 4.2 Conversion Algorithm

```python
def convert_xodr_to_localmap(odr_map: OpenDriveMap) -> LocalMap:
    local_map = LocalMap(...)
    
    # Step 1: Create Road objects
    for road in odr_map.roads:
        road_obj = Road(
            road_id=int(road.id),
            road_name=road.name,
            road_length=road.length,
            road_type=extract_road_type(road),
            predecessor_road_id=extract_predecessor_road(road),
            successor_road_id=extract_successor_road(road),
            predecessor_junction_id=extract_predecessor_junction(road),
            successor_junction_id=extract_successor_junction(road),
            lane_ids=[],  # Will be populated later
            reference_line=extract_reference_line(road),
            speed_limit=extract_speed_limit(road)
        )
        local_map.roads.append(road_obj)
    
    # Step 2: Create Junction objects
    for junction in odr_map.get_junctions():
        road_ids = set()
        for conn in junction.id_to_connection.values():
            road_ids.add(conn.incoming_road)
            road_ids.add(conn.connecting_road)
        
        junction_obj = Junction(
            junction_id=int(junction.id),
            junction_name=junction.name,
            junction_type=extract_junction_type(junction),
            road_ids=list(road_ids),
            connection_count=len(junction.id_to_connection),
            has_traffic_light=len(junction.id_to_controller) > 0,
            controller_ids=list(junction.id_to_controller.keys()),
            polygon_points=calculate_junction_polygon(junction, odr_map),
            center_point=calculate_junction_center(junction, odr_map)
        )
        local_map.junctions.append(junction_obj)
    
    # Step 3: Create Lane objects with road/junction associations
    for road in odr_map.roads:
        for lanesection in road.get_lanesections():
            for lane in lanesection.get_lanes():
                lane_id = generate_lane_id(road.id, lanesection.s0, lane.id)
                
                lane_obj = Lane(
                    lane_id=lane_id,
                    lanelet_id=lane_id,  # Use same ID for simplicity
                    lane_type=convert_lane_type(lane.type),
                    lane_direction=convert_lane_direction(lane.id, road.left_hand_traffic),
                    # ... other fields ...
                    
                    # New fields
                    road_id=int(road.id),
                    junction_id=int(road.junction) if road.junction != "-1" else None,
                    is_junction_lane=(road.junction != "-1")
                )
                
                # Add lane to road's lane list
                road_obj = get_road_by_id(local_map, int(road.id))
                if road_obj:
                    road_obj.lane_ids.append(lane_id)
                
                local_map.lanes.append(lane_obj)
    
    # Step 4: Process junction connections for lane-to-lane links
    for junction in odr_map.get_junctions():
        junction_obj = get_junction_by_id(local_map, int(junction.id))
        
        for conn in junction.id_to_connection.values():
            incoming_road = get_road_by_id(local_map, int(conn.incoming_road))
            connecting_road = get_road_by_id(local_map, int(conn.connecting_road))
            
            for lane_link in conn.lane_links:
                # Find incoming lane
                incoming_lane_id = generate_lane_id(
                    conn.incoming_road, 
                    conn.contact_point,
                    lane_link.from
                )
                incoming_lane = get_lane_by_id(local_map, incoming_lane_id)
                
                # Find connecting lane
                connecting_lane_id = generate_lane_id(
                    conn.connecting_road,
                    conn.contact_point,
                    lane_link.to
                )
                connecting_lane = get_lane_by_id(local_map, connecting_lane_id)
                
                # Set lane connections (NO junction ID in successor_lane_ids)
                if incoming_lane and connecting_lane:
                    incoming_lane.successor_lane_ids.append(connecting_lane_id)
                    connecting_lane.predecessor_lane_ids.append(incoming_lane_id)
    
    return local_map
```

### 4.3 Connection Examples

**Example 1: Simple Junction**

```
XODR:
Road 1 (Lane 1) ──> Junction 664 ──> Road 2 (Lane 1)
  Connection: incomingRoad="1", connectingRoad="2"
    laneLink: from="1", to="1"

LocalMap:
Road 1:
  road_id = 1
  successor_junction_id = 664
  lane_ids = [lane_1_1]

Road 2:
  road_id = 2
  predecessor_junction_id = 664
  lane_ids = [lane_2_1]

Junction 664:
  junction_id = 664
  road_ids = [1, 2]
  connection_count = 1

Lane (Road 1, Lane 1):
  lane_id = lane_1_1
  road_id = 1
  junction_id = None
  is_junction_lane = False
  successor_lane_ids = [lane_2_1]  # Only lane ID, NO junction ID

Lane (Road 2, Lane 1):
  lane_id = lane_2_1
  road_id = 2
  junction_id = None
  is_junction_lane = False
  predecessor_lane_ids = [lane_1_1]  # Only lane ID, NO junction ID
```

**Example 2: Junction with Multiple Connections**

```
XODR:
Road 1 (Lane 1, Lane 2) ──> Junction 664 ──> Road 675 (Lane 1)
                                                     ──> Road 676 (Lane 2)

LocalMap:
Lane (Road 1, Lane 1):
  successor_lane_ids = [lane_675_1]  # Only lane ID

Lane (Road 1, Lane 2):
  successor_lane_ids = [lane_676_2]  # Only lane ID
```

**Example 3: Junction Internal Lane**

```
XODR:
Road 675 (junction="664", Lane 1) ──> Road 2 (Lane 1)

LocalMap:
Road 675:
  road_id = 675
  successor_road_id = 2  # Direct road-to-road connection
  lane_ids = [lane_675_1]

Lane (Road 675, Lane 1):
  lane_id = lane_675_1
  road_id = 675
  junction_id = 664  # This is a junction internal lane
  is_junction_lane = True
  successor_lane_ids = [lane_2_1]  # Only lane ID
```

---

## 5. Query Capabilities

### 5.1 Road-Level Queries

```python
# Find all lanes in a specific road
def get_lanes_in_road(local_map: LocalMap, road_id: int) -> List[Lane]:
    road = get_road_by_id(local_map, road_id)
    return [get_lane_by_id(local_map, lane_id) for lane_id in road.lane_ids]

# Find road by name
def get_road_by_name(local_map: LocalMap, road_name: str) -> Optional[Road]:
    for road in local_map.roads:
        if road.road_name == road_name:
            return road
    return None

# Get road connection chain
def get_road_chain(local_map: LocalMap, road_id: int) -> List[Road]:
    chain = []
    current = get_road_by_id(local_map, road_id)
    while current:
        chain.append(current)
        if current.successor_road_id:
            current = get_road_by_id(local_map, current.successor_road_id)
        else:
            break
    return chain
```

### 5.2 Junction-Level Queries

```python
# Find all roads connected to a junction
def get_roads_in_junction(local_map: LocalMap, junction_id: int) -> List[Road]:
    junction = get_junction_by_id(local_map, junction_id)
    return [get_road_by_id(local_map, road_id) for road_id in junction.road_ids]

# Find all lanes in a junction
def get_lanes_in_junction(local_map: LocalMap, junction_id: int) -> List[Lane]:
    roads = get_roads_in_junction(local_map, junction_id)
    lanes = []
    for road in roads:
        lanes.extend(get_lanes_in_road(local_map, road.road_id))
    return lanes

# Find junctions with traffic lights
def get_signalized_junctions(local_map: LocalMap) -> List[Junction]:
    return [j for j in local_map.junctions if j.has_traffic_light]
```

### 5.3 Lane-Level Queries

```python
# Find lane's road
def get_lane_road(local_map: LocalMap, lane_id: int) -> Optional[Road]:
    lane = get_lane_by_id(local_map, lane_id)
    if lane and lane.road_id:
        return get_road_by_id(local_map, lane.road_id)
    return None

# Find lane's junction
def get_lane_junction(local_map: LocalMap, lane_id: int) -> Optional[Junction]:
    lane = get_lane_by_id(local_map, lane_id)
    if lane and lane.junction_id:
        return get_junction_by_id(local_map, lane.junction_id)
    return None

# Find path through junction
def find_path_through_junction(local_map: LocalMap, from_lane_id: int, to_lane_id: int) -> List[int]:
    from_lane = get_lane_by_id(local_map, from_lane_id)
    to_lane = get_lane_by_id(local_map, to_lane_id)
    
    # Check if both lanes connect through same junction
    if from_lane.junction_id and to_lane.junction_id and from_lane.junction_id == to_lane.junction_id:
        # Direct connection exists
        if to_lane_id in from_lane.successor_lane_ids:
            return [from_lane_id, to_lane_id]
    
    return []
```

---

## 6. Benefits of Extended Structure

### 6.1 Preserves XODR Topology

- **Road hierarchy**: Maintains XODR's road-based organization
- **Junction connections**: Preserves junction as a first-class concept
- **Lane-to-lane routing**: Enables precise path planning through junctions

### 6.2 Enables Efficient Queries

- **Road-level queries**: "Find all lanes in Road 1"
- **Junction-level queries**: "Find all roads in Junction 664"
- **Lane-level queries**: "Find next lane from Road 1 Lane 1"

### 6.3 Backward Compatibility

- **Existing fields unchanged**: All existing LocalMap fields remain the same
- **Optional new fields**: New fields are optional (Optional[int])
- **Gradual migration**: Can migrate incrementally

---

## 7. Migration Path

### 7.1 Phase 1: Add New Data Types

1. Add `Road` dataclass to `local_map_data.py`
2. Add `Junction` dataclass to `local_map_data.py` (extends existing Intersection)
3. Add `roads` and `junctions` fields to `LocalMap`

### 7.2 Phase 2: Extend Lane Structure

1. Add `road_id` field to `Lane`
2. Add `junction_id` field to `Lane`
3. Add `is_junction_lane` field to `Lane`

### 7.3 Phase 3: Update Converters

1. Update OSM converter to populate new fields (set to None)
2. Implement XODR converter to populate new fields
3. Update validation functions to check new fields

### 7.4 Phase 4: Update Query Functions

1. Add road-level query functions
2. Add junction-level query functions
3. Update existing lane-level queries to use new fields

---

## 8. Comparison with OSM

### 8.1 OSM Structure

- **Way-based**: OSM uses ways (sequences of nodes)
- **Relation-based**: Junctions are relations between ways
- **No explicit Road concept**: Roads are implicit from way sequences

### 8.2 XODR Structure

- **Road-based**: XODR has explicit Road objects
- **Junction-based**: Junctions are explicit objects with connections
- **Explicit lane hierarchy**: Road → LaneSection → Lane

### 8.3 Mapping Strategy

| Concept | OSM | XODR | LocalMap |
|----------|-------|--------|-----------|
| Road | Implicit (way) | Explicit (Road) | Explicit (Road) |
| Junction | Relation | Explicit (Junction) | Explicit (Junction) |
| Lane | Implicit | Explicit (Lane) | Explicit (Lane) |
| Connection | Relation member | Junction connection | Lane successor/predecessor |

---

## 9. Implementation Notes

### 9.1 ID Generation

**Road ID:**
```python
road_id = int(road.id)  # Direct mapping
```

**Junction ID:**
```python
junction_id = int(junction.id)  # Direct mapping
```

**Lane ID:**
```python
lane_id = hash(f"{road.id}_{lanesection.s0}_{lane.id}")
```

### 9.2 Memory Considerations

- **Road objects**: Lightweight, store metadata only
- **Junction objects**: Store connection info, not full geometry
- **Lane objects**: Store geometry, reference roads/junctions

### 9.3 Performance Considerations

- **Road lookup**: Use dictionary for O(1) access
- **Junction lookup**: Use dictionary for O(1) access
- **Lane lookup**: Use dictionary for O(1) access

---

## 10. Testing

### 10.1 Unit Tests

- Test Road creation from XODR
- Test Junction creation from XODR
- Test Lane creation with road/junction associations
- Test lane-to-lane connections through junctions

### 10.2 Integration Tests

- Test complete XODR to LocalMap conversion
- Test road-level queries
- Test junction-level queries
- Test lane-level queries with junction connections

### 10.3 Validation Tests

- Validate all lanes have road_id set
- Validate junction lanes have junction_id set
- Validate non-junction lanes have junction_id = None
- Validate lane connections don't contain junction IDs

---

## 11. References

- **XODR Specification**: ASAM OpenDRIVE 1.4
- **LocalMap Data**: `src/common/local_map/local_map_data.py`
- **XODR Mapping**: `DATA_TYPE_MAPPING.md`
- **pyOpenDRIVE API**: `pyOpenDRIVE/pyOpenDRIVE/`

---

## 12. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-08 | System | Initial version - Road and Junction data types |
