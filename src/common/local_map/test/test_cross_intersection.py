"""
测试十字路口地图
Test Cross Intersection Map

测试包含十字路口的复杂地图结构，包含四个方向的road
Tests complex map structure with cross intersection, including roads from four directions
"""

import sys
import os
from datetime import datetime

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


def create_cross_intersection_map() -> LocalMap:
    """
    创建十字路口地图
    Create cross intersection map
    
    Returns:
        LocalMap: 十字路口地图 / Cross intersection map
    """
    # Ego position at center of intersection
    ego_pose = Pose(
        position=Point3D(x=0.0, y=0.0, z=0.0),
        heading=0.0,
        pitch=0.0,
        roll=0.0
    )
    
    # Create empty local map with 300m radius
    local_map = create_empty_local_map(ego_pose, 300.0)
    
    # ==================== 创建边界分段 / Create Boundary Segments ====================
    boundary_segments = []
    
    # 南向北道路 (South to North Road)
    # 左边界 (west side)
    for i in range(1, 4):
        boundary_segments.append(LaneBoundarySegment(
            segment_id=i,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.YELLOW,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=-50.0, y=-8.0 - (i-1)*3.5, z=0.0),
                Point3D(x=0.0, y=-8.0 - (i-1)*3.5, z=0.0),
                Point3D(x=50.0, y=-8.0 - (i-1)*3.5, z=0.0),
            ]
        ))
    
    # 右边界 (east side)
    for i in range(1, 4):
        boundary_segments.append(LaneBoundarySegment(
            segment_id=i+10,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.YELLOW,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=-50.0, y=8.0 + (i-1)*3.5, z=0.0),
                Point3D(x=0.0, y=8.0 + (i-1)*3.5, z=0.0),
                Point3D(x=50.0, y=8.0 + (i-1)*3.5, z=0.0),
            ]
        ))
    
    # 北向南道路 (North to South Road)
    for i in range(1, 4):
        boundary_segments.append(LaneBoundarySegment(
            segment_id=i+20,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.YELLOW,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=-50.0, y=8.0 + (i-1)*3.5, z=0.0),
                Point3D(x=0.0, y=8.0 + (i-1)*3.5, z=0.0),
                Point3D(x=50.0, y=8.0 + (i-1)*3.5, z=0.0),
            ]
        ))
    
    for i in range(1, 4):
        boundary_segments.append(LaneBoundarySegment(
            segment_id=i+30,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.YELLOW,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=-50.0, y=-8.0 - (i-1)*3.5, z=0.0),
                Point3D(x=0.0, y=-8.0 - (i-1)*3.5, z=0.0),
                Point3D(x=50.0, y=-8.0 - (i-1)*3.5, z=0.0),
            ]
        ))
    
    # 西向东道路 (West to East Road)
    for i in range(1, 4):
        boundary_segments.append(LaneBoundarySegment(
            segment_id=i+40,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.YELLOW,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=-8.0 - (i-1)*3.5, y=-50.0, z=0.0),
                Point3D(x=-8.0 - (i-1)*3.5, y=0.0, z=0.0),
                Point3D(x=-8.0 - (i-1)*3.5, y=50.0, z=0.0),
            ]
        ))
    
    for i in range(1, 4):
        boundary_segments.append(LaneBoundarySegment(
            segment_id=i+50,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.YELLOW,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=8.0 + (i-1)*3.5, y=-50.0, z=0.0),
                Point3D(x=8.0 + (i-1)*3.5, y=0.0, z=0.0),
                Point3D(x=8.0 + (i-1)*3.5, y=50.0, z=0.0),
            ]
        ))
    
    # 东向西道路 (East to West Road)
    for i in range(1, 4):
        boundary_segments.append(LaneBoundarySegment(
            segment_id=i+60,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.YELLOW,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=8.0 + (i-1)*3.5, y=-50.0, z=0.0),
                Point3D(x=8.0 + (i-1)*3.5, y=0.0, z=0.0),
                Point3D(x=8.0 + (i-1)*3.5, y=50.0, z=0.0),
            ]
        ))
    
    for i in range(1, 4):
        boundary_segments.append(LaneBoundarySegment(
            segment_id=i+70,
            boundary_type=BoundaryType.LINE,
            boundary_line_shape=BoundaryLineShape.SOLID,
            boundary_color=BoundaryColor.YELLOW,
            boundary_thickness=0.15,
            is_virtual=False,
            boundary_points=[
                Point3D(x=-8.0 - (i-1)*3.5, y=-50.0, z=0.0),
                Point3D(x=-8.0 - (i-1)*3.5, y=0.0, z=0.0),
                Point3D(x=-8.0 - (i-1)*3.5, y=50.0, z=0.0),
            ]
        ))
    
    local_map.boundary_segments.extend(boundary_segments)
    
    # ==================== 创建车道 / Create Lanes ====================
    lanes = []
    
    # 南向北道路 (South to North Road) - Road ID 100
    for i in range(3):
        lane = Lane(
            lane_id=100 + i,
            original_lane_id=-1 - i,
            original_road_id=100,
            original_junction_id=None,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=-50.0, y=-5.25 - i*3.5, z=0.0),
                Point3D(x=-25.0, y=-5.25 - i*3.5, z=0.0),
                Point3D(x=-10.0, y=-5.25 - i*3.5, z=0.0),
            ],
            left_boundary_segment_indices=[i],
            right_boundary_segment_indices=[i+10] if i < 2 else [i+9],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=100 + i,
                    speed_limit=16.67,  # 60 km/h
                    start_position=Point3D(x=-50.0, y=-5.25 - i*3.5, z=0.0),
                    end_position=Point3D(x=-10.0, y=-5.25 - i*3.5, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 100 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 100 + i + 1,
            predecessor_lane_ids=[],
            successor_lane_ids=[200 + i],  # Connect to intersection lanes
            road_id=hash("CrossIntersection_100"),
            junction_id=None,
            is_junction_lane=False
        )
        lanes.append(lane)
    
    # 北向南道路 (North to South Road) - Road ID 101
    for i in range(3):
        lane = Lane(
            lane_id=110 + i,
            original_lane_id=1 + i,
            original_road_id=101,
            original_junction_id=None,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=50.0, y=5.25 + i*3.5, z=0.0),
                Point3D(x=25.0, y=5.25 + i*3.5, z=0.0),
                Point3D(x=10.0, y=5.25 + i*3.5, z=0.0),
            ],
            left_boundary_segment_indices=[i+30],
            right_boundary_segment_indices=[i+20] if i < 2 else [i+19],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=110 + i,
                    speed_limit=16.67,  # 60 km/h
                    start_position=Point3D(x=50.0, y=5.25 + i*3.5, z=0.0),
                    end_position=Point3D(x=10.0, y=5.25 + i*3.5, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 110 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 110 + i + 1,
            predecessor_lane_ids=[],
            successor_lane_ids=[210 + i],  # Connect to intersection lanes
            road_id=hash("CrossIntersection_101"),
            junction_id=None,
            is_junction_lane=False
        )
        lanes.append(lane)
    
    # 西向东道路 (West to East Road) - Road ID 102
    for i in range(3):
        lane = Lane(
            lane_id=120 + i,
            original_lane_id=-1 - i,
            original_road_id=102,
            original_junction_id=None,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=-5.25 - i*3.5, y=-50.0, z=0.0),
                Point3D(x=-5.25 - i*3.5, y=-25.0, z=0.0),
                Point3D(x=-5.25 - i*3.5, y=-10.0, z=0.0),
            ],
            left_boundary_segment_indices=[i+40],
            right_boundary_segment_indices=[i+50] if i < 2 else [i+49],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=120 + i,
                    speed_limit=16.67,  # 60 km/h
                    start_position=Point3D(x=-5.25 - i*3.5, y=-50.0, z=0.0),
                    end_position=Point3D(x=-5.25 - i*3.5, y=-10.0, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 120 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 120 + i + 1,
            predecessor_lane_ids=[],
            successor_lane_ids=[220 + i],  # Connect to intersection lanes
            road_id=hash("CrossIntersection_102"),
            junction_id=None,
            is_junction_lane=False
        )
        lanes.append(lane)
    
    # 东向西道路 (East to West Road) - Road ID 103
    for i in range(3):
        lane = Lane(
            lane_id=130 + i,
            original_lane_id=1 + i,
            original_road_id=103,
            original_junction_id=None,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=5.25 + i*3.5, y=50.0, z=0.0),
                Point3D(x=5.25 + i*3.5, y=25.0, z=0.0),
                Point3D(x=5.25 + i*3.5, y=10.0, z=0.0),
            ],
            left_boundary_segment_indices=[i+70],
            right_boundary_segment_indices=[i+60] if i < 2 else [i+59],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=130 + i,
                    speed_limit=16.67,  # 60 km/h
                    start_position=Point3D(x=5.25 + i*3.5, y=50.0, z=0.0),
                    end_position=Point3D(x=5.25 + i*3.5, y=10.0, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 130 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 130 + i + 1,
            predecessor_lane_ids=[],
            successor_lane_ids=[230 + i],  # Connect to intersection lanes
            road_id=hash("CrossIntersection_103"),
            junction_id=None,
            is_junction_lane=False
        )
        lanes.append(lane)
    
    # 交叉口内部车道 (Junction Internal Lanes) - Road ID 200
    # 直行车道 (Straight lanes)
    for i in range(3):
        # 南向北直行
        lane = Lane(
            lane_id=200 + i,
            original_lane_id=-1 - i,
            original_road_id=200,
            original_junction_id=999,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=-10.0, y=-5.25 - i*3.5, z=0.0),
                Point3D(x=0.0, y=-5.25 - i*3.5, z=0.0),
                Point3D(x=10.0, y=-5.25 - i*3.5, z=0.0),
            ],
            left_boundary_segment_indices=[],
            right_boundary_segment_indices=[],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=200 + i,
                    speed_limit=8.33,  # 30 km/h
                    start_position=Point3D(x=-10.0, y=-5.25 - i*3.5, z=0.0),
                    end_position=Point3D(x=10.0, y=-5.25 - i*3.5, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 200 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 200 + i + 1,
            predecessor_lane_ids=[100 + i],
            successor_lane_ids=[300 + i],
            road_id=hash("CrossIntersection_200"),
            junction_id=hash("CrossIntersection_999"),
            is_junction_lane=True
        )
        lanes.append(lane)
    
    for i in range(3):
        # 北向南直行
        lane = Lane(
            lane_id=210 + i,
            original_lane_id=1 + i,
            original_road_id=200,
            original_junction_id=999,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=10.0, y=5.25 + i*3.5, z=0.0),
                Point3D(x=0.0, y=5.25 + i*3.5, z=0.0),
                Point3D(x=-10.0, y=5.25 + i*3.5, z=0.0),
            ],
            left_boundary_segment_indices=[],
            right_boundary_segment_indices=[],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=210 + i,
                    speed_limit=8.33,  # 30 km/h
                    start_position=Point3D(x=10.0, y=5.25 + i*3.5, z=0.0),
                    end_position=Point3D(x=-10.0, y=5.25 + i*3.5, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 210 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 210 + i + 1,
            predecessor_lane_ids=[110 + i],
            successor_lane_ids=[310 + i],
            road_id=hash("CrossIntersection_200"),
            junction_id=hash("CrossIntersection_999"),
            is_junction_lane=True
        )
        lanes.append(lane)
    
    for i in range(3):
        # 西向东直行
        lane = Lane(
            lane_id=220 + i,
            original_lane_id=-1 - i,
            original_road_id=200,
            original_junction_id=999,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=-5.25 - i*3.5, y=-10.0, z=0.0),
                Point3D(x=-5.25 - i*3.5, y=0.0, z=0.0),
                Point3D(x=-5.25 - i*3.5, y=10.0, z=0.0),
            ],
            left_boundary_segment_indices=[],
            right_boundary_segment_indices=[],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=220 + i,
                    speed_limit=8.33,  # 30 km/h
                    start_position=Point3D(x=-5.25 - i*3.5, y=-10.0, z=0.0),
                    end_position=Point3D(x=-5.25 - i*3.5, y=10.0, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 220 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 220 + i + 1,
            predecessor_lane_ids=[120 + i],
            successor_lane_ids=[320 + i],
            road_id=hash("CrossIntersection_200"),
            junction_id=hash("CrossIntersection_999"),
            is_junction_lane=True
        )
        lanes.append(lane)
    
    for i in range(3):
        # 东向西直行
        lane = Lane(
            lane_id=230 + i,
            original_lane_id=1 + i,
            original_road_id=200,
            original_junction_id=999,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=5.25 + i*3.5, y=10.0, z=0.0),
                Point3D(x=5.25 + i*3.5, y=0.0, z=0.0),
                Point3D(x=5.25 + i*3.5, y=-10.0, z=0.0),
            ],
            left_boundary_segment_indices=[],
            right_boundary_segment_indices=[],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=230 + i,
                    speed_limit=8.33,  # 30 km/h
                    start_position=Point3D(x=5.25 + i*3.5, y=10.0, z=0.0),
                    end_position=Point3D(x=5.25 + i*3.5, y=-10.0, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 230 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 230 + i + 1,
            predecessor_lane_ids=[130 + i],
            successor_lane_ids=[330 + i],
            road_id=hash("CrossIntersection_200"),
            junction_id=hash("CrossIntersection_999"),
            is_junction_lane=True
        )
        lanes.append(lane)
    
    # 左转车道 (Left Turn Lanes) - Road ID 201
    # 南向北左转（转向东向西出口）
    lane = Lane(
        lane_id=400,
        original_lane_id=-1,
        original_road_id=201,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=-10.0, y=-5.25, z=0.0),
            Point3D(x=-5.0, y=-5.25, z=0.0),
            Point3D(x=0.0, y=-5.25, z=0.0),
            Point3D(x=5.0, y=-10.0, z=0.0),
            Point3D(x=10.0, y=-5.25, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=400,
                speed_limit=6.94,  # 25 km/h
                start_position=Point3D(x=-10.0, y=-5.25, z=0.0),
                end_position=Point3D(x=10.0, y=-5.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[100],
        successor_lane_ids=[410],
        road_id=hash("CrossIntersection_201"),
        junction_id=hash("CrossIntersection_999"),
        is_junction_lane=True
    )
    lanes.append(lane)
    
    # 北向南左转（转向西向东出口）
    lane = Lane(
        lane_id=401,
        original_lane_id=1,
        original_road_id=201,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=10.0, y=5.25, z=0.0),
            Point3D(x=5.0, y=5.25, z=0.0),
            Point3D(x=0.0, y=5.25, z=0.0),
            Point3D(x=-5.0, y=10.0, z=0.0),
            Point3D(x=-10.0, y=5.25, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=401,
                speed_limit=6.94,  # 25 km/h
                start_position=Point3D(x=10.0, y=5.25, z=0.0),
                end_position=Point3D(x=-10.0, y=5.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[110],
        successor_lane_ids=[411],
        road_id=hash("CrossIntersection_201"),
        junction_id=hash("CrossIntersection_999"),
        is_junction_lane=True
    )
    lanes.append(lane)
    
    # 西向东左转（转向南向北出口）
    lane = Lane(
        lane_id=402,
        original_lane_id=-1,
        original_road_id=201,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=-5.25, y=-10.0, z=0.0),
            Point3D(x=-5.25, y=-5.0, z=0.0),
            Point3D(x=-5.25, y=0.0, z=0.0),
            Point3D(x=-10.0, y=5.0, z=0.0),
            Point3D(x=-5.25, y=10.0, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=402,
                speed_limit=6.94,  # 25 km/h
                start_position=Point3D(x=-5.25, y=-10.0, z=0.0),
                end_position=Point3D(x=-5.25, y=10.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[120],
        successor_lane_ids=[412],
        road_id=hash("CrossIntersection_201"),
        junction_id=hash("CrossIntersection_999"),
        is_junction_lane=True
    )
    lanes.append(lane)
    
    # 东向西左转（转向北向南出口）
    lane = Lane(
        lane_id=403,
        original_lane_id=1,
        original_road_id=201,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=5.25, y=10.0, z=0.0),
            Point3D(x=5.25, y=5.0, z=0.0),
            Point3D(x=5.25, y=0.0, z=0.0),
            Point3D(x=10.0, y=-5.0, z=0.0),
            Point3D(x=5.25, y=-10.0, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=403,
                speed_limit=6.94,  # 25 km/h
                start_position=Point3D(x=5.25, y=10.0, z=0.0),
                end_position=Point3D(x=5.25, y=-10.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[130],
        successor_lane_ids=[413],
        road_id=hash("CrossIntersection_201"),
        junction_id=hash("CrossIntersection_999"),
        is_junction_lane=True
    )
    lanes.append(lane)
    
    # 右转车道 (Right Turn Lanes) - Road ID 202
    # 南向北右转（转向西向东出口）
    lane = Lane(
        lane_id=404,
        original_lane_id=-3,
        original_road_id=202,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=-10.0, y=-12.25, z=0.0),
            Point3D(x=-5.0, y=-12.25, z=0.0),
            Point3D(x=-5.25, y=-10.0, z=0.0),
            Point3D(x=-5.25, y=-5.0, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=404,
                speed_limit=5.56,  # 20 km/h
                start_position=Point3D(x=-10.0, y=-12.25, z=0.0),
                end_position=Point3D(x=-5.25, y=-5.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[102],
        successor_lane_ids=[414],
        road_id=hash("CrossIntersection_202"),
        junction_id=hash("CrossIntersection_999"),
        is_junction_lane=True
    )
    lanes.append(lane)
    
    # 北向南右转（转向东向西出口）
    lane = Lane(
        lane_id=405,
        original_lane_id=3,
        original_road_id=202,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=10.0, y=12.25, z=0.0),
            Point3D(x=5.0, y=12.25, z=0.0),
            Point3D(x=5.25, y=10.0, z=0.0),
            Point3D(x=5.25, y=5.0, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=405,
                speed_limit=5.56,  # 20 km/h
                start_position=Point3D(x=10.0, y=12.25, z=0.0),
                end_position=Point3D(x=5.25, y=5.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[112],
        successor_lane_ids=[415],
        road_id=hash("CrossIntersection_202"),
        junction_id=hash("CrossIntersection_999"),
        is_junction_lane=True
    )
    lanes.append(lane)
    
    # 西向东右转（转向北向南出口）
    lane = Lane(
        lane_id=406,
        original_lane_id=-3,
        original_road_id=202,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=-12.25, y=-10.0, z=0.0),
            Point3D(x=-12.25, y=-5.0, z=0.0),
            Point3D(x=-10.0, y=-5.25, z=0.0),
            Point3D(x=-5.0, y=-5.25, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=406,
                speed_limit=5.56,  # 20 km/h
                start_position=Point3D(x=-12.25, y=-10.0, z=0.0),
                end_position=Point3D(x=-5.0, y=-5.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[122],
        successor_lane_ids=[416],
        road_id=hash("CrossIntersection_202"),
        junction_id=hash("CrossIntersection_999"),
        is_junction_lane=True
    )
    lanes.append(lane)
    
    # 东向西右转（转向南向北出口）
    lane = Lane(
        lane_id=407,
        original_lane_id=3,
        original_road_id=202,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=12.25, y=10.0, z=0.0),
            Point3D(x=12.25, y=5.0, z=0.0),
            Point3D(x=10.0, y=5.25, z=0.0),
            Point3D(x=5.0, y=5.25, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=407,
                speed_limit=5.56,  # 20 km/h
                start_position=Point3D(x=12.25, y=10.0, z=0.0),
                end_position=Point3D(x=5.0, y=5.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[132],
        successor_lane_ids=[417],
        road_id=hash("CrossIntersection_202"),
        junction_id=hash("CrossIntersection_999"),
        is_junction_lane=True
    )
    lanes.append(lane)
    
    # 出口车道 (Exit Lanes) - Road ID 300
    for i in range(3):
        # 南向北出口
        lane = Lane(
            lane_id=300 + i,
            original_lane_id=-1 - i,
            original_road_id=300,
            original_junction_id=None,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=10.0, y=-5.25 - i*3.5, z=0.0),
                Point3D(x=25.0, y=-5.25 - i*3.5, z=0.0),
                Point3D(x=50.0, y=-5.25 - i*3.5, z=0.0),
            ],
            left_boundary_segment_indices=[i+10],
            right_boundary_segment_indices=[i] if i < 2 else [i-1],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=300 + i,
                    speed_limit=16.67,  # 60 km/h
                    start_position=Point3D(x=10.0, y=-5.25 - i*3.5, z=0.0),
                    end_position=Point3D(x=50.0, y=-5.25 - i*3.5, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 300 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 300 + i + 1,
            predecessor_lane_ids=[200 + i],
            successor_lane_ids=[],
            road_id=hash("CrossIntersection_300"),
            junction_id=None,
            is_junction_lane=False
        )
        lanes.append(lane)
    
    for i in range(3):
        # 北向南出口
        lane = Lane(
            lane_id=310 + i,
            original_lane_id=1 + i,
            original_road_id=301,
            original_junction_id=None,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=-10.0, y=5.25 + i*3.5, z=0.0),
                Point3D(x=-25.0, y=5.25 + i*3.5, z=0.0),
                Point3D(x=-50.0, y=5.25 + i*3.5, z=0.0),
            ],
            left_boundary_segment_indices=[i+20],
            right_boundary_segment_indices=[i+30] if i < 2 else [i+29],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=310 + i,
                    speed_limit=16.67,  # 60 km/h
                    start_position=Point3D(x=-10.0, y=5.25 + i*3.5, z=0.0),
                    end_position=Point3D(x=-50.0, y=5.25 + i*3.5, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 310 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 310 + i + 1,
            predecessor_lane_ids=[210 + i],
            successor_lane_ids=[],
            road_id=hash("CrossIntersection_301"),
            junction_id=None,
            is_junction_lane=False
        )
        lanes.append(lane)
    
    for i in range(3):
        # 西向东出口
        lane = Lane(
            lane_id=320 + i,
            original_lane_id=-1 - i,
            original_road_id=302,
            original_junction_id=None,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=-5.25 - i*3.5, y=10.0, z=0.0),
                Point3D(x=-5.25 - i*3.5, y=25.0, z=0.0),
                Point3D(x=-5.25 - i*3.5, y=50.0, z=0.0),
            ],
            left_boundary_segment_indices=[i+50],
            right_boundary_segment_indices=[i+40] if i < 2 else [i+39],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=320 + i,
                    speed_limit=16.67,  # 60 km/h
                    start_position=Point3D(x=-5.25 - i*3.5, y=10.0, z=0.0),
                    end_position=Point3D(x=-5.25 - i*3.5, y=50.0, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 320 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 320 + i + 1,
            predecessor_lane_ids=[220 + i],
            successor_lane_ids=[],
            road_id=hash("CrossIntersection_302"),
            junction_id=None,
            is_junction_lane=False
        )
        lanes.append(lane)
    
    for i in range(3):
        # 东向西出口
        lane = Lane(
            lane_id=330 + i,
            original_lane_id=1 + i,
            original_road_id=303,
            original_junction_id=None,
            map_source_type="XODR",
            map_source_id="CrossIntersection",
            lane_type=LaneType.DRIVING,
            lane_direction=LaneDirection.FORWARD,
            centerline_points=[
                Point3D(x=5.25 + i*3.5, y=-10.0, z=0.0),
                Point3D(x=5.25 + i*3.5, y=-25.0, z=0.0),
                Point3D(x=5.25 + i*3.5, y=-50.0, z=0.0),
            ],
            left_boundary_segment_indices=[i+60],
            right_boundary_segment_indices=[i+70] if i < 2 else [i+69],
            speed_limits=[
                SpeedLimitSegment(
                    segment_id=330 + i,
                    speed_limit=16.67,  # 60 km/h
                    start_position=Point3D(x=5.25 + i*3.5, y=-10.0, z=0.0),
                    end_position=Point3D(x=5.25 + i*3.5, y=-50.0, z=0.0)
                )
            ],
            left_adjacent_lane_id=None if i == 0 else 330 + i - 1,
            right_adjacent_lane_id=None if i == 2 else 330 + i + 1,
            predecessor_lane_ids=[230 + i],
            successor_lane_ids=[],
            road_id=hash("CrossIntersection_303"),
            junction_id=None,
            is_junction_lane=False
        )
        lanes.append(lane)
    
    # 转弯出口车道 (Turn Exit Lanes) - Road IDs 310-317
    # 左转出口车道 (Left Turn Exit Lanes)
    # 南向北左转出口（转向东向西）
    lane = Lane(
        lane_id=410,
        original_lane_id=1,
        original_road_id=310,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=10.0, y=-5.25, z=0.0),
            Point3D(x=25.0, y=-5.25, z=0.0),
            Point3D(x=50.0, y=-5.25, z=0.0),
        ],
        left_boundary_segment_indices=[60],
        right_boundary_segment_indices=[70],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=410,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=10.0, y=-5.25, z=0.0),
                end_position=Point3D(x=50.0, y=-5.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[400],
        successor_lane_ids=[],
        road_id=hash("CrossIntersection_310"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane)
    
    # 北向南左转出口（转向西向东）
    lane = Lane(
        lane_id=411,
        original_lane_id=-1,
        original_road_id=311,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=-10.0, y=5.25, z=0.0),
            Point3D(x=-25.0, y=5.25, z=0.0),
            Point3D(x=-50.0, y=5.25, z=0.0),
        ],
        left_boundary_segment_indices=[50],
        right_boundary_segment_indices=[40],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=411,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-10.0, y=5.25, z=0.0),
                end_position=Point3D(x=-50.0, y=5.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[401],
        successor_lane_ids=[],
        road_id=hash("CrossIntersection_311"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane)
    
    # 西向东左转出口（转向南向北）
    lane = Lane(
        lane_id=412,
        original_lane_id=-1,
        original_road_id=312,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=-5.25, y=10.0, z=0.0),
            Point3D(x=-5.25, y=25.0, z=0.0),
            Point3D(x=-5.25, y=50.0, z=0.0),
        ],
        left_boundary_segment_indices=[10],
        right_boundary_segment_indices=[0],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=412,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-5.25, y=10.0, z=0.0),
                end_position=Point3D(x=-5.25, y=50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[402],
        successor_lane_ids=[],
        road_id=hash("CrossIntersection_312"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane)
    
    # 东向西左转出口（转向北向南）
    lane = Lane(
        lane_id=413,
        original_lane_id=1,
        original_road_id=313,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=5.25, y=-10.0, z=0.0),
            Point3D(x=5.25, y=-25.0, z=0.0),
            Point3D(x=5.25, y=-50.0, z=0.0),
        ],
        left_boundary_segment_indices=[30],
        right_boundary_segment_indices=[20],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=413,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=5.25, y=-10.0, z=0.0),
                end_position=Point3D(x=5.25, y=-50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[403],
        successor_lane_ids=[],
        road_id=hash("CrossIntersection_313"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane)
    
    # 右转出口车道 (Right Turn Exit Lanes)
    # 南向北右转出口（转向西向东）
    lane = Lane(
        lane_id=414,
        original_lane_id=-1,
        original_road_id=314,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=-5.25, y=-5.0, z=0.0),
            Point3D(x=-5.25, y=-25.0, z=0.0),
            Point3D(x=-5.25, y=-50.0, z=0.0),
        ],
        left_boundary_segment_indices=[10],
        right_boundary_segment_indices=[0],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=414,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-5.25, y=-5.0, z=0.0),
                end_position=Point3D(x=-5.25, y=-50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[404],
        successor_lane_ids=[],
        road_id=hash("CrossIntersection_314"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane)
    
    # 北向南右转出口（转向东向西）
    lane = Lane(
        lane_id=415,
        original_lane_id=1,
        original_road_id=315,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=5.25, y=5.0, z=0.0),
            Point3D(x=5.25, y=25.0, z=0.0),
            Point3D(x=5.25, y=50.0, z=0.0),
        ],
        left_boundary_segment_indices=[30],
        right_boundary_segment_indices=[20],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=415,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=5.25, y=5.0, z=0.0),
                end_position=Point3D(x=5.25, y=50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[405],
        successor_lane_ids=[],
        road_id=hash("CrossIntersection_315"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane)
    
    # 西向东右转出口（转向北向南）
    lane = Lane(
        lane_id=416,
        original_lane_id=1,
        original_road_id=316,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=-5.0, y=-5.25, z=0.0),
            Point3D(x=-25.0, y=-5.25, z=0.0),
            Point3D(x=-50.0, y=-5.25, z=0.0),
        ],
        left_boundary_segment_indices=[0],
        right_boundary_segment_indices=[10],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=416,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-5.0, y=-5.25, z=0.0),
                end_position=Point3D(x=-50.0, y=-5.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[406],
        successor_lane_ids=[],
        road_id=hash("CrossIntersection_316"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane)
    
    # 东向西右转出口（转向南向北）
    lane = Lane(
        lane_id=417,
        original_lane_id=-1,
        original_road_id=317,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="CrossIntersection",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=5.0, y=5.25, z=0.0),
            Point3D(x=25.0, y=5.25, z=0.0),
            Point3D(x=50.0, y=5.25, z=0.0),
        ],
        left_boundary_segment_indices=[20],
        right_boundary_segment_indices=[30],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=417,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=5.0, y=5.25, z=0.0),
                end_position=Point3D(x=50.0, y=5.25, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[407],
        successor_lane_ids=[],
        road_id=hash("CrossIntersection_317"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane)
    
    local_map.lanes.extend(lanes)
    
    # ==================== 添加交通信号灯 / Add Traffic Lights ====================
    # 四个方向的交通信号灯
    traffic_lights = []
    
    # 南向交通灯 (South)
    traffic_lights.append(TrafficLight(
        traffic_light_id=1,
        associated_lane_id=100,  # 关联最左侧车道
        position=Point3D(x=-12.0, y=-12.0, z=5.0),
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
    ))
    
    # 北向交通灯 (North)
    traffic_lights.append(TrafficLight(
        traffic_light_id=2,
        associated_lane_id=110,
        position=Point3D(x=12.0, y=12.0, z=5.0),
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
    ))
    
    # 西向交通灯 (West)
    traffic_lights.append(TrafficLight(
        traffic_light_id=3,
        associated_lane_id=120,
        position=Point3D(x=-12.0, y=-12.0, z=5.0),
        current_state=TrafficLightState(
            timestamp=datetime.now(),
            color=TrafficLightColor.YELLOW,
            shape=None,
            status=None,
            remaining_time=3.0
        ),
        distance_to_stop_line=2.0,
        associated_stop_line_id=0,
        light_type=None,
        confidence=1.0
    ))
    
    # 东向交通灯 (East)
    traffic_lights.append(TrafficLight(
        traffic_light_id=4,
        associated_lane_id=130,
        position=Point3D(x=12.0, y=12.0, z=5.0),
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
    ))
    
    local_map.traffic_lights.extend(traffic_lights)
    
    # ==================== 添加交通标志 / Add Traffic Signs ====================
    traffic_signs = []
    
    # 限速标志
    for lane_id in [100, 110, 120, 130]:
        traffic_signs.append(TrafficSign(
            traffic_sign_id=len(traffic_signs) + 1,
            associated_lane_id=lane_id,
            position=Point3D(
                x=-40.0 if lane_id in [100, 120] else 40.0,
                y=-40.0 if lane_id in [100, 120] else 40.0,
                z=3.0
            ),
            sign_type=TrafficSignType.SPEED_LIMIT,
            distance_to_sign=5.0,
            value=60.0,  # 60 km/h
            text_content="60",
            confidence=1.0,
            is_valid=True,
            valid_until=None
        ))
    
    local_map.traffic_signs.extend(traffic_signs)
    
    return local_map


def test_cross_intersection():
    """
    测试十字路口地图
    Test cross intersection map
    """
    print("=" * 60)
    print("测试十字路口地图")
    print("Testing Cross Intersection Map")
    print("=" * 60)
    
    # 创建十字路口地图
    local_map = create_cross_intersection_map()
    
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
            100: "南向北 (South to North)",
            101: "北向南 (North to South)",
            102: "西向东 (West to East)",
            103: "东向西 (East to West)",
            200: "交叉口内部-直行 (Junction Internal - Straight)",
            201: "交叉口内部-左转 (Junction Internal - Left Turn)",
            202: "交叉口内部-右转 (Junction Internal - Right Turn)",
            300: "南向北出口 (South to North Exit)",
            301: "北向南出口 (North to South Exit)",
            302: "西向东出口 (West to East Exit)",
            303: "东向西出口 (East to West Exit)",
            310: "南向北左转出口 (South to North Left Turn Exit)",
            311: "北向南左转出口 (North to South Left Turn Exit)",
            312: "西向东左转出口 (West to East Left Turn Exit)",
            313: "东向西左转出口 (East to West Left Turn Exit)",
            314: "南向北右转出口 (South to North Right Turn Exit)",
            315: "北向南右转出口 (North to South Right Turn Exit)",
            316: "西向东右转出口 (West to East Right Turn Exit)",
            317: "东向西右转出口 (East to West Right Turn Exit)",
        }.get(road_id, f"Road {road_id}")
        print(f"  {road_name}: {len(road_lanes)} lanes")
    
    # 统计转弯车道
    straight_junction_lanes = [lane for lane in local_map.lanes if lane.original_road_id == 200]
    left_turn_lanes = [lane for lane in local_map.lanes if lane.original_road_id == 201]
    right_turn_lanes = [lane for lane in local_map.lanes if lane.original_road_id == 202]
    
    print(f"\n转弯车道统计 / Turn Lane Statistics:")
    print(f"  直行车道 / Straight lanes: {len(straight_junction_lanes)}")
    print(f"  左转车道 / Left turn lanes: {len(left_turn_lanes)}")
    print(f"  右转车道 / Right turn lanes: {len(right_turn_lanes)}")
    
    # 显示交通信号灯状态
    print(f"\n交通信号灯状态 / Traffic Light States:")
    for light in local_map.traffic_lights:
        direction = {
            1: "南 (South)",
            2: "北 (North)",
            3: "西 (West)",
            4: "东 (East)",
        }.get(light.traffic_light_id, f"ID {light.traffic_light_id}")
        print(f"  {direction}: {light.current_state.color.name} (剩余 {light.current_state.remaining_time:.1f}s)")
    
    # 可视化地图
    print(f"\n[可视化] 生成地图可视化...")
    print(f"[Visualization] Generating map visualization...")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存可视化图片
    save_path = os.path.join(output_dir, "cross_intersection.png")
    
    # 使用API的可视化方法
    api.visualize(
        title="Cross Intersection Map (十字路口地图)",
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
    test_cross_intersection()
