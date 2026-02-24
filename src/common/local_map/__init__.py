"""
LocalMap模块
LocalMap Module

提供统一的局部地图数据结构和API接口
Provides unified local map data structures and API interfaces
"""

from .local_map_data import (
    # 基础数据类型 / Basic Data Types
    Point3D, Point2D, Pose,
    
    # 枚举类型 / Enum Types
    LaneType, LaneDirection, BoundaryType, BoundaryLineShape, BoundaryColor,
    SpeedLimitType, TrafficLightColor, TrafficLightShape, TrafficLightStatus, TrafficLightType,
    TrafficSignType, RoadMarkingType, RoadMarkingColor, StopLineType, IntersectionType,
    
    # 地图元数据 / Map Metadata
    Header, LocalMapMetadata,
    
    # 车道相关结构 / Lane-Related Structures
    Lane, LaneBoundarySegment, SpeedLimitSegment,
    
    # 交通信号灯结构 / Traffic Light Structures
    TrafficLight, TrafficLightState,
    
    # 交通标志结构 / Traffic Sign Structures
    TrafficSign,
    
    # 道路标线结构 / Road Marking Structures
    RoadMarking,
    
    # 人行横道结构 / Crosswalk Structures
    Crosswalk,
    
    # 停止线结构 / Stop Line Structures
    StopLine,
    
    # 交叉口结构 / Intersection Structures
    Intersection,
    
    # 自定义数据 / Custom Data
    CustomData,
    
    # 局部地图主结构 / Local Map Main Structure
    LocalMap,
    
    # 高精地图转换器接口 / HD Map Converter Interface
    HDMapConverter,
    
    # 工具函数 / Utility Functions
    create_empty_local_map, get_lane_by_id, get_boundary_segment_by_id,
    get_traffic_light_by_id, get_traffic_sign_by_id, get_lanes_in_range,
    validate_local_map
)

from .local_map_api import LocalMapAPI

__all__ = [
    # 基础数据类型 / Basic Data Types
    'Point3D', 'Point2D', 'Pose',
    
    # 枚举类型 / Enum Types
    'LaneType', 'LaneDirection', 'BoundaryType', 'BoundaryLineShape', 'BoundaryColor',
    'SpeedLimitType', 'TrafficLightColor', 'TrafficLightShape', 'TrafficLightStatus', 'TrafficLightType',
    'TrafficSignType', 'RoadMarkingType', 'RoadMarkingColor', 'StopLineType', 'IntersectionType',
    
    # 地图元数据 / Map Metadata
    'Header', 'LocalMapMetadata',
    
    # 车道相关结构 / Lane-Related Structures
    'Lane', 'LaneBoundarySegment', 'SpeedLimitSegment',
    
    # 交通信号灯结构 / Traffic Light Structures
    'TrafficLight', 'TrafficLightState',
    
    # 交通标志结构 / Traffic Sign Structures
    'TrafficSign',
    
    # 道路标线结构 / Road Marking Structures
    'RoadMarking',
    
    # 人行横道结构 / Crosswalk Structures
    'Crosswalk',
    
    # 停止线结构 / Stop Line Structures
    'StopLine',
    
    # 交叉口结构 / Intersection Structures
    'Intersection',
    
    # 自定义数据 / Custom Data
    'CustomData',
    
    # 局部地图主结构 / Local Map Main Structure
    'LocalMap',
    
    # 高精地图转换器接口 / HD Map Converter Interface
    'HDMapConverter',
    
    # 工具函数 / Utility Functions
    'create_empty_local_map', 'get_lane_by_id', 'get_boundary_segment_by_id',
    'get_traffic_light_by_id', 'get_traffic_sign_by_id', 'get_lanes_in_range',
    'validate_local_map',
    
    # API接口 / API Interface
    'LocalMapAPI'
]