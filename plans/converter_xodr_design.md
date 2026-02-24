# XODRConverter 详细设计文档

## 1. 概述

XODRConverter负责将OpenDRIVE格式的地图数据转换为统一的LocalMap格式。该模块直接使用pyOpenDRIVE的原生API，不经过MapAPI层，以保留XODR特有属性（junctions、road objects等）。

## 2. 架构位置

```mermaid
graph TB
    subgraph MapLoader[maploader/]
        LOADER_XD[loader_xodr.py<br/>XODRMapData]
    end
    
    subgraph LocalMap[localmap/]
        ROOT[__init__.py<br/>LocalMapBuilder]
        OSM[osmconvert/]
        XODR[xodrconvert/]
        SHARED[shared/]
    end
    
    subgraph XODRContent[xodrconvert]
        CONVERTER[converter_xodr.py<br/>XODRConverter]
    end
    
    subgraph Shared[shared]
        TRANSFORMER[transformer.py]
        CACHE[cache.py]
    end
    
    LOADER_XD --> ROOT
    ROOT --> XODR
    XODR --> CONVERTER
    XODR --> SHARED
    CONVERTER --> TRANSFORMER
    
    style CONVERTER fill:#ffe1e1
    style ROOT fill:#e1ffe1
```

## 3. 类设计

### 3.1 XODRConverter

```mermaid
classDiagram
    class XODRConverter {
        -xodr_data: XODRMapData
        -transformer: CoordinateTransformer
        -ego_pose: Pose
        -range: float
        +__init__(xodr_data: XODRMapData, transformer: CoordinateTransformer)
        +convert_to_local_map(ego_pose: Pose, range: float) ConversionResult
        -_convert_lanes(ego_pose: Pose, range: float) List[Lane]
        -_convert_junctions(ego_pose: Pose, range: float) List[Junction]
        -_convert_road_objects(ego_pose: Pose, range: float) List[RoadObject]
        -_convert_traffic_signs(ego_pose: Pose, range: float) List[TrafficSign]
        -_convert_speed_limits(ego_pose: Pose, range: float) List[SpeedLimitSegment]
        -_convert_single_lane(xodr_lane: PyLane, ego_pose: Pose) Lane
        -_convert_single_junction(xodr_junction: PyJunction, ego_pose: Pose) Junction
        -_convert_single_road_object(xodr_object: PyRoadObject, ego_pose: Pose) RoadObject
        -_is_in_range(xodr_element, ego_pose: Pose, range: float) bool
    }
    
    class XODRMapData {
        +get_roads() List[PyRoad]
        +get_road_by_id(road_id: str) PyRoad
        +get_lanesections(road: PyRoad) List[PyLaneSection]
        +get_lanes(lanesection: PyLaneSection) List[PyLane]
        +get_junctions() List[PyJunction]
        +get_junction_by_id(junction_id: str) PyJunction
    }
    
    class CoordinateTransformer {
        +global_to_local(position: Position) TransformResult
        +local_to_global(point: Point3D) TransformResult
        +update_ego_pose(ego_pose: Pose) None
    }
    
    class ConversionResult {
        +success: bool
        +data: Optional[LocalMap]
        +warnings: List[str]
        +errors: List[str]
    }
    
    XODRConverter --> XODRMapData
    XODRConverter --> CoordinateTransformer
    XODRConverter --> ConversionResult
```

## 4. 数据流设计

### 4.1 完整转换流程

```mermaid
flowchart TD
    START[开始] --> INPUT[输入: XODRMapData, ego_pose, range]
    INPUT --> LANE[_convert_lanes]
    INPUT --> JUNC[_convert_junctions]
    INPUT --> OBJ[_convert_road_objects]
    INPUT --> SIGN[_convert_traffic_signs]
    INPUT --> SPEED[_convert_speed_limits]
    
    LANE --> LANE1[遍历所有Road]
    LANE1 --> LANE2[遍历所有LaneSection]
    LANE2 --> LANE3[遍历所有Lane]
    LANE3 --> LANE4[检查是否在范围内]
    LANE4 -->|是| LANE5[转换单个Lane]
    LANE5 --> LANE6[添加到lanes列表]
    
    JUNC --> JUNC1[遍历所有Junction]
    JUNC1 --> JUNC2[检查是否在范围内]
    JUNC2 -->|是| JUNC3[转换单个Junction]
    JUNC3 --> JUNC4[添加到junctions列表]
    
    OBJ --> OBJ1[遍历所有RoadObject]
    OBJ1 --> OBJ2[检查是否在范围内]
    OBJ2 -->|是| OBJ3[转换单个RoadObject]
    OBJ3 --> OBJ4[添加到road_objects列表]
    
    SIGN --> SIGN1[遍历所有RoadSignal]
    SIGN1 --> SIGN2[检查是否在范围内]
    SIGN2 -->|是| SIGN3[转换单个TrafficSign]
    SIGN3 --> SIGN4[添加到traffic_signs列表]
    
    SPEED --> SPEED1[从Lane提取限速信息]
    SPEED1 --> SPEED2[转换为SpeedLimitSegment]
    SPEED2 --> SPEED3[添加到speed_limits列表]
    
    LANE6 --> BUILD[构建LocalMap]
    JUNC4 --> BUILD
    OBJ4 --> BUILD
    SIGN4 --> BUILD
    SPEED3 --> BUILD
    
    BUILD --> RESULT[返回ConversionResult]
    RESULT --> END[结束]
    
    style LANE5 fill:#e1f5ff
    style JUNC3 fill:#ffe1e1
    style OBJ3 fill:#ffe1e1
    style BUILD fill:#e1ffe1
```

### 4.2 Lane转换流程

```mermaid
flowchart TD
    START[开始转换单个Lane] --> GET_CENTER[获取Lane中心线]
    GET_CENTER --> TRANS_CENTER[转换到局部坐标]
    TRANS_CENTER --> GET_BOUNDS[获取Lane边界]
    GET_BOUNDS --> TRANS_BOUNDS[转换边界到局部坐标]
    TRANS_BOUNDS --> GET_SPEED[获取限速信息]
    GET_SPEED --> TRANS_SPEED[转换限速到局部坐标]
    TRANS_SPEED --> BUILD_LANE[构建Lane对象]
    BUILD_LANE --> END[返回Lane]
    
    style TRANS_CENTER fill:#e1ffe1
    style TRANS_BOUNDS fill:#e1ffe1
```

### 4.3 Junction转换流程

```mermaid
flowchart TD
    START[开始转换单个Junction] --> GET_POS[获取Junction位置]
    GET_POS --> TRANS_POS[转换到局部坐标]
    TRANS_POS --> GET_CONN[获取所有连接]
    GET_CONN --> TRANS_CONN[转换连接信息]
    TRANS_CONN --> DETECT_TYPE[检测Junction类型]
    DETECT_TYPE --> BUILD_JUNC[构建Junction对象]
    BUILD_JUNC --> END[返回Junction]
    
    style TRANS_POS fill:#e1ffe1
    style TRANS_CONN fill:#e1ffe1
```

## 5. 详细方法设计

### 5.1 convert_to_local_map

```python
def convert_to_local_map(self, ego_pose: Pose, range: float) -> ConversionResult:
    """
    将XODR数据转换为LocalMap
    
    Args:
        ego_pose: 自车位姿（局部坐标系原点）
        range: 局部地图范围（米）
        
    Returns:
        ConversionResult包含:
        - success: 转换是否成功
        - data: LocalMap对象（成功时）
        - warnings: 警告列表
        - errors: 错误列表
    """
```

**实现步骤：**
1. 更新transformer的ego_pose
2. 转换lanes
3. 转换junctions
4. 转换road_objects
5. 转换traffic_signs
6. 转换speed_limits
7. 构建LocalMap对象
8. 返回ConversionResult

### 5.2 _convert_lanes

```python
def _convert_lanes(self, ego_pose: Pose, range: float) -> List[Lane]:
    """
    转换所有在范围内的Lanes
    
    Args:
        ego_pose: 自车位姿
        range: 搜索范围（米）
        
    Returns:
        Lane对象列表
    """
```

**实现步骤：**
1. 遍历所有Road
2. 遍历每个Road的LaneSection
3. 遍历每个LaneSection的Lane
4. 检查Lane是否在范围内（使用Lane的s坐标）
5. 调用_convert_single_lane转换单个Lane
6. 收集所有转换后的Lane

**范围判断策略：**
- 使用Lane的s坐标（沿道路方向的距离）
- 计算Lane中心点到ego_pose的距离
- 距离 <= range的Lane被包含

### 5.3 _convert_single_lane

```python
def _convert_single_lane(self, xodr_lane: PyLane, ego_pose: Pose) -> Lane:
    """
    转换单个XODR Lane到LocalMap Lane
    
    Args:
        xodr_lane: pyOpenDRIVE的Lane对象
        ego_pose: 自车位姿
        
    Returns:
        LocalMap的Lane对象
    """
```

**转换内容：**

| XODR属性 | LocalMap属性 | 转换方法 |
|----------|-------------|----------|
| lane.id | lane_id | 直接使用 |
| lane.type | lane_type | 枚举映射 |
| center line | centerline_points | 转换坐标 |
| speed limit | speed_limits | 提取并转换 |
| lane width | - | 用于边界计算 |

**Lane类型映射：**

| XODR Lane Type | LocalMap LaneType |
|----------------|------------------|
| driving | DRIVING |
| sidewalk | SIDEWALK |
| parking | PARKING |
| stop | UNKNOWN |
| none | UNKNOWN |

### 5.4 _convert_junctions

```python
def _convert_junctions(self, ego_pose: Pose, range: float) -> List[Junction]:
    """
    转换所有在范围内的Junctions
    
    Args:
        ego_pose: 自车位姿
        range: 搜索范围（米）
        
    Returns:
        Junction对象列表
    """
```

**实现步骤：**
1. 遍历所有Junction
2. 检查Junction是否在范围内
3. 调用_convert_single_junction转换单个Junction
4. 收集所有转换后的Junction

**范围判断策略：**
- 使用Junction的中心位置
- 计算到ego_pose的距离
- 距离 <= range的Junction被包含

### 5.5 _convert_single_junction

```python
def _convert_single_junction(self, xodr_junction: PyJunction, ego_pose: Pose) -> Junction:
    """
    转换单个XODR Junction到LocalMap Junction
    
    Args:
        xodr_junction: pyOpenDRIVE的Junction对象
        ego_pose: 自车位姿
        
    Returns:
        LocalMap的Junction对象
    """
```

**转换内容：**

| XODR属性 | LocalMap属性 | 转换方法 |
|----------|-------------|----------|
| junction.id | junction_id | 直接使用 |
| junction.name | name | 直接使用 |
| junction position | position | 转换坐标 |
| connections | connections | 转换连接信息 |
| junction type | junction_type | 检测类型 |

**Junction类型检测：**

| 连接数 | 类型 |
|--------|------|
| 3 | t_junction |
| 4 | intersection |
| 环形 | roundabout |

### 5.6 _convert_road_objects

```python
def _convert_road_objects(self, ego_pose: Pose, range: float) -> List[RoadObject]:
    """
    转换所有在范围内的RoadObjects
    
    Args:
        ego_pose: 自车位姿
        range: 搜索范围（米）
        
    Returns:
        RoadObject对象列表
    """
```

**实现步骤：**
1. 遍历所有Road
2. 遍历每个Road的RoadObject
3. 检查RoadObject是否在范围内
4. 调用_convert_single_road_object转换单个RoadObject
5. 收集所有转换后的RoadObject

### 5.7 _convert_single_road_object

```python
def _convert_single_road_object(self, xodr_object: PyRoadObject, ego_pose: Pose) -> RoadObject:
    """
    转换单个XODR RoadObject到LocalMap RoadObject
    
    Args:
        xodr_object: pyOpenDRIVE的RoadObject对象
        ego_pose: 自车位姿
        
    Returns:
        LocalMap的RoadObject对象
    """
```

**转换内容：**

| XODR属性 | LocalMap属性 | 转换方法 |
|----------|-------------|----------|
| object.id | object_id | 直接使用 |
| object.type | object_type | 直接使用 |
| object position | position | 转换坐标 |
| object orientation | orientation | 直接使用 |
| object dimensions | dimensions | 转换尺寸 |

**RoadObject类型映射：**

| XODR Object Type | LocalMap Object Type |
|------------------|---------------------|
| barrier | barrier |
| pole | pole |
| tree | tree |
| building | building |
| wall | wall |

### 5.8 _convert_traffic_signs

```python
def _convert_traffic_signs(self, ego_pose: Pose, range: float) -> List[TrafficSign]:
    """
    转换所有在范围内的TrafficSigns（RoadSignals）
    
    Args:
        ego_pose: 自车位姿
        range: 搜索范围（米）
        
    Returns:
        TrafficSign对象列表
    """
```

**实现步骤：**
1. 遍历所有Road
2. 遍历每个Road的RoadSignal
3. 检查RoadSignal是否在范围内
4. 转换为TrafficSign对象
5. 收集所有转换后的TrafficSign

### 5.9 _convert_speed_limits

```python
def _convert_speed_limits(self, ego_pose: Pose, range: float) -> List[SpeedLimitSegment]:
    """
    转换所有在范围内的SpeedLimits
    
    Args:
        ego_pose: 自车位姿
        range: 搜索范围（米）
        
    Returns:
        SpeedLimitSegment对象列表
    """
```

**实现步骤：**
1. 遍历所有在范围内的Lane
2. 提取每个Lane的speed limit信息
3. 转换为SpeedLimitSegment对象
4. 收集所有转换后的SpeedLimitSegment

## 6. 坐标转换策略

### 6.1 全局坐标到局部坐标

```python
# XODR使用全局坐标（x, y, z）
# 需要转换为局部坐标（相对于ego_pose）

def global_to_local(global_pos: Tuple[float, float, float], ego_pose: Pose) -> Point3D:
    """
    将全局坐标转换为局部坐标
    
    Args:
        global_pos: 全局坐标 (x, y, z)
        ego_pose: 自车位姿（局部坐标系原点）
        
    Returns:
        局部坐标 Point3D
    """
    # 1. 计算相对位置
    dx = global_pos[0] - ego_pose.position.x
    dy = global_pos[1] - ego_pose.position.y
    dz = global_pos[2] - ego_pose.position.z
    
    # 2. 旋转到局部坐标系
    cos_h = math.cos(-ego_pose.heading)
    sin_h = math.sin(-ego_pose.heading)
    
    local_x = dx * cos_h - dy * sin_h
    local_y = dx * sin_h + dy * cos_h
    local_z = dz
    
    return Point3D(x=local_x, y=local_y, z=local_z)
```

### 6.2 范围判断

```python
def is_in_range(element_pos: Tuple[float, float], ego_pose: Pose, range: float) -> bool:
    """
    判断元素是否在范围内
    
    Args:
        element_pos: 元素位置 (x, y)
        ego_pose: 自车位姿
        range: 搜索范围（米）
        
    Returns:
        True如果在范围内
    """
    dx = element_pos[0] - ego_pose.position.x
    dy = element_pos[1] - ego_pose.position.y
    distance = math.sqrt(dx * dx + dy * dy)
    
    return distance <= range
```

## 7. 性能优化

### 7.1 空间索引

```python
class SpatialIndex:
    """空间索引用于快速范围查询"""
    
    def __init__(self):
        self.elements = []  # (position, element) tuples
    
    def add(self, position: Tuple[float, float], element):
        """添加元素"""
        self.elements.append((position, element))
    
    def query(self, ego_pose: Pose, range: float) -> List:
        """查询范围内的元素"""
        result = []
        for pos, elem in self.elements:
            if is_in_range(pos, ego_pose, range):
                result.append(elem)
        return result
```

### 7.2 缓存策略

```python
class ConversionCache:
    """转换结果缓存"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 简单的LRU策略：删除第一个
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value
```

## 8. 错误处理

### 8.1 错误类型

| 错误类型 | 描述 | 处理方式 |
|----------|------|----------|
| XODRDataError | XODR数据解析错误 | 记录错误，返回失败 |
| CoordinateTransformError | 坐标转换错误 | 记录警告，跳过该元素 |
| OutOfRangeError | 元素超出范围 | 跳过该元素 |
| ConversionError | 转换逻辑错误 | 记录错误，返回失败 |

### 8.2 错误处理示例

```python
try:
    lane = self._convert_single_lane(xodr_lane, ego_pose)
    lanes.append(lane)
except CoordinateTransformError as e:
    logger.warning(f"Failed to transform lane {lane.id}: {e}")
    warnings.append(f"Lane {lane.id} coordinate transform failed")
except ConversionError as e:
    logger.error(f"Failed to convert lane {lane.id}: {e}")
    errors.append(f"Lane {lane.id} conversion failed")
```

## 9. 测试策略

### 9.1 单元测试

```python
class TestXODRConverter(unittest.TestCase):
    """XODRConverter单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.xodr_data = load_test_xodr()
        self.transformer = CoordinateTransformer(Pose())
        self.converter = XODRConverter(self.xodr_data, self.transformer)
    
    def test_convert_single_lane(self):
        """测试单个Lane转换"""
        lane = get_test_lane()
        result = self.converter._convert_single_lane(lane, Pose())
        self.assertIsNotNone(result)
        self.assertEqual(result.lane_id, lane.id)
    
    def test_convert_junction(self):
        """测试Junction转换"""
        junction = get_test_junction()
        result = self.converter._convert_single_junction(junction, Pose())
        self.assertIsNotNone(result)
        self.assertEqual(result.junction_id, junction.id)
```

### 9.2 集成测试

```python
class TestXODRConverterIntegration(unittest.TestCase):
    """XODRConverter集成测试"""
    
    def test_full_conversion(self):
        """测试完整转换流程"""
        xodr_data = load_test_xodr("test.xodr")
        transformer = CoordinateTransformer(Pose())
        converter = XODRConverter(xodr_data, transformer)
        
        ego_pose = Pose(position=Point3D(x=0, y=0, z=0), heading=0)
        result = converter.convert_to_local_map(ego_pose, range=200.0)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertGreater(len(result.data.lanes), 0)
```

## 10. 文件结构

```
src/localmap/xodrconvert/
├── __init__.py
├── converter_xodr.py        # 主转换器
├── xodr_adapter.py          # XODR数据适配器
├── lane_converter.py        # Lane转换
├── junction_converter.py     # Junction转换
├── object_converter.py       # RoadObject转换
├── sign_converter.py        # TrafficSign转换
├── utils.py               # 工具函数
└── tests/
    ├── test_converter.py
    ├── test_lane_converter.py
    └── test_junction_converter.py
```

## 11. 依赖关系

```mermaid
graph LR
    XODRConv[converter_xodr.py] --> XODRAdapter[xodr_adapter.py]
    XODRConv --> LaneConv[lane_converter.py]
    XODRConv --> JuncConv[junction_converter.py]
    XODRConv --> ObjConv[object_converter.py]
    XODRConv --> SignConv[sign_converter.py]
    XODRConv --> Utils[utils.py]
    XODRConv --> Transformer[../shared/transformer.py]
    XODRConv --> LocalMapData[../../common/local_map/local_map_data.py]
    
    style XODRConv fill:#ffe1e1
    style Transformer fill:#e1ffe1
    style LocalMapData fill:#e1f5ff
```

## 12. 实现优先级

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | Lane转换 | 核心功能，必须实现 |
| P0 | 坐标转换 | 核心功能，必须实现 |
| P1 | Junction转换 | 重要功能，需要实现 |
| P1 | RoadObject转换 | 重要功能，需要实现 |
| P2 | TrafficSign转换 | 次要功能，可以后续实现 |
| P2 | SpeedLimit转换 | 次要功能，可以后续实现 |
| P3 | 空间索引优化 | 性能优化，可以后续实现 |
| P3 | 缓存策略 | 性能优化，可以后续实现 |
