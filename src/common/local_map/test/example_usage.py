"""
LocalMap API使用示例
LocalMap API Usage Example

展示如何使用LocalMap API进行地图数据查询
Shows how to use LocalMap API for map data queries
"""

from datetime import datetime
from typing import List, Tuple, Optional

import sys
import os

# 添加上级目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from local_map_data import (
    LocalMap, Lane, TrafficLight, TrafficSign, Point3D, Pose,
    LaneType, LaneDirection, TrafficLightColor, TrafficSignType,
    create_empty_local_map
)
from local_map_api import LocalMapAPI


def create_sample_local_map() -> LocalMap:
    """
    创建示例局部地图
    Create sample local map
    
    Returns:
        LocalMap: 示例局部地图 / Sample local map
    """
    ego_pose = Pose(
        position=Point3D(x=0.0, y=0.0, z=0.0),
        heading=0.0,
        pitch=0.0,
        roll=0.0
    )
    
    local_map = create_empty_local_map(ego_pose, 200.0)
    
    # 这里可以添加示例数据
    # This is where sample data can be added
    
    return local_map


def example_lane_queries(api: LocalMapAPI):
    """
    车道查询示例
    Lane query examples
    
    Args:
        api: LocalMap API实例 / LocalMap API instance
    """
    print("=== 车道查询示例 / Lane Query Examples ===")
    
    # 1. 根据ID获取车道
    lane = api.get_lane_by_id(1)
    if lane:
        print(f"找到车道 / Found lane: ID={lane.lane_id}, 类型={lane.lane_type.name}")
    else:
        print("未找到ID为1的车道 / Lane with ID 1 not found")
    
    # 2. 根据类型获取车道
    driving_lanes = api.get_lanes_by_type(LaneType.DRIVING)
    print(f"行驶车道数量 / Number of driving lanes: {len(driving_lanes)}")
    
    # 3. 获取指定范围内的车道
    lanes_in_range = api.get_lanes_in_range((-50, 50), (-25, 25))
    print(f"范围内的车道数量 / Number of lanes in range: {len(lanes_in_range)}")
    
    # 4. 获取相邻车道
    left_lane, right_lane = api.get_adjacent_lanes(1)
    print(f"车道1的相邻车道 / Adjacent lanes of lane 1: 左侧={left_lane.lane_id if left_lane else None}, 右侧={right_lane.lane_id if right_lane else None}")
    
    # 5. 获取连接车道
    predecessors, successors = api.get_connected_lanes(1)
    print(f"车道1的连接车道 / Connected lanes of lane 1: 前继={[p.lane_id for p in predecessors]}, 后继={[s.lane_id for s in successors]}")
    
    # 6. 计算点到车道的距离
    test_point = Point3D(x=10.0, y=5.0, z=0.0)
    distance = api.calculate_distance_to_lane(test_point, 1)
    if distance is not None:
        print(f"点到车道1的距离 / Distance from point to lane 1: {distance:.2f}米 / meters")
    
    # 7. 查找最近的车道
    nearest_result = api.find_nearest_lane(test_point)
    if nearest_result:
        nearest_lane, nearest_distance = nearest_result
        print(f"最近的车道 / Nearest lane: ID={nearest_lane.lane_id}, 距离/distance={nearest_distance:.2f}米/meters")
    
    # 8. 检查点是否在车道内
    is_in_lane = api.is_point_in_lane(test_point, 1, tolerance=2.0)
    print(f"点是否在车道1内 / Is point in lane 1: {is_in_lane}")
    
    print()


def example_traffic_light_queries(api: LocalMapAPI):
    """
    交通信号灯查询示例
    Traffic light query examples
    
    Args:
        api: LocalMap API实例 / LocalMap API instance
    """
    print("=== 交通信号灯查询示例 / Traffic Light Query Examples ===")
    
    # 1. 根据ID获取交通信号灯
    light = api.get_traffic_light_by_id(1)
    if light:
        print(f"找到信号灯 / Found traffic light: ID={light.traffic_light_id}, 颜色={light.current_state.color.name}")
    else:
        print("未找到ID为1的信号灯 / Traffic light with ID 1 not found")
    
    # 2. 根据颜色获取交通信号灯
    red_lights = api.get_traffic_lights_by_color(TrafficLightColor.RED)
    print(f"红灯数量 / Number of red lights: {len(red_lights)}")
    
    # 3. 获取指定范围内的交通信号灯
    lights_in_range = api.get_traffic_lights_in_range((-50, 50), (-25, 25))
    print(f"范围内的信号灯数量 / Number of traffic lights in range: {len(lights_in_range)}")
    
    # 4. 获取指定距离内的交通信号灯
    test_point = Point3D(x=10.0, y=5.0, z=0.0)
    lights_within_distance = api.get_traffic_lights_within_distance(test_point, 100.0)
    print(f"100米内的信号灯数量 / Number of traffic lights within 100m: {len(lights_within_distance)}")
    
    print()


def example_traffic_sign_queries(api: LocalMapAPI):
    """
    交通标志查询示例
    Traffic sign query examples
    
    Args:
        api: LocalMap API实例 / LocalMap API instance
    """
    print("=== 交通标志查询示例 / Traffic Sign Query Examples ===")
    
    # 1. 根据ID获取交通标志
    sign = api.get_traffic_sign_by_id(1)
    if sign:
        print(f"找到交通标志 / Found traffic sign: ID={sign.traffic_sign_id}, 类型={sign.sign_type.name}")
    else:
        print("未找到ID为1的交通标志 / Traffic sign with ID 1 not found")
    
    # 2. 根据类型获取交通标志
    speed_limit_signs = api.get_traffic_signs_by_type(TrafficSignType.SPEED_LIMIT)
    print(f"限速标志数量 / Number of speed limit signs: {len(speed_limit_signs)}")
    
    # 3. 获取所有限速标志
    all_speed_limit_signs = api.get_speed_limit_signs()
    print(f"所有限速标志数量 / Number of all speed limit signs: {len(all_speed_limit_signs)}")
    
    # 4. 获取指定范围内的交通标志
    test_point = Point3D(x=10.0, y=5.0, z=0.0)
    signs_in_range = api.get_traffic_signs_in_range((-50, 50), (-25, 25))
    print(f"范围内的交通标志数量 / Number of traffic signs in range: {len(signs_in_range)}")
    
    # 5. 获取指定距离内的交通标志
    signs_within_distance = api.get_traffic_signs_within_distance(test_point, 100.0)
    print(f"100米内的交通标志数量 / Number of traffic signs within 100m: {len(signs_within_distance)}")
    
    print()


def example_statistics_and_validation(api: LocalMapAPI):
    """
    统计和验证示例
    Statistics and validation examples
    
    Args:
        api: LocalMap API实例 / LocalMap API instance
    """
    print("=== 统计和验证示例 / Statistics and Validation Examples ===")
    
    # 1. 获取统计信息
    stats = api.get_statistics()
    print("局部地图统计信息 / Local Map Statistics:")
    print(f"  时间戳 / Timestamp: {stats['timestamp']}")
    print(f"  地图范围 / Map Range: X={stats['map_range']['x']}, Y={stats['map_range']['y']}, Z={stats['map_range']['z']}")
    print(f"  自车位置 / Ego Vehicle Position: X={stats['ego_vehicle']['x']}, Y={stats['ego_vehicle']['y']}, 航向={stats['ego_vehicle']['heading']}")
    print(f"  元素数量 / Element Counts:")
    for key, value in stats['counts'].items():
        print(f"    {key}: {value}")
    
    # 2. 验证数据
    errors = api.validate_data()
    if errors:
        print("数据验证错误 / Data validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("数据验证通过 / Data validation passed")
    
    print()


def example_geometry_calculations(api: LocalMapAPI):
    """
    几何计算示例
    Geometry calculation examples
    
    Args:
        api: LocalMap API实例 / LocalMap API instance
    """
    print("=== 几何计算示例 / Geometry Calculation Examples ===")
    
    # 测试点
    test_points = [
        Point3D(x=10.0, y=5.0, z=0.0),
        Point3D(x=20.0, y=10.0, z=0.0),
        Point3D(x=30.0, y=15.0, z=0.0)
    ]
    
    for i, point in enumerate(test_points):
        print(f"测试点 {i+1} / Test Point {i+1}: ({point.x}, {point.y}, {point.z})")
        
        # 计算到车道的距离
        distance = api.calculate_distance_to_lane(point, 1)
        if distance is not None:
            print(f"  到车道1的距离 / Distance to lane 1: {distance:.2f}米/meters")
        
        # 查找最近的车道
        nearest_result = api.find_nearest_lane(point)
        if nearest_result:
            nearest_lane, nearest_distance = nearest_result
            print(f"  最近的车道 / Nearest lane: ID={nearest_lane.lane_id}, 距离/distance={nearest_distance:.2f}米/meters")
        
        # 检查是否在车道内
        is_in_lane = api.is_point_in_lane(point, 1, tolerance=2.0)
        print(f"  是否在车道1内 / Is in lane 1: {is_in_lane}")
        
        print()
    
    # 获取车道限速
    test_point_for_speed = Point3D(x=15.0, y=0.0, z=0.0)
    speed_limit = api.get_lane_speed_limit(1, test_point_for_speed)
    if speed_limit is not None:
        print(f"车道1在指定位置的限速 / Speed limit of lane 1 at specified position: {speed_limit:.2f}米/秒/m/s")
    else:
        print("车道1在指定位置无限速信息 / No speed limit info for lane 1 at specified position")


def main():
    """
    主函数
    Main function
    """
    print("LocalMap API使用示例 / LocalMap API Usage Example")
    print("=" * 50)
    
    # 创建示例局部地图
    local_map = create_sample_local_map()
    
    # 创建API实例
    api = LocalMapAPI(local_map)
    
    # 运行各种示例
    example_lane_queries(api)
    example_traffic_light_queries(api)
    example_traffic_sign_queries(api)
    example_statistics_and_validation(api)
    example_geometry_calculations(api)
    
    print("示例完成 / Examples completed")


if __name__ == "__main__":
    main()