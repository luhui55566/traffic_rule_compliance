"""
自车定位和运动姿态信息数据结构测试用例
Ego Vehicle State Data Structure Test Cases
"""

import math
from ego_vehicle_state import (
    Point3D,
    Vector3D,
    Quaternion,
    EulerAngles,
    GlobalPosition,
    LocalCoordinateOrigin,
    LocalState,
    GlobalState,
    EgoVehicleState,
    create_local_ego_state,
    create_global_ego_state,
    create_empty_ego_state
)


def test_point3d():
    """测试Point3D"""
    print("Testing Point3D...")
    point = Point3D(x=1.0, y=2.0, z=3.0)
    assert point.to_tuple() == (1.0, 2.0, 3.0)
    
    other = Point3D(x=4.0, y=6.0, z=8.0)
    distance = point.distance_to(other)
    assert abs(distance - math.sqrt(3**2 + 4**2 + 5**2)) < 0.001
    
    # 测试字典转换
    point_dict = point.to_dict()
    point_from_dict = Point3D.from_dict(point_dict)
    assert point_from_dict.x == point.x
    assert point_from_dict.y == point.y
    assert point_from_dict.z == point.z
    
    print("  Point3D tests passed!")


def test_vector3d():
    """测试Vector3D"""
    print("Testing Vector3D...")
    vector = Vector3D(x=3.0, y=4.0, z=0.0)
    assert abs(vector.magnitude() - 5.0) < 0.001
    
    normalized = vector.normalize()
    assert abs(normalized.magnitude() - 1.0) < 0.001
    
    # 测试字典转换
    vector_dict = vector.to_dict()
    vector_from_dict = Vector3D.from_dict(vector_dict)
    assert vector_from_dict.x == vector.x
    assert vector_from_dict.y == vector.y
    assert vector_from_dict.z == vector.z
    
    print("  Vector3D tests passed!")


def test_euler_angles():
    """测试EulerAngles"""
    print("Testing EulerAngles...")
    euler = EulerAngles(roll=0.1, pitch=0.2, yaw=0.3)
    assert euler.to_tuple() == (0.1, 0.2, 0.3)
    
    # 测试字典转换
    euler_dict = euler.to_dict()
    euler_from_dict = EulerAngles.from_dict(euler_dict)
    assert abs(euler_from_dict.roll - euler.roll) < 0.001
    assert abs(euler_from_dict.pitch - euler.pitch) < 0.001
    assert abs(euler_from_dict.yaw - euler.yaw) < 0.001
    
    print("  EulerAngles tests passed!")


def test_quaternion():
    """测试Quaternion"""
    print("Testing Quaternion...")
    # 从欧拉角创建四元数
    euler = EulerAngles(roll=0.1, pitch=0.2, yaw=0.3)
    quat = Quaternion.from_euler(euler)
    euler_back = quat.to_euler()
    assert abs(euler_back.roll - euler.roll) < 0.001
    assert abs(euler_back.pitch - euler.pitch) < 0.001
    assert abs(euler_back.yaw - euler.yaw) < 0.001
    
    # 测试字典转换
    quat_dict = quat.to_dict()
    quat_from_dict = Quaternion.from_dict(quat_dict)
    assert abs(quat_from_dict.x - quat.x) < 0.001
    assert abs(quat_from_dict.y - quat.y) < 0.001
    assert abs(quat_from_dict.z - quat.z) < 0.001
    assert abs(quat_from_dict.w - quat.w) < 0.001
    
    print("  Quaternion tests passed!")


def test_local_state():
    """测试LocalState"""
    print("Testing LocalState...")
    local_state = LocalState(
        position=Point3D(x=10.0, y=20.0, z=0.0),
        orientation=EulerAngles(roll=0.1, pitch=0.2, yaw=0.3),
        linear_velocity=Vector3D(x=5.0, y=0.0, z=0.0),
        linear_acceleration=Vector3D(x=1.0, y=0.0, z=0.0),
        angular_velocity=Vector3D(x=0.0, y=0.0, z=0.1)
    )
    
    # 测试字典转换
    local_state_dict = local_state.to_dict()
    local_state_from_dict = LocalState.from_dict(local_state_dict)
    assert abs(local_state_from_dict.position.x - local_state.position.x) < 0.001
    assert abs(local_state_from_dict.orientation.yaw - local_state.orientation.yaw) < 0.001
    
    print("  LocalState tests passed!")


def test_global_state():
    """测试GlobalState"""
    print("Testing GlobalState...")
    euler = EulerAngles(roll=0.1, pitch=0.2, yaw=0.3)
    global_state = GlobalState(
        position=GlobalPosition(latitude=39.9, longitude=116.4, altitude=50.0),
        orientation=Quaternion.from_euler(euler),
        euler_angles=euler,
        linear_velocity=Vector3D(x=10.0, y=0.0, z=0.0),
        linear_acceleration=Vector3D(x=2.0, y=0.0, z=0.0),
        angular_velocity=Vector3D(x=0.0, y=0.0, z=0.2)
    )
    
    # 测试字典转换
    global_state_dict = global_state.to_dict()
    global_state_from_dict = GlobalState.from_dict(global_state_dict)
    assert abs(global_state_from_dict.position.latitude - global_state.position.latitude) < 0.001
    assert abs(global_state_from_dict.euler_angles.yaw - global_state.euler_angles.yaw) < 0.001
    
    print("  GlobalState tests passed!")


def test_ego_vehicle_state_local():
    """测试局部坐标系下的EgoVehicleState"""
    print("Testing EgoVehicleState (local)...")
    ego_state = create_local_ego_state(
        timestamp=100.0,
        x=10.0,
        y=20.0,
        yaw=0.3,
        velocity_x=5.0,
        velocity_y=0.0,
        z=0.0,
        velocity_z=0.0,
        roll=0.1,
        pitch=0.2,
        acceleration_x=1.0,
        acceleration_y=0.0,
        acceleration_z=0.0,
        angular_velocity_x=0.0,
        angular_velocity_y=0.0,
        angular_velocity_z=0.1
    )
    
    assert ego_state.has_local_state()
    assert not ego_state.has_global_state()
    
    # 测试字典转换
    ego_state_dict = ego_state.to_dict()
    ego_state_from_dict = EgoVehicleState.from_dict(ego_state_dict)
    assert ego_state_from_dict.has_local_state()
    assert not ego_state_from_dict.has_global_state()
    
    print(f"  EgoVehicleState (local): {ego_state}")
    print("  EgoVehicleState (local) tests passed!")


def test_ego_vehicle_state_global():
    """测试全局坐标系下的EgoVehicleState"""
    print("Testing EgoVehicleState (global)...")
    ego_state = create_global_ego_state(
        timestamp=100.0,
        latitude=39.9,
        longitude=116.4,
        yaw=0.3,
        velocity_x=10.0,
        velocity_y=0.0,
        altitude=50.0,
        velocity_z=0.0,
        roll=0.1,
        pitch=0.2,
        acceleration_x=2.0,
        acceleration_y=0.0,
        acceleration_z=0.0,
        angular_velocity_x=0.0,
        angular_velocity_y=0.0,
        angular_velocity_z=0.2
    )
    
    assert not ego_state.has_local_state()
    assert ego_state.has_global_state()
    
    # 测试字典转换
    ego_state_dict = ego_state.to_dict()
    ego_state_from_dict = EgoVehicleState.from_dict(ego_state_dict)
    assert not ego_state_from_dict.has_local_state()
    assert ego_state_from_dict.has_global_state()
    
    print(f"  EgoVehicleState (global): {ego_state}")
    print("  EgoVehicleState (global) tests passed!")


def test_ego_vehicle_state_both():
    """测试同时包含局部和全局状态的EgoVehicleState"""
    print("Testing EgoVehicleState (both local and global)...")
    
    # 创建局部坐标系原点
    origin = LocalCoordinateOrigin(
        global_position=GlobalPosition(latitude=39.9, longitude=116.4, altitude=50.0),
        orientation=Quaternion.from_euler(EulerAngles(roll=0.0, pitch=0.0, yaw=0.0))
    )
    
    # 创建局部状态
    local_state = LocalState(
        position=Point3D(x=10.0, y=20.0, z=0.0),
        origin=origin,
        orientation=EulerAngles(roll=0.0, pitch=0.0, yaw=0.3),
        linear_velocity=Vector3D(x=5.0, y=0.0, z=0.0)
    )
    
    # 创建全局状态
    euler = EulerAngles(roll=0.1, pitch=0.2, yaw=0.3)
    global_state = GlobalState(
        position=GlobalPosition(latitude=39.9, longitude=116.4, altitude=50.0),
        euler_angles=euler,
        linear_velocity=Vector3D(x=10.0, y=0.0, z=0.0)
    )
    
    # 创建同时包含局部和全局状态的自车状态
    ego_state = EgoVehicleState(
        timestamp=100.0,
        local_state=local_state,
        global_state=global_state
    )
    
    assert ego_state.has_local_state()
    assert ego_state.has_global_state()
    
    # 测试字典转换
    ego_state_dict = ego_state.to_dict()
    ego_state_from_dict = EgoVehicleState.from_dict(ego_state_dict)
    assert ego_state_from_dict.has_local_state()
    assert ego_state_from_dict.has_global_state()
    
    print(f"  EgoVehicleState (both): {ego_state}")
    print("  EgoVehicleState (both) tests passed!")


def test_empty_ego_state():
    """测试空的自车状态"""
    print("Testing empty EgoVehicleState...")
    ego_state = create_empty_ego_state()
    assert ego_state.has_local_state()
    assert not ego_state.has_global_state()
    
    print(f"  Empty EgoVehicleState: {ego_state}")
    print("  Empty EgoVehicleState tests passed!")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Running EgoVehicleState tests...")
    print("=" * 50)
    
    test_point3d()
    test_vector3d()
    test_euler_angles()
    test_quaternion()
    test_local_state()
    test_global_state()
    test_ego_vehicle_state_local()
    test_ego_vehicle_state_global()
    test_ego_vehicle_state_both()
    test_empty_ego_state()
    
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
