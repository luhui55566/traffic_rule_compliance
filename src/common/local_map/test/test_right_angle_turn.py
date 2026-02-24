"""
测试直角弯道地图
Test Right Angle Turn Map

测试包含直角弯道的简单地图结构，包含直道和弯道部分
Tests simple map structure with right angle turn, including straight and curved sections
"""

import sys
import os
from datetime import datetime
import math

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 导入模块
from common.local_map.local_map_data import (
    LocalMap, Lane, LaneBoundarySegment, SpeedLimitSegment,
    TrafficLight, TrafficLightState, TrafficSign,
    Point3D, Pose, LaneType, LaneDirection,
    TrafficLightColor, TrafficSignType, BoundaryType, BoundaryLineShape,
    BoundaryColor, Header, LocalMapMetadata, create_empty_local_map
)
from common.local_map.local_map_api import LocalMapAPI


def create_right_angle_turn_map() -> LocalMap:
    """
    创建直角弯道地图
    Create right angle turn map
    
    Returns:
        LocalMap: 直角弯道地图 / Right angle turn map
    """
    # Ego position at start of the road
    ego_pose = Pose(
        position=Point3D(x=-25.0, y=0.0, z=0.0),
        heading=0.0,
        pitch=0.0,
        roll=0.0
    )
    
    # Create empty local map with 200m radius
    local_map = create_empty_local_map(ego_pose, 200.0)
    
    # ==================== 创建边界分段 / Create Boundary Segments ====================
    # 双向四车道：2个方向 x 2车道
    # 车道宽度统一为3.5米 / Lane width is 3.5m
    # 道路中心线半径为10米 / Road centerline radius is 10m
    # 总共13段边界：4条外边界 + 3条内分隔线 + 3条中心分隔线 + 3条最内侧边界
    # Total 13 boundary segments: 4 outer boundaries + 3 inner dividers + 3 center dividers + 3 innermost boundaries
    
    boundary_segments = []
    
    # ==================== 弯道参数 / Curve Parameters ====================
    # 道路中心线转弯半径 / Road centerline turn radius
    R = 10.0  # 米 / meters
    # 车道宽度 / Lane width
    W = 3.5  # 米 / meters
    
    # ==================== 正向车道1（最左侧）Forward Lane 1 (Leftmost) ====================
    # 直道左边界 - y = -R - 1.5W = -10 - 5.25 = -15.25
    boundary_segments.append(LaneBoundarySegment(
        segment_id=1,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=-15.25, z=0.0),
            Point3D(x=-10.0, y=-15.25, z=0.0),
        ]
    ))
    
    # 弯道左边界 - 半径 R + 1.5W = 10 + 5.25 = 15.25米
    curve_points_f1_left = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 15.25 * math.sin(rad)
        y = 15.25 * (1 - math.cos(rad))
        curve_points_f1_left.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=2,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=curve_points_f1_left
    ))
    
    # 出口直道左边界 - x = R + 1.5W = 10 + 5.25 = 15.25
    boundary_segments.append(LaneBoundarySegment(
        segment_id=3,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=15.25, y=10.0, z=0.0),
            Point3D(x=15.25, y=50.0, z=0.0),
        ]
    ))
    
    # ==================== 正向车道2（中间左侧）Forward Lane 2 (Middle Left) ====================
    # 直道左边界（即车道1的右边界）- y = -R - 0.5W = -10 - 1.75 = -11.75
    boundary_segments.append(LaneBoundarySegment(
        segment_id=4,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=-11.75, z=0.0),
            Point3D(x=-10.0, y=-11.75, z=0.0),
        ]
    ))
    
    # 弯道左边界 - 半径 R + 0.5W = 10 + 1.75 = 11.75米
    curve_points_f2_left = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 11.75 * math.sin(rad)
        y = 11.75 * (1 - math.cos(rad))
        curve_points_f2_left.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=5,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=curve_points_f2_left
    ))
    
    # 出口直道左边界 - x = R + 0.5W = 10 + 1.75 = 11.75
    boundary_segments.append(LaneBoundarySegment(
        segment_id=6,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=11.75, y=10.0, z=0.0),
            Point3D(x=11.75, y=50.0, z=0.0),
        ]
    ))
    
    # ==================== 道路中心分隔线（双向）Road Center Divider ====================
    # 直道中心分隔线 - y = 0
    boundary_segments.append(LaneBoundarySegment(
        segment_id=7,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DOUBLE_SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.20,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=0.0, z=0.0),
            Point3D(x=-10.0, y=0.0, z=0.0),
        ]
    ))
    
    # 弯道中心分隔线 - 半径 R = 10米
    curve_points_center = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 10.0 * math.sin(rad)
        y = 10.0 * (1 - math.cos(rad))
        curve_points_center.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=8,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DOUBLE_SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.20,
        is_virtual=False,
        boundary_points=curve_points_center
    ))
    
    # 出口直道中心分隔线 - x = 0
    boundary_segments.append(LaneBoundarySegment(
        segment_id=9,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DOUBLE_SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.20,
        is_virtual=False,
        boundary_points=[
            Point3D(x=0.0, y=10.0, z=0.0),
            Point3D(x=0.0, y=50.0, z=0.0),
        ]
    ))
    
    # ==================== 反向车道1（中间右侧）Backward Lane 1 (Middle Right) ====================
    # 直道右边界（即反向车道2的左边界）- y = R + 0.5W = 10 + 1.75 = 11.75
    boundary_segments.append(LaneBoundarySegment(
        segment_id=10,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=11.75, z=0.0),
            Point3D(x=-10.0, y=11.75, z=0.0),
        ]
    ))
    
    # 弯道右边界 - 半径 R - 0.5W = 10 - 1.75 = 8.25米
    curve_points_b1_right = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 8.25 * math.sin(rad)
        y = 8.25 * (1 - math.cos(rad))
        curve_points_b1_right.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=11,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=curve_points_b1_right
    ))
    
    # 出口直道右边界 - x = R - 0.5W = 10 - 1.75 = 8.25
    boundary_segments.append(LaneBoundarySegment(
        segment_id=12,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-8.25, y=10.0, z=0.0),
            Point3D(x=-8.25, y=50.0, z=0.0),
        ]
    ))
    
    # ==================== 反向车道2（最右侧）Backward Lane 2 (Rightmost) ====================
    # 直道右边界 - y = R + 1.5W = 10 + 5.25 = 15.25
    boundary_segments.append(LaneBoundarySegment(
        segment_id=13,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=15.25, z=0.0),
            Point3D(x=-10.0, y=15.25, z=0.0),
        ]
    ))
    
    # 弯道右边界 - 半径 R - 1.5W = 10 - 5.25 = 4.75米
    curve_points_b2_right = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 4.75 * math.sin(rad)
        y = 4.75 * (1 - math.cos(rad))
        curve_points_b2_right.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=14,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=curve_points_b2_right
    ))
    
    # 出口直道右边界 - x = R - 1.5W = 10 - 5.25 = 4.75
    boundary_segments.append(LaneBoundarySegment(
        segment_id=15,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-4.75, y=10.0, z=0.0),
            Point3D(x=-4.75, y=50.0, z=0.0),
        ]
    ))
    
    local_map.boundary_segments.extend(boundary_segments)
    
    # ==================== 创建车道 / Create Lanes ====================
    # 双向四车道：2个方向 x 2车道 = 4车道
    # 每个车道分为3段：直道、弯道、出口
    # Bidirectional 4 lanes: 2 directions x 2 lanes = 4 lanes
    # Each lane has 3 segments: straight, curve, exit
    
    lanes = []
    
    # ==================== 正向车道1（最左侧）Forward Lane 1 (Leftmost) ====================
    # 直道部分 - 中心线在 y = -R - W = -10 - 3.5 = -13.5
    f1_straight_centerline = [
        Point3D(x=-50.0, y=-13.5, z=0.0),
        Point3D(x=-40.0, y=-13.5, z=0.0),
        Point3D(x=-30.0, y=-13.5, z=0.0),
        Point3D(x=-20.0, y=-13.5, z=0.0),
        Point3D(x=-10.0, y=-13.5, z=0.0),
    ]
    
    lane_f1_straight = Lane(
        lane_id=1,
        original_lane_id=1,
        original_road_id=100,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f1_straight_centerline,
        left_boundary_segment_indices=[0],  # segment_id=1
        right_boundary_segment_indices=[3],  # segment_id=4
        speed_limits=[
            SpeedLimitSegment(
                segment_id=1,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-50.0, y=-13.5, z=0.0),
                end_position=Point3D(x=-10.0, y=-13.5, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=2,
        predecessor_lane_ids=[],
        successor_lane_ids=[4],  # Connect to curve lane
        road_id=hash("RightAngleTurn_100"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_f1_straight)
    
    # 弯道部分 - 半径 R - 0.5W = 10 - 1.75 = 8.25米
    f1_curve_centerline = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 8.25 * math.sin(rad)
        y = 8.25 * (1 - math.cos(rad))
        f1_curve_centerline.append(Point3D(x=x, y=y, z=0.0))
    
    lane_f1_curve = Lane(
        lane_id=4,
        original_lane_id=1,
        original_road_id=200,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f1_curve_centerline,
        left_boundary_segment_indices=[1],  # segment_id=2
        right_boundary_segment_indices=[4],  # segment_id=5
        speed_limits=[
            SpeedLimitSegment(
                segment_id=4,
                speed_limit=8.33,  # 30 km/h
                start_position=Point3D(x=-10.0, y=-13.5, z=0.0),
                end_position=Point3D(x=0.0, y=8.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=5,
        predecessor_lane_ids=[1],  # From straight lane
        successor_lane_ids=[7],  # Connect to exit lane
        road_id=hash("RightAngleTurn_200"),
        junction_id=hash("RightAngleTurn_999"),
        is_junction_lane=True
    )
    lanes.append(lane_f1_curve)
    
    # 出口直道部分 - 中心线在 x = R - W = 10 - 3.5 = 6.5
    f1_exit_centerline = [
        Point3D(x=6.5, y=10.0, z=0.0),
        Point3D(x=6.5, y=20.0, z=0.0),
        Point3D(x=6.5, y=30.0, z=0.0),
        Point3D(x=6.5, y=40.0, z=0.0),
        Point3D(x=6.5, y=50.0, z=0.0),
    ]
    
    lane_f1_exit = Lane(
        lane_id=7,
        original_lane_id=1,
        original_road_id=300,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f1_exit_centerline,
        left_boundary_segment_indices=[2],  # segment_id=3
        right_boundary_segment_indices=[5],  # segment_id=6
        speed_limits=[
            SpeedLimitSegment(
                segment_id=7,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=6.5, y=10.0, z=0.0),
                end_position=Point3D(x=6.5, y=50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=8,
        predecessor_lane_ids=[4],  # From curve lane
        successor_lane_ids=[],
        road_id=hash("RightAngleTurn_300"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_f1_exit)
    
    # ==================== 正向车道2（中间左侧）Forward Lane 2 (Middle Left) ====================
    # 直道部分 - 中心线在 y = -R - 0.5W = -10 - 1.75 = -11.75
    f2_straight_centerline = [
        Point3D(x=-50.0, y=-11.75, z=0.0),
        Point3D(x=-40.0, y=-11.75, z=0.0),
        Point3D(x=-30.0, y=-11.75, z=0.0),
        Point3D(x=-20.0, y=-11.75, z=0.0),
        Point3D(x=-10.0, y=-11.75, z=0.0),
    ]
    
    lane_f2_straight = Lane(
        lane_id=2,
        original_lane_id=2,
        original_road_id=100,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f2_straight_centerline,
        left_boundary_segment_indices=[3],  # segment_id=4
        right_boundary_segment_indices=[6],  # segment_id=7
        speed_limits=[
            SpeedLimitSegment(
                segment_id=2,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-50.0, y=-11.75, z=0.0),
                end_position=Point3D(x=-10.0, y=-11.75, z=0.0)
            )
        ],
        left_adjacent_lane_id=1,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[],
        successor_lane_ids=[5],  # Connect to curve lane
        road_id=hash("RightAngleTurn_100"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_f2_straight)
    
    # 弯道部分 - 半径 R = 10米
    f2_curve_centerline = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 10.0 * math.sin(rad)
        y = 10.0 * (1 - math.cos(rad))
        f2_curve_centerline.append(Point3D(x=x, y=y, z=0.0))
    
    lane_f2_curve = Lane(
        lane_id=5,
        original_lane_id=2,
        original_road_id=200,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f2_curve_centerline,
        left_boundary_segment_indices=[4],  # segment_id=5
        right_boundary_segment_indices=[7],  # segment_id=8
        speed_limits=[
            SpeedLimitSegment(
                segment_id=5,
                speed_limit=8.33,  # 30 km/h
                start_position=Point3D(x=-10.0, y=-11.75, z=0.0),
                end_position=Point3D(x=0.0, y=10.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=4,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[2],  # From straight lane
        successor_lane_ids=[8],  # Connect to exit lane
        road_id=hash("RightAngleTurn_200"),
        junction_id=hash("RightAngleTurn_999"),
        is_junction_lane=True
    )
    lanes.append(lane_f2_curve)
    
    # 出口直道部分 - 中心线在 x = R - 0.5W = 10 - 1.75 = 8.25
    f2_exit_centerline = [
        Point3D(x=8.25, y=10.0, z=0.0),
        Point3D(x=8.25, y=20.0, z=0.0),
        Point3D(x=8.25, y=30.0, z=0.0),
        Point3D(x=8.25, y=40.0, z=0.0),
        Point3D(x=8.25, y=50.0, z=0.0),
    ]
    
    lane_f2_exit = Lane(
        lane_id=8,
        original_lane_id=2,
        original_road_id=300,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f2_exit_centerline,
        left_boundary_segment_indices=[5],  # segment_id=6
        right_boundary_segment_indices=[8],  # segment_id=9
        speed_limits=[
            SpeedLimitSegment(
                segment_id=8,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=8.25, y=10.0, z=0.0),
                end_position=Point3D(x=8.25, y=50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=7,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[5],  # From curve lane
        successor_lane_ids=[],
        road_id=hash("RightAngleTurn_300"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_f2_exit)
    
    # ==================== 反向车道1（中间右侧）Backward Lane 1 (Middle Right) ====================
    # 直道部分 - 中心线在 y = R + 0.5W = 10 + 1.75 = 11.75
    b1_straight_centerline = [
        Point3D(x=-50.0, y=11.75, z=0.0),
        Point3D(x=-40.0, y=11.75, z=0.0),
        Point3D(x=-30.0, y=11.75, z=0.0),
        Point3D(x=-20.0, y=11.75, z=0.0),
        Point3D(x=-10.0, y=11.75, z=0.0),
    ]
    
    lane_b1_straight = Lane(
        lane_id=3,
        original_lane_id=-1,
        original_road_id=101,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=b1_straight_centerline,
        left_boundary_segment_indices=[9],  # segment_id=10
        right_boundary_segment_indices=[6],  # segment_id=7
        speed_limits=[
            SpeedLimitSegment(
                segment_id=3,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-50.0, y=11.75, z=0.0),
                end_position=Point3D(x=-10.0, y=11.75, z=0.0)
            )
        ],
        left_adjacent_lane_id=2,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[],
        successor_lane_ids=[6],  # Connect to curve lane
        road_id=hash("RightAngleTurn_101"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_b1_straight)
    
    # 弯道部分 - 半径 R = 10米
    b1_curve_centerline = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 10.0 * math.sin(rad)
        y = 10.0 * (1 - math.cos(rad))
        b1_curve_centerline.append(Point3D(x=x, y=y, z=0.0))
    
    lane_b1_curve = Lane(
        lane_id=6,
        original_lane_id=-1,
        original_road_id=201,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=b1_curve_centerline,
        left_boundary_segment_indices=[10],  # segment_id=11
        right_boundary_segment_indices=[7],  # segment_id=8
        speed_limits=[
            SpeedLimitSegment(
                segment_id=6,
                speed_limit=8.33,  # 30 km/h
                start_position=Point3D(x=-10.0, y=11.75, z=0.0),
                end_position=Point3D(x=0.0, y=10.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[3],  # From straight lane
        successor_lane_ids=[9],  # Connect to exit lane
        road_id=hash("RightAngleTurn_201"),
        junction_id=hash("RightAngleTurn_999"),
        is_junction_lane=True
    )
    lanes.append(lane_b1_curve)
    
    # 出口直道部分 - 中心线在 x = R - 0.5W = 10 - 1.75 = 8.25
    b1_exit_centerline = [
        Point3D(x=-8.25, y=10.0, z=0.0),
        Point3D(x=-8.25, y=20.0, z=0.0),
        Point3D(x=-8.25, y=30.0, z=0.0),
        Point3D(x=-8.25, y=40.0, z=0.0),
        Point3D(x=-8.25, y=50.0, z=0.0),
    ]
    
    lane_b1_exit = Lane(
        lane_id=9,
        original_lane_id=-1,
        original_road_id=301,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=b1_exit_centerline,
        left_boundary_segment_indices=[11],  # segment_id=12
        right_boundary_segment_indices=[8],  # segment_id=9
        speed_limits=[
            SpeedLimitSegment(
                segment_id=9,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-8.25, y=10.0, z=0.0),
                end_position=Point3D(x=-8.25, y=50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[6],  # From curve lane
        successor_lane_ids=[],
        road_id=hash("RightAngleTurn_301"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_b1_exit)
    
    # ==================== 反向车道2（最右侧）Backward Lane 2 (Rightmost) ====================
    # 直道部分 - 中心线在 y = R + W = 10 + 3.5 = 13.5
    b2_straight_centerline = [
        Point3D(x=-50.0, y=13.5, z=0.0),
        Point3D(x=-40.0, y=13.5, z=0.0),
        Point3D(x=-30.0, y=13.5, z=0.0),
        Point3D(x=-20.0, y=13.5, z=0.0),
        Point3D(x=-10.0, y=13.5, z=0.0),
    ]
    
    lane_b2_straight = Lane(
        lane_id=10,
        original_lane_id=-2,
        original_road_id=101,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=b2_straight_centerline,
        left_boundary_segment_indices=[12],  # segment_id=13
        right_boundary_segment_indices=[],  # No right boundary (edge of road)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=10,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-50.0, y=13.5, z=0.0),
                end_position=Point3D(x=-10.0, y=13.5, z=0.0)
            )
        ],
        left_adjacent_lane_id=3,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[],
        successor_lane_ids=[11],  # Connect to curve lane
        road_id=hash("RightAngleTurn_101"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_b2_straight)
    
    # 弯道部分 - 半径 R + 0.5W = 10 + 1.75 = 11.75米
    b2_curve_centerline = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 11.75 * math.sin(rad)
        y = 11.75 * (1 - math.cos(rad))
        b2_curve_centerline.append(Point3D(x=x, y=y, z=0.0))
    
    lane_b2_curve = Lane(
        lane_id=11,
        original_lane_id=-2,
        original_road_id=201,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=b2_curve_centerline,
        left_boundary_segment_indices=[13],  # segment_id=14
        right_boundary_segment_indices=[],  # No right boundary (edge of road)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=11,
                speed_limit=8.33,  # 30 km/h
                start_position=Point3D(x=-10.0, y=13.5, z=0.0),
                end_position=Point3D(x=0.0, y=11.75, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[10],  # From straight lane
        successor_lane_ids=[12],  # Connect to exit lane
        road_id=hash("RightAngleTurn_201"),
        junction_id=hash("RightAngleTurn_999"),
        is_junction_lane=True
    )
    lanes.append(lane_b2_curve)
    
    # 出口直道部分 - 中心线在 x = R + W = 10 + 3.5 = 13.5
    b2_exit_centerline = [
        Point3D(x=13.5, y=10.0, z=0.0),
        Point3D(x=13.5, y=20.0, z=0.0),
        Point3D(x=13.5, y=30.0, z=0.0),
        Point3D(x=13.5, y=40.0, z=0.0),
        Point3D(x=13.5, y=50.0, z=0.0),
    ]
    
    lane_b2_exit = Lane(
        lane_id=12,
        original_lane_id=-2,
        original_road_id=301,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=b2_exit_centerline,
        left_boundary_segment_indices=[14],  # segment_id=15
        right_boundary_segment_indices=[],  # No right boundary (edge of road)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=12,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=13.5, y=10.0, z=0.0),
                end_position=Point3D(x=13.5, y=50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[11],  # From curve lane
        successor_lane_ids=[],
        road_id=hash("RightAngleTurn_301"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_b2_exit)
    
    local_map.lanes.extend(lanes)
    
    # ==================== 添加交通信号灯 / Add Traffic Lights ====================
    # 在弯道入口添加交通信号灯（两个方向）
    # 正向交通灯
    traffic_light_forward = TrafficLight(
        traffic_light_id=1,
        associated_lane_id=1,  # 关联正向直道车道
        position=Point3D(x=-12.0, y=-14.0, z=5.0),
        current_state=TrafficLightState(
            timestamp=datetime.now(),
            color=TrafficLightColor.GREEN,
            shape=None,
            status=None,
            remaining_time=30.0
        ),
        distance_to_stop_line=2.0,
        associated_stop_line_id=0,
        light_type=None,
        confidence=1.0
    )
    local_map.traffic_lights.append(traffic_light_forward)
    
    # 反向交通灯
    traffic_light_backward = TrafficLight(
        traffic_light_id=2,
        associated_lane_id=3,  # 关联反向直道车道
        position=Point3D(x=-12.0, y=14.0, z=5.0),
        current_state=TrafficLightState(
            timestamp=datetime.now(),
            color=TrafficLightColor.RED,
            shape=None,
            status=None,
            remaining_time=30.0
        ),
        distance_to_stop_line=2.0,
        associated_stop_line_id=0,
        light_type=None,
        confidence=1.0
    )
    local_map.traffic_lights.append(traffic_light_backward)
    
    # ==================== 添加交通标志 / Add Traffic Signs ====================
    # 添加限速标志（两个方向）
    for lane_id, x, y in [(1, -40.0, -14.0), (3, -40.0, 14.0)]:
        traffic_sign = TrafficSign(
            traffic_sign_id=len(local_map.traffic_signs) + 1,
            associated_lane_id=lane_id,
            position=Point3D(x=x, y=y, z=3.0),
            sign_type=TrafficSignType.SPEED_LIMIT,
            distance_to_sign=5.0,
            value=60.0,  # 60 km/h
            text_content="60",
            confidence=1.0,
            is_valid=True,
            valid_until=None
        )
        local_map.traffic_signs.append(traffic_sign)
    
    # 添加弯道警告标志（两个方向）
    traffic_sign_curve_forward = TrafficSign(
        traffic_sign_id=len(local_map.traffic_signs) + 1,
        associated_lane_id=4,
        position=Point3D(x=-12.0, y=-9.0, z=3.0),
        sign_type=TrafficSignType.CURVE_RIGHT,  # 右急弯 / Right curve
        distance_to_sign=5.0,
        value=None,
        text_content="Right Turn",
        confidence=1.0,
        is_valid=True,
        valid_until=None
    )
    local_map.traffic_signs.append(traffic_sign_curve_forward)
    
    traffic_sign_curve_backward = TrafficSign(
        traffic_sign_id=len(local_map.traffic_signs) + 1,
        associated_lane_id=6,
        position=Point3D(x=-12.0, y=12.0, z=3.0),
        sign_type=TrafficSignType.CURVE_RIGHT,  # 右急弯 / Right curve
        distance_to_sign=5.0,
        value=None,
        text_content="Right Turn",
        confidence=1.0,
        is_valid=True,
        valid_until=None
    )
    local_map.traffic_signs.append(traffic_sign_curve_backward)
    
    return local_map


def test_right_angle_turn():
    """
    测试直角弯道地图
    Test right angle turn map
    """
    print("=" * 60)
    print("测试直角弯道地图")
    print("Testing Right Angle Turn Map")
    print("=" * 60)
    
    # 创建直角弯道地图
    local_map = create_right_angle_turn_map()
    
    # 创建API实例
    api = LocalMapAPI(local_map)
    
    # 统计信息
    print(f"\n地图统计信息 / Map Statistics:")
    print(f"  总车道数 / Total lanes: {len(local_map.lanes)}")
    print(f"  边界分段数 / Boundary segments: {len(local_map.boundary_segments)}")
    print(f"  交通信号灯数 / Traffic lights: {len(local_map.traffic_lights)}")
    print(f"  交通标志数 / Traffic signs: {len(local_map.traffic_signs)}")
    
    # 统计不同类型的车道
    driving_lanes = api.get_lanes_by_type(LaneType.DRIVING)
    junction_lanes = [lane for lane in local_map.lanes if lane.is_junction_lane]
    
    print(f"\n车道分类 / Lane Classification:")
    print(f"  行驶车道 / Driving lanes: {len(driving_lanes)}")
    print(f"  交叉口车道 / Junction lanes: {len(junction_lanes)}")
    print(f"  非交叉口车道 / Non-junction lanes: {len(driving_lanes) - len(junction_lanes)}")
    
    # 统计不同方向的道路
    roads = {}
    for lane in local_map.lanes:
        if lane.original_road_id not in roads:
            roads[lane.original_road_id] = []
        roads[lane.original_road_id].append(lane)
    
    print(f"\n道路分布 / Road Distribution:")
    for road_id, road_lanes in sorted(roads.items()):
        road_name = {
            100: "正向直道 (Forward Straight)",
            101: "反向直道 (Backward Straight)",
            200: "正向弯道 (Forward Curve)",
            201: "反向弯道 (Backward Curve)",
            300: "正向出口 (Forward Exit)",
            301: "反向出口 (Backward Exit)",
        }.get(road_id, f"Road {road_id}")
        print(f"  {road_name}: {len(road_lanes)} lanes")
    
    # 统计不同方向的车道
    forward_lanes = [lane for lane in local_map.lanes if lane.original_road_id in [100, 200, 300]]
    backward_lanes = [lane for lane in local_map.lanes if lane.original_road_id in [101, 201, 301]]
    
    print(f"\n方向统计 / Direction Statistics:")
    print(f"  正向车道 / Forward lanes: {len(forward_lanes)}")
    print(f"  反向车道 / Backward lanes: {len(backward_lanes)}")
    
    # 显示每个车道的详细信息
    print(f"\n车道详细信息 / Lane Details:")
    for lane in local_map.lanes:
        lane_type = "弯道" if lane.is_junction_lane else "直道"
        print(f"  Lane {lane.lane_id} ({lane_type}): {len(lane.centerline_points)} centerline points")
        print(f"    左边界索引 / Left boundary indices: {lane.left_boundary_segment_indices}")
        print(f"    右边界索引 / Right boundary indices: {lane.right_boundary_segment_indices}")
        print(f"    前驱车道 / Predecessors: {lane.predecessor_lane_ids}")
        print(f"    后继车道 / Successors: {lane.successor_lane_ids}")
    
    # 显示交通信号灯状态
    print(f"\n交通信号灯状态 / Traffic Light States:")
    for light in local_map.traffic_lights:
        direction = "正向" if light.traffic_light_id == 1 else "反向"
        print(f"  {direction} / {direction}: {light.current_state.color.name} (剩余 {light.current_state.remaining_time:.1f}s)")
    
    # 可视化地图
    print(f"\n[可视化] 生成地图可视化...")
    print(f"[Visualization] Generating map visualization...")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存可视化图片
    save_path = os.path.join(output_dir, "right_angle_turn.png")
    
    # 使用API的可视化方法
    api.visualize(
        title="Right Angle Turn Map (直角弯道地图)",
        show_lanes=True,
        show_centerlines=True,
        show_traffic_elements=True,
        show_ego_position=True,
        save_path=save_path,
        dpi=150
    )
    
    print(f"\n可视化图片已保存到 / Visualization saved to:")
    print(f"  {save_path}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("Test Completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_right_angle_turn()
