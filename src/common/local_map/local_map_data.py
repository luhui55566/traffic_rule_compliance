"""
局部地图数据结构定义
Local Map Data Structure Definition

基于设计文档 src/common/local_map_data_introduction.md 实现
Implementation based on design document src/common/local_map_data_introduction.md
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple
from datetime import datetime
from enum import IntEnum
from abc import ABC, abstractmethod


# ============================================================================
# 基础数据类型 / Basic Data Types
# ============================================================================

@dataclass
class Point3D:
    """三维点 / Point3D"""
    x: float                               # X坐标（米）/ X coordinate (meters)
    y: float                               # Y坐标（米）/ Y coordinate (meters)
    z: float                               # Z坐标（米）/ Z coordinate (meters)


@dataclass
class Point2D:
    """二维点 / Point2D"""
    x: float                               # X坐标（米）/ X coordinate (meters)
    y: float                               # Y坐标（米）/ Y coordinate (meters)


@dataclass
class Pose:
    """位姿 / Pose"""
    position: Point3D                      # 位置 / Position
    heading: float                          # 航向角（弧度）/ Heading angle (radians)
    pitch: float = 0.0                     # 俯仰角（弧度）/ Pitch angle (radians)
    roll: float = 0.0                      # 横滚角（弧度）/ Roll angle (radians)


# ============================================================================
# 枚举类型 / Enum Types
# ============================================================================

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


class LaneDirection(IntEnum):
    """车道方向枚举 / Lane Direction Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    FORWARD = 1                            # 前进 / Forward
    BACKWARD = 2                           # 后退 / Backward
    BIDIRECTIONAL = 3                      # 双向 / Bidirectional


class BoundaryType(IntEnum):
    """边界类型枚举 / Boundary Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    LINE = 1                               # 线型边界 / Line boundary
    CURB = 2                               # 路缘石 / Curb
    GUARDRAIL = 3                          # 护栏 / Guardrail
    WALL = 4                               # 墙壁 / Wall
    VIRTUAL = 5                            # 虚拟边界 / Virtual boundary


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


class BoundaryColor(IntEnum):
    """边界颜色枚举 / Boundary Color Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    WHITE = 1                              # 白色 / White
    YELLOW = 2                             # 黄色 / Yellow
    BLUE = 3                               # 蓝色 / Blue
    RED = 4                                # 红色 / Red


class SpeedLimitType(IntEnum):
    """限速类型枚举 / Speed Limit Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    REGULAR = 1                            # 常规限速：道路默认限速 / Regular speed limit: default road speed limit
    TEMPORARY = 2                          # 临时限速：临时限速牌产生的限速 / Temporary speed limit: speed limit from temporary speed limit sign
    SCHOOL_ZONE = 3                        # 学校区域限速 / School zone speed limit
    CONSTRUCTION_ZONE = 4                  # 施工区域限速 / Construction zone speed limit
    WEATHER_CONDITION = 5                  # 天气条件限速 / Weather condition speed limit


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


class TrafficLightStatus(IntEnum):
    """交通信号灯状态枚举 / Traffic Light Status Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    SOLID_OFF = 1                          # 常灭 / Solid off
    SOLID_ON = 2                           # 常亮 / Solid on
    FLASHING = 3                           # 闪烁 / Flashing


class TrafficLightType(IntEnum):
    """交通信号灯类型枚举 / Traffic Light Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    VEHICLE = 1                            # 机动车信号灯 / Vehicle traffic light
    PEDESTRIAN = 2                         # 行人信号灯 / Pedestrian traffic light
    BICYCLE = 3                            # 自行车信号灯 / Bicycle traffic light
    LANE_CONTROL = 4                       # 车道控制信号灯 / Lane control light


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


class RoadMarkingColor(IntEnum):
    """道路标线颜色枚举 / Road Marking Color Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    WHITE = 1                              # 白色 / White
    YELLOW = 2                             # 黄色 / Yellow
    BLUE = 3                               # 蓝色 / Blue
    RED = 4                                # 红色 / Red


class StopLineType(IntEnum):
    """停止线类型枚举 / Stop Line Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    TRAFFIC_LIGHT = 1                      # 信号灯停止线 / Traffic light stop line
    STOP_SIGN = 2                          # 停车标志停止线 / Stop sign stop line
    CROSSWALK = 3                          # 人行横道停止线 / Crosswalk stop line
    RAILWAY = 4                            # 铁路道口停止线 / Railway crossing stop line
    YIELD = 5                              # 让行线 / Yield line
    CHECKPOINT = 6                         # 检查站停止线 / Checkpoint stop line


class IntersectionType(IntEnum):
    """交叉口类型枚举 / Intersection Type Enum"""
    UNKNOWN = 0                            # 未知 / Unknown
    FOUR_WAY = 1                           # 十字路口 / Four-way intersection
    THREE_WAY = 2                          # 三岔路口 / Three-way intersection
    T_JUNCTION = 3                         # T型路口 / T-junction
    Y_JUNCTION = 4                         # Y型路口 / Y-junction
    ROUNDABOUT = 5                         # 环岛 / Roundabout
    MULTI_LEG = 6                          # 多岔路口 / Multi-leg intersection


# ============================================================================
# 地图元数据 / Map Metadata
# ============================================================================

@dataclass
class Header:
    """消息头 / Message Header"""
    timestamp: datetime                    # 时间戳 / Timestamp
    frame_id: str                          # 坐标系ID / Coordinate frame ID
    sequence_number: int = 0               # 序列号 / Sequence number


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


# ============================================================================
# 车道相关结构 / Lane-Related Structures
# ============================================================================

@dataclass
class LaneBoundarySegment:
    """车道边界分段 / Lane Boundary Segment
    
    说明：车道边界需要分段定义，因为边界类型（实线/虚线）可能沿车道变化
    Description: Lane boundaries need to be defined in segments because boundary types (solid/dashed) may change along the lane
    
    注意：boundary_points是边界线的中心点
    Note: boundary_points are center points of boundary line
    
    共享机制 / Sharing Mechanism:
    - 相邻车道可以引用同一个LaneBoundarySegment来实现边界共享
    - Adjacent lanes can reference same LaneBoundarySegment to achieve boundary sharing
    - Lanelet2格式：相邻lanelet共享同一个linestring，转换时创建共享的LaneBoundarySegment
    - XODR格式：同一个road内的相邻lane可以共享边界，转换时按需创建共享的LaneBoundarySegment
    - LaneBoundarySegment是自包含的，包含完整的边界点数据
    - LaneBoundarySegment is self-contained, contains complete boundary point data
    """
    segment_id: int                        # 分段唯一标识符 / Unique segment identifier
    #boundary_type: BoundaryType            # 边界类型 / Boundary type
    #boundary_line_shape: BoundaryLineShape  # 边界线形状 / Boundary line shape
    #boundary_color: BoundaryColor           # 边界颜色 / Boundary color
    #boundary_thickness: float              # 边界线宽度（米）/ Boundary line thickness (meters)
    #is_virtual: bool                       # 是否虚拟边界 / Whether virtual boundary
    
    # 边界点集（边界线中心点）/ Boundary point set (center points of boundary line)
    boundary_points: List[Point3D]         # 边界点列表 / Boundary point list
    
    # 分段边界支持 / Segmented Boundary Support:
    # - 使用绝对坐标数组来支持多个边界子段
    # - Use absolute coordinate arrays to support multiple boundary sub-segments
    boundary_type_segments: List[Tuple[Point3D, BoundaryType]] = field(default_factory=list)  # [(起点坐标, 边界类型), ...] / [(start point, boundary type), ...]
    boundary_line_shape_segments: List[Tuple[Point3D, BoundaryLineShape]] = field(default_factory=list)  # [(起点坐标, 边界线形状), ...] / [(start point, boundary line shape), ...]
    boundary_color_segments: List[Tuple[Point3D, BoundaryColor]] = field(default_factory=list)  # [(起点坐标, 边界颜色), ...] / [(start point, boundary color), ...]
    boundary_thickness_segments: List[Tuple[Point3D, float]] = field(default_factory=list)  # [(起点坐标, 边界线宽度), ...] / [(start point, boundary thickness), ...]
    is_virtual_segments: List[Tuple[Point3D, bool]] = field(default_factory=list)  # [(起点坐标, 是否虚拟边界), ...] / [(start point, is virtual), ...]


@dataclass
class SpeedLimitSegment:
    """限速分段 / Speed Limit Segment
    
    说明：每条车道的限速可能随位置变化，需要分段定义
    Description: Speed limit for each lane may change with position, needs to be defined in segments
    """
    segment_id: int                        # 分段唯一标识符 / Unique segment identifier
    speed_limit: float                     # 限速值（米/秒）/ Speed limit (m/s)
    min_speed_limit: float = 0.0          # 最低限速值（米/秒），默认为0表示无最低限速 / Minimum speed limit (m/s), default 0 means no minimum speed limit
    
    # 关联的交通标志ID / Associated traffic sign ID
    associated_sign_id: Optional[int] = None  # 产生此限速的交通标志ID / Traffic sign ID that created this speed limit
    
    # 限速类型 / Speed limit type
    speed_limit_type: SpeedLimitType = SpeedLimitType.REGULAR  # 限速类型 / Speed limit type
    
    # 分段范围（绝对坐标）/ Segment range (absolute coordinates)
    start_position: Point3D = field(default_factory=lambda: Point3D(x=0.0, y=0.0, z=0.0))  # 分段起始位置（绝对坐标）/ Segment start position (absolute coordinates)
    end_position: Point3D = field(default_factory=lambda: Point3D(x=0.0, y=0.0, z=0.0))    # 分段结束位置（绝对坐标）/ Segment end position (absolute coordinates)


@dataclass
class Lane:
    """车道 / Lane
    
    约束条件 / Constraints:
    - centerline_points 为空时，left_boundary_segment_indices 和 right_boundary_segment_indices 必须非空
      When centerline_points is empty, left_boundary_segment_indices and right_boundary_segment_indices must be non-empty
    """
    lane_id: int                           # 车道唯一标识符 / Unique lane identifier (globally unique)
    lane_type: LaneType                    # 车道类型 / Lane type
    lane_direction: LaneDirection          # 车道方向 / Lane direction
    
    # 原始ID字段 / Original ID fields (for traceability)
    original_lane_id: Optional[int] = None    # 原始lane ID / Original lane ID
    original_road_id: Optional[int] = None    # 原始road ID / Original road ID
    original_junction_id: Optional[int] = None # 原始junction ID / Original junction ID
    
    # 地图源信息 / Map source information
    map_source_type: str = ""              # 地图源类型 / Map source type ("OSM", "XODR", etc.)
    map_source_id: str = ""               # 地图源标识 / Map source identifier (e.g., "Town10HD")
    
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
    speed_limits: List[SpeedLimitSegment] = field(default_factory=list) # 限速分段列表 / Speed limit segment list
    
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
    # 注意：展平设计，所有lane ID都是全局唯一的，连接关系直接展开到lane级别
    # Note: Flattened design, all lane IDs are globally unique, connections are expanded to lane level
    # 不需要层级查询（Road→Lane或Junction→Road→Lane），直接使用lane ID即可
    # No hierarchical queries needed (Road→Lane or Junction→Road→Lane), use lane IDs directly
    predecessor_lane_ids: List[int] = field(default_factory=list)  # 前继车道ID列表 / Predecessor lane ID list (只包含lane ID，不包含junction ID / Only contains lane IDs, no junction IDs)
    successor_lane_ids: List[int] = field(default_factory=list)      # 后继车道ID列表 / Successor lane ID list (只包含lane ID，不包含junction ID / Only contains lane IDs, no junction IDs)
    
    # XODR元数据 / XODR metadata
    # road_id和junction_id为全局唯一ID，通过hash(map_source_id, original_id)生成
    # road_id and junction_id are globally unique IDs, generated via hash(map_source_id, original_id)
    road_id: Optional[int] = None          # 全局唯一道路ID / Globally unique road ID (用于快速查询某road包含的所有lane / For quick query of all lanes in a road)
    junction_id: Optional[int] = None       # 全局唯一交叉口ID / Globally unique junction ID (用于快速查询某junction连接的所有lane / For quick query of all lanes connected to a junction)
    is_junction_lane: bool = False          # 是否为交叉口内部车道 / Whether is junction internal lane


# ============================================================================
# 交通信号灯结构 / Traffic Light Structures
# ============================================================================

@dataclass
class TrafficLightState:
    """交通信号灯状态 / Traffic Light State"""
    timestamp: datetime                    # 状态时间戳 / State timestamp
    color: TrafficLightColor               # 灯光颜色 / Light color
    shape: TrafficLightShape               # 灯光形状 / Light shape
    status: TrafficLightStatus             # 灯光状态 / Light status
    remaining_time: float = 0.0            # 剩余时间（秒）/ Remaining time (seconds)


@dataclass
class TrafficLight:
    """交通信号灯 / Traffic Light"""
    traffic_light_id: int                  # 信号灯唯一标识符 / Unique traffic light identifier
    position: Point3D                      # 信号灯位置（局部坐标系）/ Traffic light position (local frame)
    current_state: TrafficLightState       # 当前状态 / Current state
    associated_lane_id: int = 0            # 关联的车道ID / Associated lane ID (use lane_id, not lanelet_id)
    predicted_states: List[TrafficLightState] = field(default_factory=list)  # 预测状态序列 / Predicted state sequence
    distance_to_stop_line: float = 0.0     # 到停止线的距离（米）/ Distance to stop line (meters)
    associated_stop_line_id: int = 0       # 关联的停止线ID / Associated stop line ID
    light_type: TrafficLightType = TrafficLightType.UNKNOWN  # 信号灯类型 / Traffic light type
    confidence: float = 0.0                 # 检测置信度 / Detection confidence


# ============================================================================
# 交通标志结构 / Traffic Sign Structures
# ============================================================================

@dataclass
class TrafficSign:
    """交通标志 / Traffic Sign"""
    traffic_sign_id: int                   # 标志唯一标识符 / Unique traffic sign identifier
    position: Point3D                      # 标志位置（局部坐标系）/ Sign position (local frame)
    sign_type: TrafficSignType             # 标志类型 / Sign type
    associated_lane_id: int = 0            # 关联的车道ID / Associated lane ID (use lane_id, not lanelet_id)
    distance_to_sign: float = 0.0          # 到标志的距离（米）/ Distance to sign (meters)
    value: float = 0.0                      # 标志数值（如限速值）/ Sign value (e.g., speed limit)
    text_content: str = ""                  # 标志文本内容 / Sign text content
    confidence: float = 0.0                 # 检测置信度 / Detection confidence
    is_valid: bool = True                   # 标志是否有效 / Whether sign is valid
    valid_until: Optional[datetime] = None  # 有效期截止时间 / Validity expiration time


# ============================================================================
# 道路标线结构 / Road Marking Structures
# ============================================================================

@dataclass
class RoadMarking:
    """道路标线 / Road Marking"""
    road_marking_id: int                   # 标线唯一标识符 / Unique road marking identifier
    marking_type: RoadMarkingType          # 标线类型 / Marking type
    marking_points: List[Point3D] = field(default_factory=list)  # 标线点集 / Marking point set
    marking_width: float = 0.0             # 标线宽度（米）/ Marking width (meters)
    marking_color: RoadMarkingColor = RoadMarkingColor.UNKNOWN  # 标线颜色 / Marking color
    associated_lane_id: int = 0            # 关联的车道ID / Associated lane ID (use lane_id, not lanelet_id)
    confidence: float = 0.0                 # 检测置信度 / Detection confidence


# ============================================================================
# 人行横道结构 / Crosswalk Structures
# ============================================================================

@dataclass
class Crosswalk:
    """人行横道 / Crosswalk"""
    crosswalk_id: int                      # 人行横道唯一标识符 / Unique crosswalk identifier
    polygon_points: List[Point3D] = field(default_factory=list)  # 人行横道多边形顶点 / Crosswalk polygon vertices
    crosswalk_width: float = 0.0           # 人行横道宽度（米）/ Crosswalk width (meters)
    crosswalk_length: float = 0.0          # 人行横道长度（米）/ Crosswalk length (meters)
    has_traffic_light: bool = False        # 是否有信号灯控制 / Whether controlled by traffic light
    associated_traffic_light_id: int = 0   # 关联的信号灯ID / Associated traffic light ID
    associated_lane_id: int = 0            # 关联的车道ID / Associated lane ID (use lane_id, not lanelet_id)
    has_pedestrian_island: bool = False     # 是否有安全岛 / Whether has pedestrian island
    confidence: float = 0.0                 # 检测置信度 / Detection confidence


# ============================================================================
# 停止线结构 / Stop Line Structures
# ============================================================================

@dataclass
class StopLine:
    """停止线 / Stop Line"""
    stop_line_id: int                      # 停止线唯一标识符 / Unique stop line identifier
    line_points: List[Point3D] = field(default_factory=list)  # 停止线点集 / Stop line point set
    stop_line_type: StopLineType = StopLineType.UNKNOWN  # 停止线类型 / Stop line type
    associated_lane_id: int = 0            # 关联的车道ID / Associated lane ID (use lane_id, not lanelet_id)
    associated_traffic_light_id: int = 0   # 关联的信号灯ID / Associated traffic light ID
    associated_sign_id: int = 0            # 关联的标志ID / Associated sign ID
    distance_to_stop_line: float = 0.0     # 到停止线的距离（米）/ Distance to stop line (meters)
    is_mandatory: bool = True               # 是否强制停止 / Whether mandatory stop
    confidence: float = 0.0                 # 检测置信度 / Detection confidence


# ============================================================================
# 道路结构 / Road Structures
# ============================================================================

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


# ============================================================================
# 交叉口结构 / Intersection Structures (XODR Extended)
# ============================================================================

@dataclass
class Junction:
    """交叉口 / Junction (XODR Extended)
    
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


@dataclass
class Intersection:
    """交叉口 / Intersection"""
    intersection_id: int                   # 交叉口唯一标识符 / Unique intersection identifier
    intersection_type: IntersectionType = IntersectionType.UNKNOWN  # 交叉口类型 / Intersection type
    polygon_points: List[Point3D] = field(default_factory=list)  # 交叉口多边形顶点 / Intersection polygon vertices
    incoming_lane_ids: List[int] = field(default_factory=list)  # 进入车道ID列表 / Incoming lane ID list
    outgoing_lane_ids: List[int] = field(default_factory=list)  # 离开车道ID列表 / Outgoing lane ID list
    traffic_light_ids: List[int] = field(default_factory=list)  # 信号灯ID列表 / Traffic light ID list
    stop_line_ids: List[int] = field(default_factory=list)  # 停止线ID列表 / Stop line ID list
    crosswalk_ids: List[int] = field(default_factory=list)  # 人行横道ID列表 / Crosswalk ID list
    has_traffic_light: bool = False        # 是否有信号灯控制 / Whether controlled by traffic light
    has_stop_sign: bool = False            # 是否有停车标志 / Whether has stop sign
    is_roundabout: bool = False            # 是否为环岛 / Whether is roundabout
    associated_lane_id: int = 0            # 关联的车道ID / Associated lane ID (use lane_id, not lanelet_id)
    confidence: float = 0.0                 # 检测置信度 / Detection confidence


# ============================================================================
# 自定义数据 / Custom Data
# ============================================================================

@dataclass
class CustomData:
    """自定义数据 / Custom Data"""
    key: str                              # 数据键 / Data key
    value: str                            # 数据值 / Data value


# ============================================================================
# 局部地图主结构 / Local Map Main Structure
# ============================================================================

@dataclass
class LocalMap:
    """局部地图主结构 / Local Map Main Structure"""
    header: Header                          # 时间戳和坐标系信息 / Timestamp and coordinate frame info
    metadata: LocalMapMetadata              # 地图元数据 / Map metadata
    lanes: List[Lane] = field(default_factory=list)                       # 车道信息 / Lane information
    traffic_lights: List[TrafficLight] = field(default_factory=list)      # 红绿灯信息 / Traffic light information
    traffic_signs: List[TrafficSign] = field(default_factory=list)        # 交通标志信息 / Traffic sign information
    road_markings: List[RoadMarking] = field(default_factory=list)        # 道路标线信息 / Road marking information
    crosswalks: List[Crosswalk] = field(default_factory=list)             # 人行横道信息 / Crosswalk information
    stop_lines: List[StopLine] = field(default_factory=list)              # 停止线信息 / Stop line information
    intersections: List[Intersection] = field(default_factory=list)      # 交叉口信息 / Intersection information
    
    # 边界分段池子 / Boundary segment pool
    # 用于存储所有边界分段，支持相邻车道共享边界分段
    # Stores all boundary segments, supports boundary segment sharing between adjacent lanes
    boundary_segments: List[LaneBoundarySegment] = field(default_factory=list)
    
    # XODR扩展字段 / XODR extension fields
    roads: List[Road] = field(default_factory=list)      # 道路信息列表 / Road information list (用于快速查询某road包含的所有lane / For quick query of all lanes in a road)
    junctions: List[Junction] = field(default_factory=list)  # 交叉口信息列表 / Junction information list (用于快速查询某junction连接的所有road / For quick query of all roads connected to a junction)
    
    # 扩展字段 / Extension fields
    custom_data: List[CustomData] = field(default_factory=list)  # 自定义数据列表 / Custom data list
    reserved_bytes: bytes = b''              # 预留字节 / Reserved bytes
    reserved_string: str = ''                # 预留字符串 / Reserved string


# ============================================================================
# 高精地图转换器接口 / HD Map Converter Interface
# ============================================================================

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


# ============================================================================
# 工具函数 / Utility Functions
# ============================================================================

def create_empty_local_map(ego_pose: Pose, map_range: float = 200.0) -> LocalMap:
    """
    创建空的局部地图
    Create empty local map
    
    Args:
        ego_pose: 自车位姿 / Ego vehicle pose
        map_range: 地图范围（米）/ Map range (meters)
    
    Returns:
        LocalMap: 空的局部地图对象 / Empty local map object
    """
    now = datetime.now()
    
    header = Header(
        timestamp=now,
        frame_id="ego_vehicle_local",
        sequence_number=0
    )
    
    metadata = LocalMapMetadata(
        map_range_x=map_range,
        map_range_y=map_range,
        map_range_z=10.0,
        ego_vehicle_x=ego_pose.position.x,
        ego_vehicle_y=ego_pose.position.y,
        ego_vehicle_heading=ego_pose.heading,
        ego_vehicle_velocity=0.0,
        timestamp=now
    )
    
    return LocalMap(
        header=header,
        metadata=metadata
    )


def get_lane_by_id(local_map: LocalMap, lane_id: int) -> Optional[Lane]:
    """
    根据车道ID获取车道对象
    Get lane object by lane ID
    
    Args:
        local_map: 局部地图对象 / Local map object
        lane_id: 车道ID / Lane ID
    
    Returns:
        Optional[Lane]: 车道对象，如果不存在则返回None / Lane object, None if not found
    """
    for lane in local_map.lanes:
        if lane.lane_id == lane_id:
            return lane
    return None


def get_boundary_segment_by_id(local_map: LocalMap, segment_id: int) -> Optional[LaneBoundarySegment]:
    """
    根据边界分段ID获取边界分段对象
    Get boundary segment object by segment ID
    
    Args:
        local_map: 局部地图对象 / Local map object
        segment_id: 边界分段ID / Boundary segment ID
    
    Returns:
        Optional[LaneBoundarySegment]: 边界分段对象，如果不存在则返回None / Boundary segment object, None if not found
    """
    for segment in local_map.boundary_segments:
        if segment.segment_id == segment_id:
            return segment
    return None


def get_traffic_light_by_id(local_map: LocalMap, traffic_light_id: int) -> Optional[TrafficLight]:
    """
    根据信号灯ID获取信号灯对象
    Get traffic light object by traffic light ID
    
    Args:
        local_map: 局部地图对象 / Local map object
        traffic_light_id: 信号灯ID / Traffic light ID
    
    Returns:
        Optional[TrafficLight]: 信号灯对象，如果不存在则返回None / Traffic light object, None if not found
    """
    for traffic_light in local_map.traffic_lights:
        if traffic_light.traffic_light_id == traffic_light_id:
            return traffic_light
    return None


def get_traffic_sign_by_id(local_map: LocalMap, traffic_sign_id: int) -> Optional[TrafficSign]:
    """
    根据交通标志ID获取交通标志对象
    Get traffic sign object by traffic sign ID
    
    Args:
        local_map: 局部地图对象 / Local map object
        traffic_sign_id: 交通标志ID / Traffic sign ID
    
    Returns:
        Optional[TrafficSign]: 交通标志对象，如果不存在则返回None / Traffic sign object, None if not found
    """
    for traffic_sign in local_map.traffic_signs:
        if traffic_sign.traffic_sign_id == traffic_sign_id:
            return traffic_sign
    return None


def get_lanes_in_range(local_map: LocalMap, x_range: tuple, y_range: tuple) -> List[Lane]:
    """
    获取指定范围内的车道
    Get lanes within specified range
    
    Args:
        local_map: 局部地图对象 / Local map object
        x_range: X轴范围 (min_x, max_x) / X-axis range (min_x, max_x)
        y_range: Y轴范围 (min_y, max_y) / Y-axis range (min_y, max_y)
    
    Returns:
        List[Lane]: 指定范围内的车道列表 / List of lanes within specified range
    """
    result = []
    min_x, max_x = x_range
    min_y, max_y = y_range
    
    for lane in local_map.lanes:
        # 检查车道中心线点是否在范围内
        for point in lane.centerline_points:
            if min_x <= point.x <= max_x and min_y <= point.y <= max_y:
                result.append(lane)
                break
    
    return result


def validate_local_map(local_map: LocalMap) -> List[str]:
    """
    验证局部地图数据的有效性
    Validate local map data
    
    Args:
        local_map: 局部地图对象 / Local map object
    
    Returns:
        List[str]: 验证错误列表，空列表表示验证通过 / List of validation errors, empty list means validation passed
    """
    errors = []
    
    # 检查边界分段引用是否有效
    for lane in local_map.lanes:
        for segment_idx in lane.left_boundary_segment_indices:
            if segment_idx < 0 or segment_idx >= len(local_map.boundary_segments):
                errors.append(f"Lane {lane.lane_id} references invalid left boundary segment index {segment_idx}")
        
        for segment_idx in lane.right_boundary_segment_indices:
            if segment_idx < 0 or segment_idx >= len(local_map.boundary_segments):
                errors.append(f"Lane {lane.lane_id} references invalid right boundary segment index {segment_idx}")
    
    # 检查关联元素ID是否有效
    for lane in local_map.lanes:
        for light_id in lane.associated_traffic_light_ids:
            if get_traffic_light_by_id(local_map, light_id) is None:
                errors.append(f"Lane {lane.lane_id} references invalid traffic light ID {light_id}")
        
        for sign_id in lane.associated_traffic_sign_ids:
            if get_traffic_sign_by_id(local_map, sign_id) is None:
                errors.append(f"Lane {lane.lane_id} references invalid traffic sign ID {sign_id}")
    
    return errors