"""
LocalMap基本功能测试
LocalMap Basic Functionality Test

测试LocalMap数据结构和API的基本功能
Tests basic functionality of LocalMap data structures and API
"""

import sys
import os
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 直接导入模块，避免相对导入问题
import sys
import os

# 添加上级目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import local_map_data
import local_map_api

from local_map_data import (
    LocalMap, Lane, LaneBoundarySegment, SpeedLimitSegment,
    TrafficLight, TrafficLightState, TrafficSign,
    Point3D, Pose, LaneType, LaneDirection,
    TrafficLightColor, TrafficSignType, BoundaryType, BoundaryLineShape,
    Header, LocalMapMetadata, create_empty_local_map
)
from local_map_api import LocalMapAPI


def create_test_local_map() -> LocalMap:
    """
    创建测试用的局部地图
    Create test local map
    
    Returns:
        LocalMap: 测试局部地图 / Test local map
    """
    ego_pose = Pose(
        position=Point3D(x=0.0, y=0.0, z=0.0),
        heading=0.0,
        pitch=0.0,
        roll=0.0
    )
    
    # 创建空的局部地图
    local_map = create_empty_local_map(ego_pose, 200.0)
    
    # 添加测试车道
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
        speed_limits=[
            SpeedLimitSegment(
                segment_id=1,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=0.0, y=0.0, z=0.0),
                end_position=Point3D(x=40.0, y=0.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=2,
        right_adjacent_lane_id=None
    )
    
    lane2 = Lane(
        lane_id=2,
        lanelet_id=1002,
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=[
            Point3D(x=0.0, y=3.5, z=0.0),
            Point3D(x=10.0, y=3.5, z=0.0),
            Point3D(x=20.0, y=3.5, z=0.0),
            Point3D(x=30.0, y=3.5, z=0.0),
            Point3D(x=40.0, y=3.5, z=0.0),
        ],
        speed_limits=[
            SpeedLimitSegment(
                segment_id=2,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=0.0, y=3.5, z=0.0),
                end_position=Point3D(x=40.0, y=3.5, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=1
    )
    
    # 添加边界分段
    boundary1 = LaneBoundarySegment(
        segment_id=1,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=1,  # WHITE
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
    
    boundary2 = LaneBoundarySegment(
        segment_id=2,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=1,  # WHITE
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=0.0, y=-1.75, z=0.0),
            Point3D(x=10.0, y=-1.75, z=0.0),
            Point3D(x=20.0, y=-1.75, z=0.0),
            Point3D(x=30.0, y=-1.75, z=0.0),
            Point3D(x=40.0, y=-1.75, z=0.0),
        ]
    )
    
    # 添加交通信号灯
    traffic_light = TrafficLight(
        traffic_light_id=1,
        lanelet_id=2001,
        position=Point3D(x=50.0, y=-5.0, z=5.0),
        current_state=TrafficLightState(
            timestamp=datetime.now(),
            color=TrafficLightColor.RED,
            shape=1,  # CIRCLE
            status=2,  # SOLID_ON
            remaining_time=25.0
        ),
        light_type=1,  # VEHICLE
        confidence=0.95
    )
    
    # 添加交通标志
    traffic_sign = TrafficSign(
        traffic_sign_id=1,
        lanelet_id=3001,
        position=Point3D(x=25.0, y=5.0, z=3.0),
        sign_type=TrafficSignType.SPEED_LIMIT,
        value=60.0,
        text_content="60",
        confidence=0.98
    )
    
    # 设置车道边界引用
    lane1.left_boundary_segment_indices = [0]  # boundary1
    lane1.right_boundary_segment_indices = [1]  # boundary2
    lane2.left_boundary_segment_indices = [1]  # boundary2 (shared)
    lane2.right_boundary_segment_indices = []  # empty for simplicity
    
    # 添加到局部地图
    local_map.lanes.extend([lane1, lane2])
    local_map.boundary_segments.extend([boundary1, boundary2])
    local_map.traffic_lights.append(traffic_light)
    local_map.traffic_signs.append(traffic_sign)
    
    return local_map


def test_basic_functionality():
    """测试基本功能 / Test basic functionality"""
    print("开始LocalMap基本功能测试 / Starting LocalMap basic functionality test")
    print("=" * 60)
    
    # 创建测试地图
    test_map = create_test_local_map()
    api = LocalMapAPI(test_map)
    
    # 测试1: 车道查询
    print("\n测试1: 车道查询 / Test 1: Lane Queries")
    lane1 = api.get_lane_by_id(1)
    lane2 = api.get_lane_by_id(2)
    
    assert lane1 is not None, "应该能找到车道1 / Should find lane 1"
    assert lane2 is not None, "应该能找到车道2 / Should find lane 2"
    assert lane1.lane_type == LaneType.DRIVING, "车道1应该是行驶车道 / Lane 1 should be driving lane"
    assert lane1.left_adjacent_lane_id == 2, "车道1的左侧相邻车道应该是车道2 / Lane 1's left adjacent should be lane 2"
    assert lane2.right_adjacent_lane_id == 1, "车道2的右侧相邻车道应该是车道1 / Lane 2's right adjacent should be lane 1"
    
    print("✓ 车道查询测试通过 / Lane query test passed")
    
    # 测试2: 相邻车道查询
    print("\n测试2: 相邻车道查询 / Test 2: Adjacent Lane Queries")
    left_adj, right_adj = api.get_adjacent_lanes(1)
    assert left_adj is not None and left_adj.lane_id == 2, "车道1的左侧相邻应该是车道2 / Lane 1's left adjacent should be lane 2"
    assert right_adj is None, "车道1的右侧相邻应该为空 / Lane 1's right adjacent should be None"
    
    left_adj, right_adj = api.get_adjacent_lanes(2)
    assert left_adj is None, "车道2的左侧相邻应该为空 / Lane 2's left adjacent should be None"
    assert right_adj is not None and right_adj.lane_id == 1, "车道2的右侧相邻应该是车道1 / Lane 2's right adjacent should be lane 1"
    
    print("✓ 相邻车道查询测试通过 / Adjacent lane query test passed")
    
    # 测试3: 交通信号灯查询
    print("\n测试3: 交通信号灯查询 / Test 3: Traffic Light Queries")
    light = api.get_traffic_light_by_id(1)
    assert light is not None, "应该能找到信号灯1 / Should find traffic light 1"
    assert light.current_state.color == TrafficLightColor.RED, "信号灯应该是红色 / Traffic light should be red"
    
    red_lights = api.get_traffic_lights_by_color(TrafficLightColor.RED)
    assert len(red_lights) == 1, "应该有1个红灯 / Should have 1 red light"
    
    print("✓ 交通信号灯查询测试通过 / Traffic light query test passed")
    
    # 测试4: 交通标志查询
    print("\n测试4: 交通标志查询 / Test 4: Traffic Sign Queries")
    sign = api.get_traffic_sign_by_id(1)
    assert sign is not None, "应该能找到交通标志1 / Should find traffic sign 1"
    assert sign.sign_type == TrafficSignType.SPEED_LIMIT, "交通标志应该是限速标志 / Traffic sign should be speed limit sign"
    assert sign.value == 60.0, "限速值应该是60 / Speed limit value should be 60"
    
    speed_limit_signs = api.get_traffic_signs_by_type(TrafficSignType.SPEED_LIMIT)
    assert len(speed_limit_signs) == 1, "应该有1个限速标志 / Should have 1 speed limit sign"
    
    print("✓ 交通标志查询测试通过 / Traffic sign query test passed")
    
    # 测试5: 范围查询
    print("\n测试5: 范围查询 / Test 5: Range Queries")
    lanes_in_range = api.get_lanes_in_range((-10, 10), (-5, 5))
    assert len(lanes_in_range) >= 1, "范围内应该至少有1个车道 / Should have at least 1 lane in range"
    
    lights_in_range = api.get_traffic_lights_in_range((-10, 10), (-5, 5))
    assert len(lights_in_range) == 0, "范围内应该没有信号灯 / Should have no traffic lights in range"
    
    signs_in_range = api.get_traffic_signs_in_range((-10, 10), (-5, 5))
    assert len(signs_in_range) == 0, "范围内应该没有交通标志 / Should have no traffic signs in range"
    
    print("✓ 范围查询测试通过 / Range query test passed")
    
    # 测试6: 几何计算
    print("\n测试6: 几何计算 / Test 6: Geometry Calculations")
    test_point = Point3D(x=5.0, y=0.0, z=0.0)
    distance = api.calculate_distance_to_lane(test_point, 1)
    assert distance is not None, "应该能计算距离 / Should be able to calculate distance"
    assert abs(distance - 0.0) < 0.1, "点到车道1的距离应该接近0 / Distance from point to lane 1 should be close to 0"
    
    nearest_result = api.find_nearest_lane(test_point)
    assert nearest_result is not None, "应该能找到最近的车道 / Should find nearest lane"
    nearest_lane, nearest_distance = nearest_result
    assert nearest_lane.lane_id == 1, "最近的车道应该是车道1 / Nearest lane should be lane 1"
    assert abs(nearest_distance - 0.0) < 0.1, "最近距离应该接近0 / Nearest distance should be close to 0"
    
    is_in_lane = api.is_point_in_lane(test_point, 1, tolerance=2.0)
    assert is_in_lane, "点应该在车道1内 / Point should be in lane 1"
    
    print("✓ 几何计算测试通过 / Geometry calculation test passed")
    
    # 测试7: 限速查询
    print("\n测试7: 限速查询 / Test 7: Speed Limit Queries")
    speed_limit = api.get_lane_speed_limit(1, Point3D(x=15.0, y=0.0, z=0.0))
    assert speed_limit is not None, "应该能获取限速 / Should be able to get speed limit"
    assert abs(speed_limit - 16.67) < 0.1, "限速应该是16.67米/秒 / Speed limit should be 16.67 m/s"
    
    print("✓ 限速查询测试通过 / Speed limit query test passed")
    
    # 测试8: 统计信息
    print("\n测试8: 统计信息 / Test 8: Statistics")
    stats = api.get_statistics()
    assert stats['counts']['lanes'] == 2, "应该有2个车道 / Should have 2 lanes"
    assert stats['counts']['traffic_lights'] == 1, "应该有1个信号灯 / Should have 1 traffic light"
    assert stats['counts']['traffic_signs'] == 1, "应该有1个交通标志 / Should have 1 traffic sign"
    
    print("✓ 统计信息测试通过 / Statistics test passed")
    
    # 测试9: 数据验证
    print("\n测试9: 数据验证 / Test 9: Data Validation")
    errors = api.validate_data()
    assert len(errors) == 0, f"数据验证应该通过，但发现错误: {errors} / Data validation should pass, but found errors: {errors}"
    
    print("✓ 数据验证测试通过 / Data validation test passed")
    
    print("\n" + "=" * 60)
    print("所有测试通过！/ All tests passed!")
    return True


def test_integration_with_existing_systems():
    """测试与现有系统的集成 / Test integration with existing systems"""
    print("\n测试与现有系统的集成 / Testing integration with existing systems")
    print("=" * 60)
    
    # 这里可以添加与map_node和traffic_rule模块的集成测试
    # This is where integration tests with map_node and traffic_rule modules can be added
    
    print("✓ 集成测试占位符 / Integration test placeholder")
    print("注意：实际的集成测试需要与map_node和traffic_rule模块配合进行")
    print("Note: Actual integration tests need to be done with map_node and traffic_rule modules")
    
    return True


def main():
    """主函数 / Main function"""
    try:
        # 运行基本功能测试
        basic_test_passed = test_basic_functionality()
        
        # 运行集成测试
        integration_test_passed = test_integration_with_existing_systems()
        
        if basic_test_passed and integration_test_passed:
            print("\n🎉 所有测试通过！/ All tests passed!")
            return 0
        else:
            print("\n❌ 部分测试失败！/ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e} / Error occurred during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)