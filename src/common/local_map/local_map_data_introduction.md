# 局部地图数据结构定义提案
## Local Map Data Structure Proposal

**版本 / Version**: 2.3
**日期 / Date**: 2026-02-03
**坐标系 / Coordinate System**: 自车局部坐标系 (Ego Vehicle Local Coordinate System)
**实现语言 / Implementation Language**: Python (dataclass)
**兼容性 / Compatibility**: 可扩展至C++ (Extensible to C++)

---

## 1. 概述 / Overview

本文档定义了从高精地图到交规判断之间的局部地图接口数据结构。该数据结构用于在自车局部坐标系下表示周围环境的道路几何、交通设施和交规元素，为交规判断模块提供必要的输入信息。

This document defines the data structure for the local map interface between high-definition maps and traffic rule judgment. This data structure represents the surrounding road geometry, traffic facilities, and traffic rule elements in the ego vehicle's local coordinate system, providing necessary input for the traffic rule judgment module.

### 1.1 设计原则 / Design Principles

1. **语言无关性 / Language Agnostic**: 使用Python dataclass定义，可转换为C++结构体
2. **分段支持 / Segmentation Support**: 车道边界和限速支持分段定义
3. **关联关系 / Association**: 每条车道维护关联元素的ID列表（参考Apollo / Reference Apollo）
4. **可扩展性 / Extensibility**: 预留扩展字段，支持未来需求
5. **边界点存储 / Boundary Point Storage**: 边界点存储在LaneBoundarySegment中，相邻车道可通过引用共享点
6. **多格式支持 / Multi-Format Support**: 采用适配器模式，支持从多种HD地图格式（Lanelet2、OpenDRIVE/XODR、Apollo等）转换到统一的局部地图格式

### 1.2 架构设计 / Architecture Design

为了支持多种高精地图格式，本设计采用**适配器模式**，将交规判断模块与具体的HD地图格式解耦。

To support multiple HD map formats, this design adopts the **Adapter Pattern**, decoupling the traffic rule judgment module from specific HD map formats.

```
┌─────────────────────────────────────────────────────────┐
│                    交规判断模块                          │
│              (Traffic Rule Judgment)                    │
│                                                         │
│  只依赖: LocalMap数据结构                                │
│  Only depends on: LocalMap data structure               │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ 统一接口 / Unified Interface
                            │
                            │
┌─────────────────────────────────────────────────────────┐
│              地图转换适配器层                             │
│              (Map Converter Adapters)                    │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Lanelet2转换器   │  │  XODR转换器      │              │
│  │ Lanelet2Converter│  │ XODRConverter   │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Apollo转换器     │  │  ...其他格式     │              │
│  │ ApolloConverter  │  │  OtherFormats   │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    Lanelet2              XODR                Apollo
```

**优势 / Advantages:**

1. **解耦 / Decoupling**: 交规判断模块只依赖自定义的LocalMap格式，与HD地图格式无关
2. **灵活 / Flexibility**: 每种HD地图格式只需一个转换器，新增格式只需添加新的转换器
3. **优化 / Optimization**: 转换器可以针对交规判断的需求进行优化，只提取必要信息
4. **扩展 / Extensibility**: 未来支持新的HD地图格式无需修改交规判断模块

### 1.3 转换器接口定义 / Converter Interface Definition

所有HD地图转换器应实现统一的接口：

All HD map converters should implement a unified interface:

```python
from abc import ABC, abstractmethod
from typing import Optional

class HDMapConverter(ABC):
    """高精地图转换器基类 / Base class for HD map converters"""
    
    @abstractmethod
    def convert_to_local_map(
        self,
        hd_map: Any,
        ego_pose: Pose,
        range: float = 200.0
    ) -> LocalMap:
        """
        将HD地图转换为局部地图
        Convert HD map to local map
        
        Args:
            hd_map: HD地图对象 / HD map object
            ego_pose: 自车位姿 / Ego vehicle pose
            range: 转换范围（米）/ Conversion range (meters)
        
        Returns:
            LocalMap: 局部地图对象 / Local map object
        """
        pass
    
    @abstractmethod
    def get_supported_format(self) -> str:
        """
        获取支持的HD地图格式
        Get supported HD map format
        
        Returns:
            str: 格式名称 / Format name (e.g., "lanelet2", "xodr", "apollo")
        """
        pass
```

**示例 / Example:**

```python
class Lanelet2Converter(HDMapConverter):
    """Lanelet2格式转换器 / Lanelet2 format converter"""
    
    def convert_to_local_map(self, hd_map, ego_pose, range=200.0):
        # 实现Lanelet2到LocalMap的转换逻辑
        # Implement conversion logic from Lanelet2 to LocalMap
        pass
    
    def get_supported_format(self) -> str:
        return "lanelet2"


class XODRConverter(HDMapConverter):
    """OpenDRIVE/XODR格式转换器 / OpenDRIVE/XODR format converter"""
    
    def convert_to_local_map(self, hd_map, ego_pose, range=200.0):
        # 实现XODR到LocalMap的转换逻辑
        # Implement conversion logic from XODR to LocalMap
        pass
    
    def get_supported_format(self) -> str:
        return "xodr"
```

### 1.4 长时序交规判断支持 / Long-Term Traffic Rule Judgment Support

交规判断是长时序问题，需要考虑历史状态。典型场景包括：

Traffic rule judgment is a long-term problem that requires considering historical states. Typical scenarios include:

| 场景 / Scenario | 时间跨度 / Time Span | 空间范围 / Spatial Range | 说明 / Description |
|-----------------|---------------------|------------------------|-------------------|
| 连续变道 / Continuous Lane Change | 10s | ~150-200m | 需要跟踪变道过程中的状态 / Need to track state during lane change |
| 转弯前打转向灯 / Turn Signal Before Turn | 30m | 30m | 需要判断转弯前30m是否已打转向灯 / Need to check if turn signal was activated 30m before turn |
| 超车 / Overtaking | 5-10s | ~100-150m | 需要跟踪超车过程中的状态 / Need to track state during overtaking |
| 让行 / Yielding | 5-15s | ~100-200m | 需要跟踪让行过程中的状态 / Need to track state during yielding |

#### 1.4.1 解决方案 / Solution

**推荐方案：局部地图 + 历史状态管理器**

**Recommended Solution: Local Map + Historical State Manager**

```
┌─────────────────────────────────────────────────────────┐
│                    交规判断模块                          │
│              (Traffic Rule Judgment)                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │           历史状态管理器                          │  │
│  │       (History State Manager)                    │  │
│  │                                                   │  │
│  │  - 转向灯状态 / Turn signal state                 │  │
│  │  - 变道状态 / Lane change state                  │  │
│  │  - 超车状态 / Overtaking state                   │  │
│  │  - 让行状态 / Yielding state                     │  │
│  │  - 时间戳 / Timestamp                            │  │
│  │  - 历史轨迹 / Historical trajectory              │  │
│  └─────────────────────────────────────────────────┘  │
│                          ▲                              │
│                          │                              │
│  ┌───────────────────────┴─────────────────────────┐  │
│  │              交规规则引擎                          │  │
│  │          (Traffic Rule Engine)                    │  │
│  │                                                   │  │
│  │  输入: LocalMap + 历史状态                         │  │
│  │  Input: LocalMap + History State                  │  │
│  │                                                   │  │
│  │  输出: 交规判断结果                                │  │
│  │  Output: Traffic rule judgment result             │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### 1.4.2 局部地图范围设计 / Local Map Range Design

**推荐范围：200-300m**

**Recommended Range: 200-300m**

**设计理由 / Design Rationale:**

1. **覆盖大部分场景**：200-300m范围可以覆盖大部分长时序交规判断场景
   - **Covers most scenarios**: 200-300m range covers most long-term traffic rule judgment scenarios
   
2. **性能可控**：100ms的更新频率下，200-300m范围的数据处理性能足够
   - **Controlled performance**: With 100ms update frequency, processing 200-300m range data is sufficient
   
3. **历史状态管理**：交规判断模块自己维护历史状态，不依赖局部地图
   - **Historical state management**: Traffic rule judgment module maintains its own historical state, independent of local map

---

## 2. 坐标系定义 / Coordinate System Definition

### 2.1 自车局部坐标系 / Ego Vehicle Local Coordinate System

- **原点 / Origin**: 自车后轴中心点 (Center of rear axle)
- **X轴 / X-axis**: 自车前进方向 (Forward direction of ego vehicle)
- **Y轴 / Y-axis**: 自车左侧方向 (Left direction of ego vehicle)
- **Z轴 / Z-axis**: 垂直向上方向 (Vertical upward direction)
- **单位 / Unit**: 米 (Meters)

---

## 3. 核心数据结构 / Core Data Structures

### 3.1 局部地图主结构 / Local Map Main Structure

```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class LocalMap:
    """局部地图主结构 / Local Map Main Structure"""
    header: Header                          # 时间戳和坐标系信息 / Timestamp and coordinate frame info
    metadata: LocalMapMetadata              # 地图元数据 / Map metadata
    lanes: List[Lane]                       # 车道信息 / Lane information
    traffic_lights: List[TrafficLight]      # 红绿灯信息 / Traffic light information
    traffic_signs: List[TrafficSign]        # 交通标志信息 / Traffic sign information
    road_markings: List[RoadMarking]        # 道路标线信息 / Road marking information
    crosswalks: List[Crosswalk]             # 人行横道信息 / Crosswalk information
    stop_lines: List[StopLine]              # 停止线信息 / Stop line information
    intersections: List[Intersection]      # 交叉口信息 / Intersection information
    
    # 边界分段池子 / Boundary segment pool
    # 用于存储所有边界分段，支持相邻车道共享边界分段
    # Stores all boundary segments, supports boundary segment sharing between adjacent lanes
    boundary_segments: List[LaneBoundarySegment] = field(default_factory=list)
```

### 3.2 地图元数据 / Map Metadata

```python
@dataclass
class LocalMapMetadata:
    """地图元数据 / Map Metadata"""
    map_range_x: float                     # 地图X轴范围（米）/ Map X-axis range (meters)
    map_range_y: float                     # 地图Y轴范围（米）/ Map Y-axis range (meters)
    map_range_z: float                     # 地图Z轴范围（米）/ Map Z-axis range (meters)
    ego_vehicle_x: float                   # 自车X坐标（局部坐标系）/ Ego vehicle X coordinate (local frame)
    ego_vehicle_y: float                   # 自车Y坐标（局部坐标系）/ Ego vehicle Y coordinate (local frame)
    ego_vehicle_heading: float             # 自车航向角（弧度）/ Ego vehicle heading angle (radians)
    ego_vehicle_velocity: float            # 自车速度（米/秒）/ Ego vehicle velocity (m/s)
    timestamp: datetime                    # 数据生成时间戳 / Data generation timestamp

@dataclass
class Header:
    """消息头 / Message Header"""
    timestamp: datetime                    # 时间戳 / Timestamp
    frame_id: str                          # 坐标系ID / Coordinate frame ID
    sequence_number: int = 0               # 序列号 / Sequence number
```

---

## 4. 车道相关结构 / Lane-Related Structures

### 4.1 车道 / Lane

```python
@dataclass
class Lane:
    """车道 / Lane
    
    约束条件 / Constraints:
    - centerline_points 为空时，left_boundary_segment_indices 和 right_boundary_segment_indices 必须非空
      When centerline_points is empty, left_boundary_segment_indices and right_boundary_segment_indices must be non-empty
    """
    lane_id: int                           # 车道唯一标识符 / Unique lane identifier
    lanelet_id: int                        # 对应的高精地图lanelet ID / Corresponding HD map lanelet ID
    lane_type: LaneType                    # 车道类型 / Lane type
    lane_direction: LaneDirection          # 车道方向 / Lane direction
    
    # 中心线点集（可选）/ Centerline point set (optional)
    centerline_points: List[Point3D] = field(default_factory=list)  # 车道中心线点集 / Lane centerline point set
    
    # 边界定义（分段，通过索引引用）/ Boundary definition (segmented, referenced by index)
    # 通过索引引用LocalMap.boundary_segments中的边界分段
    # Reference boundary segments in LocalMap.boundary_segments by index
    # 相邻车道可以引用同一个segment_id来实现共享
    # Adjacent lanes can reference the same segment_id to achieve sharing
    left_boundary_segment_indices: List[int] = field(default_factory=list)  # 左边界分段索引列表 / Left boundary segment index list
    right_boundary_segment_indices: List[int] = field(default_factory=list) # 右边界分段索引列表 / Right boundary segment index list
    
    # 限速定义（分段）/ Speed limit definition (segmented)
    speed_limits: List[SpeedLimitSegment] # 限速分段列表 / Speed limit segment list
    
    # 关联元素ID列表 / Associated element ID lists (参考Apollo / Reference Apollo)
    associated_traffic_light_ids: List[int] = field(default_factory=list)      # 关联的信号灯ID / Associated traffic light IDs
    associated_traffic_sign_ids: List[int] = field(default_factory=list)      # 关联的交通标志ID / Associated traffic sign IDs
    associated_stop_line_ids: List[int] = field(default_factory=list)         # 关联的停止线ID / Associated stop line IDs
    associated_crosswalk_ids: List[int] = field(default_factory=list)         # 关联的人行横道ID / Associated crosswalk IDs
    associated_road_marking_ids: List[int] = field(default_factory=list)      # 关联的道路标线ID / Associated road marking IDs
    associated_intersection_id: Optional[int] = None                           # 关联的交叉口ID / Associated intersection ID
    
    # 相邻车道信息 / Adjacent lane information
    left_adjacent_lane_id: Optional[int] = None  # 左侧相邻车道ID / Left adjacent lane ID
    right_adjacent_lane_id: Optional[int] = None  # 右侧相邻车道ID / Right adjacent lane ID
    
    # 车道连接关系 / Lane connection relationships
    predecessor_lane_ids: List[int] = field(default_factory=list)  # 前继车道ID列表 / Predecessor lane ID list
    successor_lane_ids: List[int] = field(default_factory=list)      # 后继车道ID列表 / Successor lane ID list
```

### 4.2 车道边界分段 / Lane Boundary Segment

```python
@dataclass
class LaneBoundarySegment:
    """车道边界分段 / Lane Boundary Segment
    
    说明：车道边界需要分段定义，因为边界类型（实线/虚线）可能沿车道变化
    Description: Lane boundaries need to be defined in segments because boundary types (solid/dashed) may change along the lane
    
    注意：boundary_point_indices引用的点是边界线的中心点
    Note: Points referenced by boundary_point_indices are center points of boundary line
    
    共享机制 / Sharing Mechanism:
    - 相邻车道可以引用同一个LaneBoundarySegment来实现边界共享
    - Adjacent lanes can reference same LaneBoundarySegment to achieve boundary sharing
    - Lanelet2格式：相邻lanelet共享同一个linestring，转换时创建共享的LaneBoundarySegment
    - XODR格式：同一个road内的相邻lane可以共享边界，转换时按需创建共享的LaneBoundarySegment
    - LaneBoundarySegment是自包含的，包含完整的边界点数据
    - LaneBoundarySegment is self-contained, contains complete boundary point data
    """
    segment_id: int                        # 分段唯一标识符 / Unique segment identifier
    boundary_type: BoundaryType            # 边界类型 / Boundary type
    boundary_line_shape: BoundaryLineShape  # 边界线形状 / Boundary line shape
    boundary_color: BoundaryColor           # 边界颜色 / Boundary color
    boundary_thickness: float              # 边界线宽度（米）/ Boundary line thickness (meters)
    is_virtual: bool                       # 是否虚拟边界 / Whether virtual boundary
    
    # 边界点集（边界线中心点）/ Boundary point set (center points of boundary line)
    boundary_points: List[Point3D]         # 边界点列表 / Boundary point list
```

### 4.3 边界颜色枚举 / Boundary Color Enum

```python
class BoundaryColor(IntEnum):
    """边界颜色枚举 / Boundary Color Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    WHITE = 1                              # 白色 / White
    YELLOW = 2                             # 黄色 / Yellow
    BLUE = 3                               # 蓝色 / Blue
    RED = 4                                # 红色 / Red
```

### 4.4 限速分段 / Speed Limit Segment

```python
@dataclass
class SpeedLimitSegment:
    """限速分段 / Speed Limit Segment
    
    说明：每条车道的限速可能随位置变化，需要分段定义
    Description: Speed limit for each lane may change with position, needs to be defined in segments
    """
    segment_id: int                        # 分段唯一标识符 / Unique segment identifier
    speed_limit: float                     # 限速值（米/秒）/ Speed limit (m/s)
    min_speed_limit: float = 0.0          # 最低限速值（米/秒），默认为0表示无最低限速 / Minimum speed limit (m/s), default 0 means no minimum speed limit
    
    # 分段范围（绝对坐标）/ Segment range (absolute coordinates)
    start_position: Point3D                 # 分段起始位置（绝对坐标）/ Segment start position (absolute coordinates)
    end_position: Point3D                   # 分段结束位置（绝对坐标）/ Segment end position (absolute coordinates)
    
    # 关联的交通标志ID / Associated traffic sign ID
    associated_sign_id: Optional[int] = None  # 产生此限速的交通标志ID / Traffic sign ID that created this speed limit
    
    # 限速类型 / Speed limit type
    speed_limit_type: SpeedLimitType = SpeedLimitType.REGULAR  # 限速类型 / Speed limit type
```

### 4.5 限速类型枚举 / Speed Limit Type Enum

```python
from enum import IntEnum

class SpeedLimitType(IntEnum):
    """限速类型枚举 / Speed Limit Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    REGULAR = 1                            # 常规限速：道路默认限速 / Regular speed limit: default road speed limit
    TEMPORARY = 2                          # 临时限速：临时限速牌产生的限速 / Temporary speed limit: speed limit from temporary speed limit sign
    SCHOOL_ZONE = 3                        # 学校区域限速 / School zone speed limit
    CONSTRUCTION_ZONE = 4                  # 施工区域限速 / Construction zone speed limit
    WEATHER_CONDITION = 5                  # 天气条件限速 / Weather condition speed limit
```

### 4.6 车道类型枚举 / Lane Type Enum

```python
class LaneType(IntEnum):
    """车道类型枚举 / Lane Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    DRIVING = 1                            # 行驶车道 / Driving lane
    SHOULDER = 2                           # 路肩 / Shoulder
    PARKING = 3                            # 停车位 / Parking spot
    BIKING = 4                             # 自行车道 / Biking lane
    SIDEWALK = 5                           # 人行道 / Sidewalk
    CROSSWALK = 6                          # 人行横道 / Crosswalk
    EXIT = 7                               # 出口车道 / Exit lane
    ENTRY = 8                              # 入口车道 / Entry lane
    MERGE = 9                              # 合并车道 / Merge lane
    SPLIT = 10                             # 分叉车道 / Split lane
```

### 4.7 车道方向枚举 / Lane Direction Enum

```python
class LaneDirection(IntEnum):
    """车道方向枚举 / Lane Direction Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    FORWARD = 1                            # 前进 / Forward
    BACKWARD = 2                           # 后退 / Backward
    BIDIRECTIONAL = 3                      # 双向 / Bidirectional
```

### 4.8 边界类型枚举 / Boundary Type Enum

```python
class BoundaryType(IntEnum):
    """边界类型枚举 / Boundary Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    LINE = 1                               # 线型边界 / Line boundary
    CURB = 2                               # 路缘石 / Curb
    GUARDRAIL = 3                          # 护栏 / Guardrail
    WALL = 4                               # 墙壁 / Wall
    VIRTUAL = 5                            # 虚拟边界 / Virtual boundary
```

### 4.9 边界线形状枚举 / Boundary Line Shape Enum

```python
class BoundaryLineShape(IntEnum):
    """边界线形状枚举 / Boundary Line Shape Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    SOLID = 1                              # 实线 / Solid
    DASHED = 2                             # 虚线 / Dashed
    DOUBLE_SOLID = 3                       # 双实线 / Double solid
    DOUBLE_DASHED = 4                      # 双虚线 / Double dashed
    SOLID_DASHED = 5                       # 实虚组合 / Solid-dashed combination
    DOTTED = 6                             # 点线 / Dotted
    LEFT_SOLID_RIGHT_DASHED = 7            # 左实右虚 / Left solid right dashed
    LEFT_DASHED_RIGHT_SOLID = 8            # 左虚右实 / Left dashed right solid
```

---

## 5. 交通信号灯结构 / Traffic Light Structures

### 5.1 交通信号灯 / Traffic Light

```python
@dataclass
class TrafficLight:
    """交通信号灯 / Traffic Light"""
    traffic_light_id: int                  # 信号灯唯一标识符 / Unique traffic light identifier
    lanelet_id: int                        # 对应的高精地图lanelet ID / Corresponding HD map lanelet ID
    position: Point3D                      # 信号灯位置（局部坐标系）/ Traffic light position (local frame)
    current_state: TrafficLightState       # 当前状态 / Current state
    predicted_states: List[TrafficLightState]  # 预测状态序列 / Predicted state sequence
    distance_to_stop_line: float           # 到停止线的距离（米）/ Distance to stop line (meters)
    associated_stop_line_id: int           # 关联的停止线ID / Associated stop line ID
    light_type: TrafficLightType           # 信号灯类型 / Traffic light type
    confidence: float                      # 检测置信度 / Detection confidence
```

### 5.2 交通信号灯状态 / Traffic Light State

```python
@dataclass
class TrafficLightState:
    """交通信号灯状态 / Traffic Light State"""
    timestamp: datetime                    # 状态时间戳 / State timestamp
    color: TrafficLightColor               # 灯光颜色 / Light color
    shape: TrafficLightShape               # 灯光形状 / Light shape
    status: TrafficLightStatus             # 灯光状态 / Light status
    remaining_time: float                   # 剩余时间（秒）/ Remaining time (seconds)
```

### 5.3 交通信号灯颜色枚举 / Traffic Light Color Enum

```python
class TrafficLightColor(IntEnum):
    """交通信号灯颜色枚举 / Traffic Light Color Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    RED = 1                                # 红色 / Red
    YELLOW = 2                             # 黄色 / Yellow
    GREEN = 3                              # 绿色 / Green
    RED_YELLOW = 4                         # 红黄组合 / Red-yellow combination
    FLASHING_RED = 5                       # 闪烁红 / Flashing red
    FLASHING_YELLOW = 6                    # 闪烁黄 / Flashing yellow
    FLASHING_GREEN = 7                     # 闪烁绿 / Flashing green
```

### 5.4 交通信号灯形状枚举 / Traffic Light Shape Enum

```python
class TrafficLightShape(IntEnum):
    """交通信号灯形状枚举 / Traffic Light Shape Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    CIRCLE = 1                             # 圆形 / Circle
    LEFT_ARROW = 2                         # 左箭头 / Left arrow
    RIGHT_ARROW = 3                        # 右箭头 / Right arrow
    UP_ARROW = 4                          # 上箭头 / Up arrow
    DOWN_ARROW = 5                         # 下箭头 / Down arrow
    UP_LEFT_ARROW = 6                      # 左上箭头 / Up-left arrow
    UP_RIGHT_ARROW = 7                     # 右上箭头 / Up-right arrow
    CROSS = 8                              # 叉号 / Cross
```

### 5.5 交通信号灯状态枚举 / Traffic Light Status Enum

```python
class TrafficLightStatus(IntEnum):
    """交通信号灯状态枚举 / Traffic Light Status Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    SOLID_OFF = 1                          # 常灭 / Solid off
    SOLID_ON = 2                           # 常亮 / Solid on
    FLASHING = 3                           # 闪烁 / Flashing
```

### 5.6 交通信号灯类型枚举 / Traffic Light Type Enum

```python
class TrafficLightType(IntEnum):
    """交通信号灯类型枚举 / Traffic Light Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    VEHICLE = 1                            # 机动车信号灯 / Vehicle traffic light
    PEDESTRIAN = 2                         # 行人信号灯 / Pedestrian traffic light
    BICYCLE = 3                            # 自行车信号灯 / Bicycle traffic light
    LANE_CONTROL = 4                       # 车道控制信号灯 / Lane control light
```

---

## 6. 交通标志结构 / Traffic Sign Structures

### 6.1 交通标志 / Traffic Sign

```python
@dataclass
class TrafficSign:
    """交通标志 / Traffic Sign"""
    traffic_sign_id: int                   # 标志唯一标识符 / Unique traffic sign identifier
    lanelet_id: int                        # 对应的高精地图lanelet ID / Corresponding HD map lanelet ID
    position: Point3D                      # 标志位置（局部坐标系）/ Sign position (local frame)
    sign_type: TrafficSignType             # 标志类型 / Sign type
    distance_to_sign: float                # 到标志的距离（米）/ Distance to sign (meters)
    value: float                            # 标志数值（如限速值）/ Sign value (e.g., speed limit)
    text_content: str                       # 标志文本内容 / Sign text content
    confidence: float                      # 检测置信度 / Detection confidence
    is_valid: bool                          # 标志是否有效 / Whether sign is valid
    valid_until: Optional[datetime] = None  # 有效期截止时间 / Validity expiration time
```

### 6.2 交通标志类型枚举 / Traffic Sign Type Enum

```python
class TrafficSignType(IntEnum):
    """交通标志类型枚举 / Traffic Sign Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown

    # 限速类 / Speed Limit Signs
    SPEED_LIMIT = 1                        # 限速 / Speed limit
    SPEED_LIMIT_END = 2                    # 解除限速 / End of speed limit
    MINIMUM_SPEED = 3                      # 最低限速 / Minimum speed
    SPEED_LIMIT_ZONE_START = 4             # 限速区开始 / Speed limit zone start
    SPEED_LIMIT_ZONE_END = 5               # 限速区结束 / Speed limit zone end

    # 禁止类 / Prohibition Signs
    NO_ENTRY = 10                          # 禁止驶入 / No entry
    NO_PARKING = 11                        # 禁止停车 / No parking
    NO_STOPPING = 12                       # 禁止停车（临时）/ No stopping
    NO_OVERTAKING = 13                     # 禁止超车 / No overtaking
    NO_LEFT_TURN = 14                      # 禁止左转 / No left turn
    NO_RIGHT_TURN = 15                     # 禁止右转 / No right turn
    NO_U_TURN = 16                         # 禁止掉头 / No U-turn
    NO_HONKING = 17                        # 禁止鸣笛 / No honking

    # 警告类 / Warning Signs
    CURVE_LEFT = 20                        # 左急弯 / Left curve
    CURVE_RIGHT = 21                       # 右急弯 / Right curve
    WINDING_ROAD = 22                      # 连续弯路 / Winding road
    STEEP_ASCENT = 23                      # 陡坡上坡 / Steep ascent
    STEEP_DESCENT = 24                     # 陡坡下坡 / Steep descent
    NARROW_ROAD = 25                       # 窄路 / Narrow road
    ROAD_WORKS = 26                        # 施工 / Road works
    TRAFFIC_SIGNAL_AHEAD = 27               # 前方信号灯 / Traffic signal ahead
    PEDESTRIAN_CROSSING = 28                # 人行横道 / Pedestrian crossing
    SCHOOL_ZONE = 29                       # 学校区域 / School zone
    SLIPPERY_ROAD = 30                     # 湿滑路面 / Slippery road
    FALLING_ROCKS = 31                     # 落石 / Falling rocks
    ANIMAL_CROSSING = 32                   # 动物出没 / Animal crossing

    # 指示类 / Mandatory Signs
    STRAIGHT_ONLY = 40                     # 直行 / Straight only
    LEFT_TURN_ONLY = 41                    # 左转 / Left turn only
    RIGHT_TURN_ONLY = 42                   # 右转 / Right turn only
    STRAIGHT_OR_LEFT = 43                  # 直行或左转 / Straight or left
    STRAIGHT_OR_RIGHT = 44                 # 直行或右转 / Straight or right
    KEEP_LEFT = 45                         # 靠左行驶 / Keep left
    KEEP_RIGHT = 46                        # 靠右行驶 / Keep right
    ROUNDABOUT = 47                        # 环岛 / Roundabout
    PASS_EITHER_SIDE = 48                  # 两侧通行 / Pass either side

    # 信息类 / Information Signs
    HIGHWAY_ENTRANCE = 50                  # 高速公路入口 / Highway entrance
    HIGHWAY_EXIT = 51                      # 高速公路出口 / Highway exit
    SERVICE_AREA = 52                      # 服务区 / Service area
    PARKING_AREA = 53                      # 停车场 / Parking area
    HOSPITAL = 54                         # 医院 / Hospital
    GAS_STATION = 55                       # 加油站 / Gas station
    REST_AREA = 56                        # 休息区 / Rest area

    # 临时标志 / Temporary Signs
    TEMPORARY_SPEED_LIMIT = 60             # 临时限速 / Temporary speed limit
    TEMPORARY_NO_OVERTAKING = 61           # 临时禁止超车 / Temporary no overtaking
    TEMPORARY_LANE_CLOSURE = 62            # 临时车道封闭 / Temporary lane closure
    TEMPORARY_ROAD_CLOSURE = 63            # 临时道路封闭 / Temporary road closure
```

---

## 7. 道路标线结构 / Road Marking Structures

### 7.1 道路标线 / Road Marking

```python
@dataclass
class RoadMarking:
    """道路标线 / Road Marking"""
    road_marking_id: int                   # 标线唯一标识符 / Unique road marking identifier
    lanelet_id: int                        # 对应的高精地图lanelet ID / Corresponding HD map lanelet ID
    marking_type: RoadMarkingType          # 标线类型 / Marking type
    marking_points: List[Point3D]          # 标线点集 / Marking point set
    marking_width: float                   # 标线宽度（米）/ Marking width (meters)
    marking_color: RoadMarkingColor        # 标线颜色 / Marking color
    confidence: float                      # 检测置信度 / Detection confidence
```

### 7.2 道路标线类型枚举 / Road Marking Type Enum

```python
class RoadMarkingType(IntEnum):
    """道路标线类型枚举 / Road Marking Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    STOP_LINE = 1                          # 停止线 / Stop line
    CROSSWALK = 2                          # 人行横道 / Crosswalk
    ZEBRA_CROSSING = 3                     # 斑马线 / Zebra crossing
    ARROW_LEFT = 4                         # 左转箭头 / Left turn arrow
    ARROW_RIGHT = 5                        # 右转箭头 / Right turn arrow
    ARROW_STRAIGHT = 6                     # 直行箭头 / Straight arrow
    ARROW_U_TURN = 7                       # 掉头箭头 / U-turn arrow
    YIELD_LINE = 8                         # 让行线 / Yield line
    TEXT_MARKING = 9                       # 文字标线 / Text marking
    DIAGONAL_MARKING = 10                  # 斜线标线 / Diagonal marking
    CHECKERBOARD = 11                      # 棋盘格标线 / Checkerboard marking
```

### 7.3 道路标线颜色枚举 / Road Marking Color Enum

```python
class RoadMarkingColor(IntEnum):
    """道路标线颜色枚举 / Road Marking Color Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    WHITE = 1                              # 白色 / White
    YELLOW = 2                             # 黄色 / Yellow
    BLUE = 3                               # 蓝色 / Blue
    RED = 4                                # 红色 / Red
```

---

## 8. 人行横道结构 / Crosswalk Structures

### 8.1 人行横道 / Crosswalk

```python
@dataclass
class Crosswalk:
    """人行横道 / Crosswalk"""
    crosswalk_id: int                      # 人行横道唯一标识符 / Unique crosswalk identifier
    lanelet_id: int                        # 对应的高精地图lanelet ID / Corresponding HD map lanelet ID
    polygon_points: List[Point3D]          # 人行横道多边形顶点 / Crosswalk polygon vertices
    crosswalk_width: float                 # 人行横道宽度（米）/ Crosswalk width (meters)
    crosswalk_length: float                # 人行横道长度（米）/ Crosswalk length (meters)
    has_traffic_light: bool                # 是否有信号灯控制 / Whether controlled by traffic light
    associated_traffic_light_id: int       # 关联的信号灯ID / Associated traffic light ID
    has_pedestrian_island: bool            # 是否有安全岛 / Whether has pedestrian island
    confidence: float                      # 检测置信度 / Detection confidence
```

---

## 9. 停止线结构 / Stop Line Structures

### 9.1 停止线 / Stop Line

```python
@dataclass
class StopLine:
    """停止线 / Stop Line"""
    stop_line_id: int                      # 停止线唯一标识符 / Unique stop line identifier
    lanelet_id: int                        # 对应的高精地图lanelet ID / Corresponding HD map lanelet ID
    line_points: List[Point3D]             # 停止线点集 / Stop line point set
    stop_line_type: StopLineType           # 停止线类型 / Stop line type
    associated_traffic_light_id: int       # 关联的信号灯ID / Associated traffic light ID
    associated_sign_id: int                # 关联的标志ID / Associated sign ID
    distance_to_stop_line: float           # 到停止线的距离（米）/ Distance to stop line (meters)
    is_mandatory: bool                     # 是否强制停止 / Whether mandatory stop
    confidence: float                      # 检测置信度 / Detection confidence
```

### 9.2 停止线类型枚举 / Stop Line Type Enum

```python
class StopLineType(IntEnum):
    """停止线类型枚举 / Stop Line Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    TRAFFIC_LIGHT = 1                      # 信号灯停止线 / Traffic light stop line
    STOP_SIGN = 2                          # 停车标志停止线 / Stop sign stop line
    CROSSWALK = 3                          # 人行横道停止线 / Crosswalk stop line
    RAILWAY = 4                            # 铁路道口停止线 / Railway crossing stop line
    YIELD = 5                              # 让行线 / Yield line
    CHECKPOINT = 6                         # 检查站停止线 / Checkpoint stop line
```

---

## 10. 交叉口结构 / Intersection Structures

### 10.1 交叉口 / Intersection

```python
@dataclass
class Intersection:
    """交叉口 / Intersection"""
    intersection_id: int                   # 交叉口唯一标识符 / Unique intersection identifier
    lanelet_id: int                        # 对应的高精地图lanelet ID / Corresponding HD map lanelet ID
    intersection_type: IntersectionType   # 交叉口类型 / Intersection type
    polygon_points: List[Point3D]          # 交叉口多边形顶点 / Intersection polygon vertices
    incoming_lane_ids: List[int]           # 进入车道ID列表 / Incoming lane ID list
    outgoing_lane_ids: List[int]           # 离开车道ID列表 / Outgoing lane ID list
    traffic_light_ids: List[int]           # 信号灯ID列表 / Traffic light ID list
    stop_line_ids: List[int]              # 停止线ID列表 / Stop line ID list
    crosswalk_ids: List[int]              # 人行横道ID列表 / Crosswalk ID list
    has_traffic_light: bool                # 是否有信号灯控制 / Whether controlled by traffic light
    has_stop_sign: bool                    # 是否有停车标志 / Whether has stop sign
    is_roundabout: bool                    # 是否为环岛 / Whether is roundabout
    confidence: float                      # 检测置信度 / Detection confidence
```

### 10.2 交叉口类型枚举 / Intersection Type Enum

```python
class IntersectionType(IntEnum):
    """交叉口类型枚举 / Intersection Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    FOUR_WAY = 1                           # 十字路口 / Four-way intersection
    THREE_WAY = 2                          # 三岔路口 / Three-way intersection
    T_JUNCTION = 3                         # T型路口 / T-junction
    Y_JUNCTION = 4                         # Y型路口 / Y-junction
    ROUNDABOUT = 5                         # 环岛 / Roundabout
    MULTI_LEG = 6                          # 多岔路口 / Multi-leg intersection
```

---

## 11. 基础数据类型 / Basic Data Types

### 11.1 三维点 / Point3D

```python
@dataclass
class Point3D:
    """三维点 / Point3D"""
    x: float                               # X坐标（米）/ X coordinate (meters)
    y: float                               # Y坐标（米）/ Y coordinate (meters)
    z: float                               # Z坐标（米）/ Z coordinate (meters)
```

### 11.2 二维点 / Point2D

```python
@dataclass
class Point2D:
    """二维点 / Point2D"""
    x: float                               # X坐标（米）/ X coordinate (meters)
    y: float                               # Y坐标（米）/ Y coordinate (meters)
```

### 11.3 位姿 / Pose

```python
@dataclass
class Pose:
    """位姿 / Pose"""
    position: Point3D                      # 位置 / Position
    heading: float                          # 航向角（弧度）/ Heading angle (radians)
    pitch: float                           # 俯仰角（弧度）/ Pitch angle (radians)
    roll: float                            # 横滚角（弧度）/ Roll angle (radians)
```

---

## 12. 高精地图元素分类参考 / HD Map Element Classification Reference

基于Lanelet2高精地图标准，以下元素分类被映射到局部地图数据结构中：

Based on the Lanelet2 HD map standard, the following element classifications are mapped to the local map data structure:

### 12.1 Lanelet2元素映射 / Lanelet2 Element Mapping

| Lanelet2元素 / Lanelet2 Element | 局部地图结构 / Local Map Structure | 说明 / Description |
|--------------------------------|-----------------------------------|-------------------|
| lanelet                        | Lane                              | 车道 / Lane |
| regulatory_element             | TrafficSign, TrafficLight         | 交规元素 / Traffic rule elements |
| traffic_light                  | TrafficLight                      | 信号灯 / Traffic light |
| speed_limit                    | TrafficSign (SPEED_LIMIT)        | 限速 / Speed limit |
| stop_line                      | StopLine                          | 停止线 / Stop line |
| crosswalk                      | Crosswalk                         | 人行横道 / Crosswalk |
| road_marking                   | RoadMarking                       | 道路标线 / Road marking |
| intersection                   | Intersection                      | 交叉口 / Intersection |

### 12.2 交规元素分类 / Traffic Rule Element Classification

#### 12.2.1 速度控制类 / Speed Control Class
- 限速标志 (Speed Limit Sign)
- 最低限速标志 (Minimum Speed Sign)
- 限速区 (Speed Limit Zone)
- 临时限速标志 (Temporary Speed Limit Sign)

#### 12.2.2 通行控制类 / Access Control Class
- 禁止驶入标志 (No Entry Sign)
- 禁止通行标志 (No Through Sign)
- 单行道标志 (One Way Sign)
- 专用车道标志 (Exclusive Lane Sign)

#### 12.2.3 转向控制类 / Turn Control Class
- 禁止左转标志 (No Left Turn Sign)
- 禁止右转标志 (No Right Turn Sign)
- 禁止掉头标志 (No U-Turn Sign)
- 指定转向标志 (Mandatory Turn Sign)

#### 12.2.4 停车控制类 / Stop Control Class
- 停车标志 (Stop Sign)
- 让行标志 (Yield Sign)
- 禁止停车标志 (No Parking Sign)
- 禁止停车（临时）标志 (No Stopping Sign)

#### 12.2.5 超车控制类 / Overtaking Control Class
- 禁止超车标志 (No Overtaking Sign)
- 临时禁止超车标志 (Temporary No Overtaking Sign)

#### 12.2.6 警告类 / Warning Class
- 施工标志 (Construction Sign)
- 弯道警告标志 (Curve Warning Sign)
- 陡坡警告标志 (Steep Slope Warning Sign)
- 窄路警告标志 (Narrow Road Warning Sign)
- 学校区域标志 (School Zone Sign)
- 人行横道警告标志 (Pedestrian Crossing Warning Sign)

#### 12.2.7 信号控制类 / Signal Control Class
- 交通信号灯 (Traffic Light)
- 车道控制信号灯 (Lane Control Light)
- 行人信号灯 (Pedestrian Signal Light)

---

## 13. 数据更新策略 / Data Update Strategy

### 13.1 更新频率 / Update Frequency

| 数据类型 / Data Type | 更新频率 / Update Frequency | 说明 / Description |
|---------------------|---------------------------|-------------------|
| 地图元数据 / Map Metadata | 10 Hz | 自车状态实时更新 / Ego vehicle state real-time update |
| 车道信息 / Lane Information | 1 Hz | 车道几何变化较慢 / Lane geometry changes slowly |
| 交通信号灯 / Traffic Light | 10 Hz | 信号灯状态实时更新 / Traffic light state real-time update |
| 交通标志 / Traffic Sign | 1 Hz | 标志位置固定，状态变化慢 / Sign position fixed, state changes slowly |
| 道路标线 / Road Marking | 1 Hz | 标线位置固定 / Marking position fixed |
| 人行横道 / Crosswalk | 1 Hz | 人行横道位置固定 / Crosswalk position fixed |
| 停止线 / Stop Line | 1 Hz | 停止线位置固定 / Stop line position fixed |
| 交叉口 / Intersection | 1 Hz | 交叉口位置固定 / Intersection position fixed |

### 13.2 数据有效性 / Data Validity

- 所有坐标数据必须经过坐标系转换，确保在自车局部坐标系下
- 所有距离数据必须为正值
- 所有置信度数据范围应在 [0.0, 1.0] 之间
- 所有时间戳应使用系统统一时间基准

---

## 14. 扩展性考虑 / Extensibility Considerations

### 14.1 预留字段 / Reserved Fields

为未来扩展，各主要数据结构预留以下字段：

For future extensions, following reserved fields are provided in major data structures:

```python
# 在各主要数据类中添加 / Add to major data classes
reserved_bytes: bytes = b''              # 预留字节 / Reserved bytes
reserved_string: str = ''                # 预留字符串 / Reserved string
```

### 14.2 自定义数据 / Custom Data

```python
@dataclass
class CustomData:
    """自定义数据 / Custom Data"""
    key: str                              # 数据键 / Data key
    value: str                            # 数据值 / Data value
```

可在主要数据结构中添加：

Can be added to major data structures:

```python
custom_data: List[CustomData] = field(default_factory=list)  # 自定义数据列表 / Custom data list
```

---

## 15. 示例数据 / Example Data

### 15.1 简单场景示例 / Simple Scene Example

```python
"""
场景描述：自车在直行车道上，前方有信号灯控制的交叉口
Scene description: Ego vehicle on straight lane, approaching signal-controlled intersection
"""

# 创建局部地图 / Create local map
local_map = LocalMap(
    header=Header(
        timestamp=datetime(2026, 2, 3, 7, 51, 0),
        frame_id="ego_vehicle_local",
        sequence_number=0
    ),
    metadata=LocalMapMetadata(
        map_range_x=200.0,
        map_range_y=100.0,
        map_range_z=10.0,
        ego_vehicle_x=0.0,
        ego_vehicle_y=0.0,
        ego_vehicle_heading=0.0,
        ego_vehicle_velocity=15.0,
        timestamp=datetime(2026, 2, 3, 7, 51, 0)
    ),
    lanes=[
        Lane(
            lane_id=1,
            lanelet_id=1001,
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=0.0, y=0.0, z=0.0),
                Point3D(x=10.0, y=0.0, z=0.0),
                Point3D(x=20.0, y=0.0, z=0.0),
                Point3D(x=30.0, y=0.0, z=0.0),
                Point3D(x=40.0, y=0.0, z=0.0),
            ],
            left_boundary_segment_indices=[
                LaneBoundarySegment(
                    segment_id=1,
                    boundary_type=BoundaryType.LINE,
                    boundary_line_shape=BoundaryLineShape.SOLID,
                    boundary_color=BoundaryColor.WHITE,
                    boundary_thickness=0.15,
                    is_virtual=False,
                    boundary_point_indices=[0, 1, 2, 3, 4],
                )
            ],
            right_boundary_segment_indices=[
                LaneBoundarySegment(
                    segment_id=2,
                    boundary_type=BoundaryType.LINE,
                    boundary_line_shape=BoundaryLineShape.DASHED,
                    boundary_color=BoundaryColor.WHITE,
                    boundary_thickness=0.15,
                    is_virtual=False,
                    boundary_point_indices=[5, 6, 7, 8, 9],
                )
            ],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=1,
                    speed_limit=16.67,  # 60 km/h
                    min_speed_limit=0.0,
                    start_position=Point3D(x=0.0, y=0.0, z=0.0),
                    end_position=Point3D(x=40.0, y=0.0, z=0.0),
                    speed_limit_type=SpeedLimitType.REGULAR
                )
            ],
            associated_traffic_light_ids=[1],
            associated_stop_line_ids=[1],
            associated_intersection_id=1
        )
    ],
    boundary_segments=[
        LaneBoundarySegment(
            segment_id=1,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.WHITE,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=0.0, y=1.75, z=0.0),
                Point3D(x=10.0, y=1.75, z=0.0),
                Point3D(x=20.0, y=1.75, z=0.0),
                Point3D(x=30.0, y=1.75, z=0.0),
                Point3D(x=40.0, y=1.75, z=0.0),
            ]
        ),
        LaneBoundarySegment(
            segment_id=2,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.DASHED,
            boundary_color=BoundaryColor.WHITE,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=0.0, y=-1.75, z=0.0),
                Point3D(x=10.0, y=-1.75, z=0.0),
                Point3D(x=20.0, y=-1.75, z=0.0),
                Point3D(x=30.0, y=-1.75, z=0.0),
                Point3D(x=40.0, y=-1.75, z=0.0),
            ]
        ),
    ],
    traffic_lights=[
        TrafficLight(
            traffic_light_id=1,
            lanelet_id=2001,
            position=Point3D(x=50.0, y=-5.0, z=5.0),
            current_state=TrafficLightState(
                timestamp=datetime(2026, 2, 3, 7, 51, 0),
                color=TrafficLightColor.RED,
                shape=TrafficLightShape.CIRCLE,
                status=TrafficLightStatus.SOLID_ON,
                remaining_time=25.0
            ),
            predicted_states=[],
            distance_to_stop_line=45.0,
            associated_stop_line_id=1,
            light_type=TrafficLightType.VEHICLE,
            confidence=0.95
        )
    ],
    stop_lines=[
        StopLine(
            stop_line_id=1,
            lanelet_id=3001,
            line_points=[
                Point3D(x=45.0, y=-1.75, z=0.0),
                Point3D(x=45.0, y=1.75, z=0.0)
            ],
            stop_line_type=StopLineType.TRAFFIC_LIGHT,
            associated_traffic_light_id=1,
            associated_sign_id=0,
            distance_to_stop_line=45.0,
            is_mandatory=True,
            confidence=0.98
        )
    ],
    intersections=[
        Intersection(
            intersection_id=1,
            lanelet_id=4001,
            intersection_type=IntersectionType.FOUR_WAY,
            polygon_points=[
                Point3D(x=45.0, y=-10.0, z=0.0),
                Point3D(x=55.0, y=-10.0, z=0.0),
                Point3D(x=55.0, y=10.0, z=0.0),
                Point3D(x=45.0, y=10.0, z=0.0)
            ],
            incoming_lane_ids=[1, 2, 3, 4],
            outgoing_lane_ids=[5, 6, 7, 8],
            traffic_light_ids=[1],
            stop_line_ids=[1],
            crosswalk_ids=[],
            has_traffic_light=True,
            has_stop_sign=False,
            is_roundabout=False,
            confidence=0.99
        )
    ],
    traffic_signs=[],
    road_markings=[],
    crosswalks=[]
)
```

### 15.2 边界点共享示例 / Boundary Point Sharing Example

```python
"""
场景描述：两条相邻车道共享边界分段
Scene description: Two adjacent lanes share boundary segments

说明：边界分段存储在LocalMap.boundary_segments中，相邻车道通过索引引用相同的边界分段来实现共享
Note: Boundary segments are stored in LocalMap.boundary_segments, adjacent lanes share by referencing same boundary segments via indices
"""

# 创建共享的边界分段 / Create shared boundary segment
shared_boundary_segment = LaneBoundarySegment(
    segment_id=1,
    boundary_type=BoundaryType.LINE,
    boundary_line_shape=BoundaryLineShape.DASHED,
    boundary_color=BoundaryColor.WHITE,
    boundary_thickness=0.15,
    is_virtual=False,
    boundary_points=[
        Point3D(x=0.0, y=1.75, z=0.0),
        Point3D(x=10.0, y=1.75, z=0.0),
        Point3D(x=20.0, y=1.75, z=0.0),
        Point3D(x=30.0, y=1.75, z=0.0),
        Point3D(x=40.0, y=1.75, z=0.0),
    ]
)

# 车道1的右边界使用共享边界分段 / Lane 1's right boundary uses shared boundary segment
lane1 = Lane(
    lane_id=1,
    lanelet_id=1001,
    lane_type=LaneType.DRIVING,
    lane_direction=LaneDirection.FORWARD,
    centerline_points=[
        Point3D(x=0.0, y=0.0, z=0.0),
        Point3D(x=10.0, y=0.0, z=0.0),
        Point3D(x=20.0, y=0.0, z=0.0),
        Point3D(x=30.0, y=0.0, z=0.0),
        Point3D(x=40.0, y=0.0, z=0.0),
    ],
    right_boundary_segment_indices=[0],  # 引用共享的边界分段segment_id=1 / Reference shared boundary segment segment_id=1
    left_boundary_segment_indices=[],
    speed_limits=[],
    associated_traffic_light_ids=[],
    associated_traffic_sign_ids=[],
    associated_stop_line_ids=[],
    associated_crosswalk_ids=[],
    associated_road_marking_ids=[],
    associated_intersection_id=None,
    left_adjacent_lane_id=None,
    right_adjacent_lane_id=2,
    predecessor_lane_ids=[],
    successor_lane_ids=[]
)

# 车道2的左边界使用相同的共享边界分段 / Lane 2's left boundary uses same shared boundary segment
lane2 = Lane(
    lane_id=2,
    lanelet_id=1002,
    lane_type=LaneType.DRIVING,
    lane_direction=LaneDirection.FORWARD,
    centerline_points=[
        Point3D(x=0.0, y=0.0, z=0.0),
        Point3D(x=10.0, y=0.0, z=0.0),
        Point3D(x=20.0, y=0.0, z=0.0),
        Point3D(x=30.0, y=0.0, z=0.0),
        Point3D(x=40.0, y=0.0, z=0.0),
    ],
    left_boundary_segment_indices=[0],  # 引用相同的共享边界分段segment_id=0 / Reference same shared boundary segment segment_id=0
    right_boundary_segment_indices=[],
    speed_limits=[],
    associated_traffic_light_ids=[],
    associated_traffic_sign_ids=[],
    associated_stop_line_ids=[],
    associated_crosswalk_ids=[],
    associated_road_marking_ids=[],
    associated_intersection_id=None,
    left_adjacent_lane_id=1,
    right_adjacent_lane_id=None,
    predecessor_lane_ids=[],
    successor_lane_ids=[]
)
```

**设计说明 / Design Note:**

在这个设计中：
- 边界分段存储在LocalMap.boundary_segments中
- 车道通过索引引用边界分段（left_boundary_segment_indices、right_boundary_segment_indices）
- LaneBoundarySegment是自包含的，包含完整的边界点数据（boundary_points）
- 相邻车道可以引用同一个LaneBoundarySegment的索引来实现共享

In this design:
- Boundary segments are stored in LocalMap.boundary_segments
- Lanes reference boundary segments via indices (left_boundary_segment_indices, right_boundary_segment_indices)
- LaneBoundarySegment is self-contained, contains complete boundary point data (boundary_points)
- Adjacent lanes can share by referencing to same LaneBoundarySegment index
### 15.3 限速分段示例 / Speed Limit Segmentation Example

```python
"""
场景描述：车道限速随位置变化
Scene description: Lane speed limit changes with position
"""

# 车道限速分段 / Lane speed limit segments
speed_limits = [
    SpeedLimitSegment(
        segment_id=1,
        speed_limit=16.67,  # 60 km/h
        min_speed_limit=0.0,
        start_position=Point3D(x=0.0, y=0.0, z=0.0),
        end_position=Point3D(x=100.0, y=0.0, z=0.0),
        speed_limit_type=SpeedLimitType.REGULAR
    ),
    SpeedLimitSegment(
        segment_id=2,
        speed_limit=13.89,  # 50 km/h (学校区域)
        min_speed_limit=0.0,
        start_position=Point3D(x=100.0, y=0.0, z=0.0),
        end_position=Point3D(x=200.0, y=0.0, z=0.0),
        associated_sign_id=101,
        speed_limit_type=SpeedLimitType.SCHOOL_ZONE
    ),
    SpeedLimitSegment(
        segment_id=3,
        speed_limit=16.67,  # 60 km/h (恢复)
        min_speed_limit=0.0,
        start_position=Point3D(x=200.0, y=0.0, z=0.0),
        end_position=Point3D(x=300.0, y=0.0, z=0.0),
        speed_limit_type=SpeedLimitType.REGULAR
    ),
    SpeedLimitSegment(
        segment_id=4,
        speed_limit=8.33,   # 30 km/h (施工区域)
        min_speed_limit=0.0,
        start_position=Point3D(x=300.0, y=0.0, z=0.0),
        end_position=Point3D(x=400.0, y=0.0, z=0.0),
        associated_sign_id=102,
        speed_limit_type=SpeedLimitType.CONSTRUCTION_ZONE
    ),
]
```

---

## 16. 附录 / Appendix

### 16.1 术语表 / Glossary

| 术语 / Term | 中文 / Chinese | 说明 / Description |
|-------------|---------------|-------------------|
| Ego Vehicle | 自车 | 当前控制的车辆 / Currently controlled vehicle |
| Local Coordinate System | 局部坐标系 | 以自车为原点的坐标系 / Coordinate system with ego vehicle as origin |
| Lanelet | 车道单元 | Lanelet2标准中的最小车道单元 / Minimum lane unit in Lanelet2 standard |
| HD Map | 高精地图 | 高精度地图 / High-definition map |
| Stop Line | 停止线 | 要求车辆停止的标线 / Marking requiring vehicles to stop |
| Yield Line | 让行线 | 要求车辆让行的标线 / Marking requiring vehicles to yield |
| Boundary Segment Sharing | 边界分段共享 | 不同车道通过索引引用相同的LaneBoundarySegment来实现共享，LaneBoundarySegment包含完整的边界点数据 / Different lanes share boundary segments via index references, LaneBoundarySegment contains complete boundary point data |
| Speed Limit Segmentation | 限速分段 | 车道限速随位置变化的分段定义 / Segmented definition of lane speed limit changes with position |

### 16.2 参考标准 / Reference Standards

- Lanelet2: https://github.com/fzi-forschungszentrum-informatik/Lanelet2
- OpenDRIVE: https://www.asam.net/standards/opendrive/
- ISO 19133: Geographic information — Location based services — Tracking and navigation
- Apollo HD Map: https://github.com/ApolloAuto/apollo/tree/master/modules/map/hdmap
- Python dataclass: https://docs.python.org/3/library/dataclasses.html

### 16.3 C++兼容性说明 / C++ Compatibility Note

本数据结构使用Python dataclass定义，但可以方便地转换为C++结构体。以下是转换指南：

This data structure is defined using Python dataclass, but can be easily converted to C++ structs. Here is the conversion guide:

```cpp
// C++结构体示例 / C++ struct example
struct Lane {
    int64_t lane_id;
    int64_t lanelet_id;
    LaneType lane_type;
    LaneDirection lane_direction;
    std::vector<Point3D> centerline_points;
    std::vector<int64_t> left_boundary_segment_indices;
    std::vector<int64_t> right_boundary_segment_indices;
    std::vector<SpeedLimitSegment> speed_limits;
    std::vector<int64_t> associated_traffic_light_ids;
    std::vector<int64_t> associated_traffic_sign_ids;
    std::vector<int64_t> associated_stop_line_ids;
    std::vector<int64_t> associated_crosswalk_ids;
    std::vector<int64_t> associated_road_marking_ids;
    std::optional<int64_t> associated_intersection_id;
    std::optional<int64_t> left_adjacent_lane_id;
    std::optional<int64_t> right_adjacent_lane_id;
    std::vector<int64_t> predecessor_lane_ids;
    std::vector<int64_t> successor_lane_ids;
};

struct LaneBoundarySegment {
    int64_t segment_id;
    BoundaryType boundary_type;
    BoundaryLineShape boundary_line_shape;
    BoundaryColor boundary_color;
    double boundary_thickness;
    bool is_virtual;
    std::vector<Point3D> boundary_points;  // Boundary point list / 边界点列表
};

struct LocalMap {
    Header header;
    LocalMapMetadata metadata;
    std::vector<Lane> lanes;
    std::vector<TrafficLight> traffic_lights;
    std::vector<TrafficSign> traffic_signs;
    std::vector<RoadMarking> road_markings;
    std::vector<Crosswalk> crosswalks;
    std::vector<StopLine> stop_lines;
    std::vector<Intersection> intersections;
    std::vector<LaneBoundarySegment> boundary_segments;  // Boundary segment pool / 边界分段池子
};

struct SpeedLimitSegment {
    int64_t segment_id;
    double speed_limit;
    double min_speed_limit = 0.0;
    Point3D start_position;  // Absolute coordinates / 绝对坐标
    Point3D end_position;    // Absolute coordinates / 绝对坐标
    std::optional<int64_t> associated_sign_id;
    SpeedLimitType speed_limit_type;
};
```

---

## 17. 版本历史 / Version History

| 版本 / Version | 日期 / Date | 作者 / Author | 变更说明 / Change Description |
|---------------|------------|--------------|-----------------------------|
| 1.0 | 2026-02-03 | Roo Code | 初始版本 / Initial version |
| 2.0 | 2026-02-03 | Roo Code | 改用Python dataclass定义，增加边界点共享、限速分段、关联元素ID列表 / Changed to Python dataclass definition, added boundary point sharing, speed limit segmentation, associated element ID lists |
| 2.1 | 2026-02-03 | Roo Code | 移除lane_width，边界点存储在LaneBoundarySegment中，相邻车道细化为左右，车道连接细化为前继后继，边界样式改名为BoundaryLineShape并增加左实右虚/左虚右实类型 / Removed lane_width, boundary points stored in LaneBoundarySegment, adjacent lanes refined to left/right, lane connections refined to predecessor/successor, boundary style renamed to BoundaryLineShape and added left-solid-right-dashed/left-dashed-right-solid types |
| 2.2 | 2026-02-03 | Roo Code | 移除LaneBoundarySegment的start_s/end_s字段，SpeedLimitSegment改用绝对坐标（start_position/end_position）替代s坐标，增加min_speed_limit字段，更新SpeedLimitType注释说明REGULAR为道路默认限速、TEMPORARY为临时限速牌产生的限速 / Removed start_s/end_s from LaneBoundarySegment, SpeedLimitSegment changed to use absolute coordinates (start_position/end_position) instead of s-coordinate, added min_speed_limit field, updated SpeedLimitType comments to clarify REGULAR as default road speed limit and TEMPORARY as speed limit from temporary speed limit sign |
| 2.3 | 2026-02-03 | Roo Code | 添加边界分段池子（boundary_segments）到LocalMap，Lane通过索引引用边界分段（left_boundary_segment_indices、right_boundary_segment_indices），LaneBoundarySegment是自包含的，包含完整的边界点数据（boundary_points），支持相邻车道共享边界分段，更新共享机制说明和示例 / Added boundary segment pool (boundary_segments) to LocalMap, lanes reference boundary segments via indices (left_boundary_segment_indices, right_boundary_segment_indices), LaneBoundarySegment is self-contained, contains complete boundary point data (boundary_points), supports adjacent lanes sharing boundary segments, updated sharing mechanism description and examples |

---

**文档结束 / End of Document**
