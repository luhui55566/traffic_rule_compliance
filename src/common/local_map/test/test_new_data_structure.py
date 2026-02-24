"""
测试新的LocalMap数据结构
Test New LocalMap Data Structure

测试更新后的Lane类（使用新的ID字段结构）
Tests updated Lane class (using new ID field structure)
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
    BoundaryColor,  # 添加缺失的导入
    Header, LocalMapMetadata, create_empty_local_map
)
from common.local_map.local_map_api import LocalMapAPI


def create_demo_local_map() -> LocalMap:
    """
    创建演示用的局部地图（使用新的数据结构）
    Create demo local map (using new data structure)
    
    Returns:
        LocalMap: 演示局部地图 / Demo local map
    """
    ego_pose = Pose(
        position=Point3D(x=0.0, y=0.0, z=0.0),
        heading=0.0,
        pitch=0.0,
        roll=0.0
    )
    
    # 创建空的局部地图
    local_map = create_empty_local_map(ego_pose, 200.0)
    
    # 添加边界分段（共享边界）
    # Lane 1的右边界 = Lane 2的左边界
    shared_boundary = LaneBoundarySegment(
        segment_id=1,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=0.0, y=0.0, z=0.0),
            Point3D(x=10.0, y=0.0, z=0.0),
            Point3D(x=20.0, y=0.0, z=0.0),
            Point3D(x=30.0, y=0.0, z=0.0),
            Point3D(x=40.0, y=0.0, z=0.0),
            Point3D(x=50.0, y=0.0, z=0.0),
        ]
    )
    
    # Lane 1的左边界
    left_boundary_lane1 = LaneBoundarySegment(
        segment_id=2,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=0.0, y=-3.5, z=0.0),
            Point3D(x=10.0, y=-3.5, z=0.0),
            Point3D(x=20.0, y=-3.5, z=0.0),
            Point3D(x=30.0, y=-3.5, z=0.0),
            Point3D(x=40.0, y=-3.5, z=0.0),
            Point3D(x=50.0, y=-3.5, z=0.0),
        ]
    )
    
    # Lane 2的右边界
    right_boundary_lane2 = LaneBoundarySegment(
        segment_id=3,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=0.0, y=3.5, z=0.0),
            Point3D(x=10.0, y=3.5, z=0.0),
            Point3D(x=20.0, y=3.5, z=0.0),
            Point3D(x=30.0, y=3.5, z=0.0),
            Point3D(x=40.0, y=3.5, z=0.0),
            Point3D(x=50.0, y=3.5, z=0.0),
        ]
    )
    
    # 添加边界分段到地图
    local_map.boundary_segments.extend([
        shared_boundary,
        left_boundary_lane1,
        right_boundary_lane2
    ])
    
    # 创建测试车道 - 使用新的数据结构
    # Lane 1: 左侧车道（负车道ID）
    lane1 = Lane(
        lane_id=1,  # 全局唯一的车道ID
        # 原始ID字段 / Original ID fields
        original_lane_id=-1,  # XODR格式：负数表示左侧车道
        original_road_id=100,  # 原始道路ID
        original_junction_id=None,  # 不属于交叉口
        # 地图源信息 / Map source information
        map_source_type="XODR",  # 地图源类型
        map_source_id="Town10HD",  # 地图源标识
        # 车道属性 / Lane attributes
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=0.0, y=-1.75, z=0.0),
            Point3D(x=10.0, y=-1.75, z=0.0),
            Point3D(x=20.0, y=-1.75, z=0.0),
            Point3D(x=30.0, y=-1.75, z=0.0),
            Point3D(x=40.0, y=-1.75, z=0.0),
            Point3D(x=50.0, y=-1.75, z=0.0),
        ],
        left_boundary_segment_indices=[1],  # 索引1对应left_boundary_lane1
        right_boundary_segment_indices=[0],  # 索引0对应shared_boundary
        speed_limits=[
            SpeedLimitSegment(
                segment_id=1,
                speed_limit=16.67,  # 60 km/h = 16.67 m/s
                start_position=Point3D(x=0.0, y=-1.75, z=0.0),
                end_position=Point3D(x=50.0, y=-1.75, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=2,
        predecessor_lane_ids=[],
        successor_lane_ids=[3],  # 连接到转弯车道
        # XODR元数据 / XODR metadata
        road_id=hash("Town10HD_100"),  # 全局唯一道路ID
        junction_id=None,
        is_junction_lane=False
    )
    
    # Lane 2: 右侧车道（正车道ID）
    lane2 = Lane(
        lane_id=2,  # 全局唯一的车道ID
        # 原始ID字段 / Original ID fields
        original_lane_id=1,  # XODR格式：正数表示右侧车道
        original_road_id=100,  # 原始道路ID
        original_junction_id=None,  # 不属于交叉口
        # 地图源信息 / Map source information
        map_source_type="XODR",  # 地图源类型
        map_source_id="Town10HD",  # 地图源标识
        # 车道属性 / Lane attributes
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=0.0, y=1.75, z=0.0),
            Point3D(x=10.0, y=1.75, z=0.0),
            Point3D(x=20.0, y=1.75, z=0.0),
            Point3D(x=30.0, y=1.75, z=0.0),
            Point3D(x=40.0, y=1.75, z=0.0),
            Point3D(x=50.0, y=1.75, z=0.0),
        ],
        left_boundary_segment_indices=[0],  # 索引0对应shared_boundary
        right_boundary_segment_indices=[2],  # 索引2对应right_boundary_lane2
        speed_limits=[
            SpeedLimitSegment(
                segment_id=2,
                speed_limit=16.67,  # 60 km/h = 16.67 m/s
                start_position=Point3D(x=0.0, y=1.75, z=0.0),
                end_position=Point3D(x=50.0, y=1.75, z=0.0)
            )
        ],
        left_adjacent_lane_id=1,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[],
        successor_lane_ids=[4],  # 连接到转弯车道
        # XODR元数据 / XODR metadata
        road_id=hash("Town10HD_100"),  # 全局唯一道路ID
        junction_id=None,
        is_junction_lane=False
    )
    
    # Lane 3: 左转车道（交叉口内部）
    lane3 = Lane(
        lane_id=3,  # 全局唯一的车道ID
        # 原始ID字段 / Original ID fields
        original_lane_id=-1,
        original_road_id=200,  # 交叉口内部道路
        original_junction_id=664,  # 交叉口ID
        # 地图源信息 / Map source information
        map_source_type="XODR",
        map_source_id="Town10HD",
        # 车道属性 / Lane attributes
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=50.0, y=-1.75, z=0.0),
            Point3D(x=55.0, y=-1.75, z=0.0),
            Point3D(x=60.0, y=0.0, z=0.0),
            Point3D(x=60.0, y=5.0, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=3,
                speed_limit=8.33,  # 30 km/h = 8.33 m/s
                start_position=Point3D(x=50.0, y=-1.75, z=0.0),
                end_position=Point3D(x=60.0, y=5.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=4,
        predecessor_lane_ids=[1],
        successor_lane_ids=[5],
        # XODR元数据 / XODR metadata
        road_id=hash("Town10HD_200"),  # 全局唯一道路ID
        junction_id=hash("Town10HD_664"),  # 全局唯一交叉口ID
        is_junction_lane=True
    )
    
    # Lane 4: 右转车道（交叉口内部）
    lane4 = Lane(
        lane_id=4,  # 全局唯一的车道ID
        # 原始ID字段 / Original ID fields
        original_lane_id=1,
        original_road_id=200,  # 交叉口内部道路
        original_junction_id=664,  # 交叉口ID
        # 地图源信息 / Map source information
        map_source_type="XODR",
        map_source_id="Town10HD",
        # 车道属性 / Lane attributes
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=50.0, y=1.75, z=0.0),
            Point3D(x=55.0, y=1.75, z=0.0),
            Point3D(x=60.0, y=0.0, z=0.0),
            Point3D(x=60.0, y=-5.0, z=0.0),
        ],
        left_boundary_segment_indices=[],
        right_boundary_segment_indices=[],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=4,
                speed_limit=8.33,  # 30 km/h = 8.33 m/s
                start_position=Point3D(x=50.0, y=1.75, z=0.0),
                end_position=Point3D(x=60.0, y=-5.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=3,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[2],
        successor_lane_ids=[6],
        # XODR元数据 / XODR metadata
        road_id=hash("Town10HD_200"),  # 全局唯一道路ID
        junction_id=hash("Town10HD_664"),  # 全局唯一交叉口ID
        is_junction_lane=True
    )
    
    # 添加车道到地图
    local_map.lanes.extend([lane1, lane2, lane3, lane4])
    
    # 添加交通信号灯
    traffic_light = TrafficLight(
        traffic_light_id=1,
        associated_lane_id=1,  # 关联的车道ID（使用lane_id，不是lanelet_id）
        position=Point3D(x=48.0, y=-1.75, z=5.0),
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
    local_map.traffic_lights.append(traffic_light)
    
    # 添加交通标志（限速）
    traffic_sign = TrafficSign(
        traffic_sign_id=1,
        associated_lane_id=2,  # 关联的车道ID（使用lane_id，不是lanelet_id）
        position=Point3D(x=5.0, y=1.75, z=3.0),
        sign_type=TrafficSignType.SPEED_LIMIT,
        distance_to_sign=5.0,
        value=60.0,  # 60 km/h
        text_content="60",
        confidence=1.0,
        is_valid=True,
        valid_until=None
    )
    local_map.traffic_signs.append(traffic_sign)
    
    return local_map


def test_new_data_structure():
    """
    测试新的数据结构
    Test new data structure
    """
    print("=" * 60)
    print("测试新的LocalMap数据结构")
    print("Testing New LocalMap Data Structure")
    print("=" * 60)
    
    # 创建演示地图
    local_map = create_demo_local_map()
    
    # 创建API实例
    api = LocalMapAPI(local_map)
    
    # 测试1：验证车道的新字段
    print("\n[测试1] 验证车道的新字段")
    print("[Test 1] Verify new lane fields")
    for lane in local_map.lanes:
        print(f"\nLane ID: {lane.lane_id}")
        print(f"  原始ID / Original IDs:")
        print(f"    original_lane_id: {lane.original_lane_id}")
        print(f"    original_road_id: {lane.original_road_id}")
        print(f"    original_junction_id: {lane.original_junction_id}")
        print(f"  地图源 / Map Source:")
        print(f"    map_source_type: {lane.map_source_type}")
        print(f"    map_source_id: {lane.map_source_id}")
        print(f"  全局唯一ID / Globally Unique IDs:")
        print(f"    road_id: {lane.road_id}")
        print(f"    junction_id: {lane.junction_id}")
        print(f"  是否为交叉口车道 / Is Junction Lane: {lane.is_junction_lane}")
    
    # 测试2：验证关联元素使用associated_lane_id
    print("\n[测试2] 验证关联元素使用associated_lane_id")
    print("[Test 2] Verify associated elements use associated_lane_id")
    
    for light in local_map.traffic_lights:
        print(f"\nTrafficLight ID: {light.traffic_light_id}")
        print(f"  associated_lane_id: {light.associated_lane_id}")
        print(f"  Position: ({light.position.x}, {light.position.y}, {light.position.z})")
    
    for sign in local_map.traffic_signs:
        print(f"\nTrafficSign ID: {sign.traffic_sign_id}")
        print(f"  associated_lane_id: {sign.associated_lane_id}")
        print(f"  Type: {sign.sign_type.name}")
        print(f"  Value: {sign.value}")
    
    # 测试3：验证API查询功能
    print("\n[测试3] 验证API查询功能")
    print("[Test 3] Verify API query functionality")
    
    # 根据ID获取车道
    lane = api.get_lane_by_id(1)
    if lane:
        print(f"\n根据ID获取车道 / Get lane by ID:")
        print(f"  Lane ID: {lane.lane_id}")
        print(f"  Type: {lane.lane_type.name}")
        print(f"  Direction: {lane.lane_direction.name}")
        print(f"  Source: {lane.map_source_type} - {lane.map_source_id}")
    
    # 获取行驶车道
    driving_lanes = api.get_lanes_by_type(LaneType.DRIVING)
    print(f"\n行驶车道数量 / Number of driving lanes: {len(driving_lanes)}")
    
    # 获取交叉口内部车道
    junction_lanes = [lane for lane in local_map.lanes if lane.is_junction_lane]
    print(f"交叉口内部车道数量 / Number of junction lanes: {len(junction_lanes)}")
    
    # 测试4：可视化地图
    print("\n[测试4] 可视化地图")
    print("[Test 4] Visualize map")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存可视化图片
    save_path = os.path.join(output_dir, "demo_new_structure.png")
    
    # 使用API的可视化方法
    api.visualize(
        title="Demo Local Map (New Data Structure)",
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
    test_new_data_structure()
