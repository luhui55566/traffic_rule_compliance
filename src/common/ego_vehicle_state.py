"""
自车定位和运动姿态信息数据结构
Ego Vehicle State Data Structure

包含自车的位置、姿态、速度、加速度等关键信息
Supports both local coordinates and global coordinates (latitude, longitude).
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import math


@dataclass
class Point3D:
    """三维点 / Point3D"""
    x: float  # X坐标（米）/ X coordinate (meters)
    y: float  # Y坐标（米）/ Y coordinate (meters)
    z: float = 0.0  # Z坐标（米）/ Z coordinate (meters)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """转换为元组"""
        return (self.x, self.y, self.z)
    
    def distance_to(self, other: 'Point3D') -> float:
        """计算到另一个点的距离"""
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {'x': self.x, 'y': self.y, 'z': self.z}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Point3D':
        """从字典创建Point3D"""
        return cls(
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            z=data.get('z', 0.0)
        )


@dataclass
class Vector3D:
    """三维向量 / Vector3D"""
    x: float  # X分量 / X component
    y: float  # Y分量 / Y component
    z: float = 0.0  # Z分量 / Z component
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """转换为元组"""
        return (self.x, self.y, self.z)
    
    def magnitude(self) -> float:
        """计算向量模长"""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    
    def normalize(self) -> 'Vector3D':
        """归一化向量"""
        mag = self.magnitude()
        if mag == 0:
            return Vector3D(0.0, 0.0, 0.0)
        return Vector3D(self.x / mag, self.y / mag, self.z / mag)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {'x': self.x, 'y': self.y, 'z': self.z}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Vector3D':
        """从字典创建Vector3D"""
        return cls(
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            z=data.get('z', 0.0)
        )


@dataclass
class Quaternion:
    """四元数 / Quaternion"""
    x: float  # X分量 / X component
    y: float  # Y component
    z: float  # Z component
    w: float  # W分量 / W component
    
    def to_tuple(self) -> Tuple[float, float, float, float]:
        """转换为元组"""
        return (self.x, self.y, self.z, self.w)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {'x': self.x, 'y': self.y, 'z': self.z, 'w': self.w}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quaternion':
        """从字典创建Quaternion"""
        return cls(
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            z=data.get('z', 0.0),
            w=data.get('w', 1.0)
        )
    
    @classmethod
    def from_euler(cls, euler_angles: 'EulerAngles') -> 'Quaternion':
        """
        从欧拉角创建四元数
        
        Args:
            euler_angles: 欧拉角对象
        
        Returns:
            Quaternion: 四元数对象
        """
        roll = euler_angles.roll
        pitch = euler_angles.pitch
        yaw = euler_angles.yaw
        
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        
        return cls(x=x, y=y, z=z, w=w)
    
    def to_euler(self) -> 'EulerAngles':
        """
        转换为欧拉角
        
        Returns:
            EulerAngles: 欧拉角对象
        """
        # roll (x-axis rotation)
        sinr_cosp = 2 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1 - 2 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        # pitch (y-axis rotation)
        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)  # use 90 degrees if out of range
        else:
            pitch = math.asin(sinp)
        
        # yaw (z-axis rotation)
        siny_cosp = 2 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1 - 2 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return EulerAngles(roll=roll, pitch=pitch, yaw=yaw)


@dataclass
class EulerAngles:
    """欧拉角 / EulerAngles"""
    roll: float = 0.0  # 横滚角（弧度）/ Roll angle (radians)
    pitch: float = 0.0  # 俯仰角（弧度）/ Pitch angle (radians)
    yaw: float = 0.0  # 偏航角（弧度）/ Yaw angle (radians)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """转换为元组"""
        return (self.roll, self.pitch, self.yaw)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {'roll': self.roll, 'pitch': self.pitch, 'yaw': self.yaw}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EulerAngles':
        """从字典创建EulerAngles"""
        return cls(
            roll=data.get('roll', 0.0),
            pitch=data.get('pitch', 0.0),
            yaw=data.get('yaw', 0.0)
        )


@dataclass
class GlobalPosition:
    """全局位置（经纬度）/ Global Position (latitude, longitude)"""
    latitude: float  # 纬度（度）/ Latitude (degrees)
    longitude: float  # 经度（度）/ Longitude (degrees)
    altitude: float = 0.0  # 高度（米）/ Altitude (meters)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalPosition':
        """从字典创建GlobalPosition"""
        return cls(
            latitude=data.get('latitude', 0.0),
            longitude=data.get('longitude', 0.0),
            altitude=data.get('altitude', 0.0)
        )


@dataclass
class LocalCoordinateOrigin:
    """局部坐标系原点在全局坐标系中的位置"""
    global_position: GlobalPosition  # 全局位置
    orientation: Quaternion  # 姿态（四元数）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'global_position': self.global_position.to_dict(),
            'orientation': self.orientation.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocalCoordinateOrigin':
        """从字典创建LocalCoordinateOrigin"""
        return cls(
            global_position=GlobalPosition.from_dict(data.get('global_position', {})),
            orientation=Quaternion.from_dict(data.get('orientation', {}))
        )


@dataclass
class LocalState:
    """
    局部坐标系下的自车状态
    
    包含局部坐标、速度、加速度、角度、角速度
    """
    # 位置信息 / Position Information
    position: Point3D  # 局部坐标位置（x, y, z）
    origin: Optional[LocalCoordinateOrigin] = None  # 局部坐标系原点
    
    # 姿态信息 / Orientation Information
    orientation: Optional[EulerAngles] = None  # 欧拉角
    
    # 运动信息 / Motion Information
    linear_velocity: Optional[Vector3D] = None  # 线速度（x, y, z）
    linear_acceleration: Optional[Vector3D] = None  # 线加速度（x, y, z）
    angular_velocity: Optional[Vector3D] = None  # 角速度（x, y, z）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'position': self.position.to_dict()
        }
        
        if self.origin is not None:
            result['origin'] = self.origin.to_dict()
        
        if self.orientation is not None:
            result['orientation'] = self.orientation.to_dict()
        
        if self.linear_velocity is not None:
            result['linear_velocity'] = self.linear_velocity.to_dict()
        
        if self.linear_acceleration is not None:
            result['linear_acceleration'] = self.linear_acceleration.to_dict()
        
        if self.angular_velocity is not None:
            result['angular_velocity'] = self.angular_velocity.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocalState':
        """从字典创建LocalState"""
        origin_data = data.get('origin')
        orientation_data = data.get('orientation')
        linear_velocity_data = data.get('linear_velocity')
        linear_acceleration_data = data.get('linear_acceleration')
        angular_velocity_data = data.get('angular_velocity')
        
        return cls(
            position=Point3D.from_dict(data.get('position', {})),
            origin=LocalCoordinateOrigin.from_dict(origin_data) if origin_data else None,
            orientation=EulerAngles.from_dict(orientation_data) if orientation_data else None,
            linear_velocity=Vector3D.from_dict(linear_velocity_data) if linear_velocity_data else None,
            linear_acceleration=Vector3D.from_dict(linear_acceleration_data) if linear_acceleration_data else None,
            angular_velocity=Vector3D.from_dict(angular_velocity_data) if angular_velocity_data else None
        )


@dataclass
class GlobalState:
    """
    全局坐标系下的自车状态
    
    包含全局坐标（经纬度）、速度、加速度、角度（四元数）、角速度
    """
    # 位置信息 / Position Information
    position: GlobalPosition  # 全局位置（经纬度）
    
    # 姿态信息 / Orientation Information
    orientation: Optional[Quaternion] = None  # 姿态（四元数）
    euler_angles: Optional[EulerAngles] = None  # 欧拉角
    
    # 运动信息 / Motion Information
    linear_velocity: Optional[Vector3D] = None  # 线速度（x, y, z）
    linear_acceleration: Optional[Vector3D] = None  # 线加速度（x, y, z）
    angular_velocity: Optional[Vector3D] = None  # 角速度（x, y, z）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'position': self.position.to_dict()
        }
        
        if self.orientation is not None:
            result['orientation'] = self.orientation.to_dict()
        
        if self.euler_angles is not None:
            result['euler_angles'] = self.euler_angles.to_dict()
        
        if self.linear_velocity is not None:
            result['linear_velocity'] = self.linear_velocity.to_dict()
        
        if self.linear_acceleration is not None:
            result['linear_acceleration'] = self.linear_acceleration.to_dict()
        
        if self.angular_velocity is not None:
            result['angular_velocity'] = self.angular_velocity.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalState':
        """从字典创建GlobalState"""
        orientation_data = data.get('orientation')
        euler_angles_data = data.get('euler_angles')
        linear_velocity_data = data.get('linear_velocity')
        linear_acceleration_data = data.get('linear_acceleration')
        angular_velocity_data = data.get('angular_velocity')
        
        return cls(
            position=GlobalPosition.from_dict(data.get('position', {})),
            orientation=Quaternion.from_dict(orientation_data) if orientation_data else None,
            euler_angles=EulerAngles.from_dict(euler_angles_data) if euler_angles_data else None,
            linear_velocity=Vector3D.from_dict(linear_velocity_data) if linear_velocity_data else None,
            linear_acceleration=Vector3D.from_dict(linear_acceleration_data) if linear_acceleration_data else None,
            angular_velocity=Vector3D.from_dict(angular_velocity_data) if angular_velocity_data else None
        )


@dataclass
class EgoVehicleState:
    """
    自车定位和运动姿态信息
    
    Ego vehicle localization and motion state information
    
    包含局部和全局坐标系下的自车状态，两者可以并存
    """
    timestamp: float  # 时间戳（秒）
    local_state: Optional[LocalState] = None  # 局部坐标系状态
    global_state: Optional[GlobalState] = None  # 全局坐标系状态
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于序列化和存储"""
        result = {
            'timestamp': self.timestamp
        }
        
        if self.local_state is not None:
            result['local_state'] = self.local_state.to_dict()
        
        if self.global_state is not None:
            result['global_state'] = self.global_state.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EgoVehicleState':
        """从字典创建EgoVehicleState"""
        local_state_data = data.get('local_state')
        global_state_data = data.get('global_state')
        
        return cls(
            timestamp=data.get('timestamp', 0.0),
            local_state=LocalState.from_dict(local_state_data) if local_state_data else None,
            global_state=GlobalState.from_dict(global_state_data) if global_state_data else None
        )
    
    def has_local_state(self) -> bool:
        """是否有局部状态"""
        return self.local_state is not None
    
    def has_global_state(self) -> bool:
        """是否有全局状态"""
        return self.global_state is not None
    
    def __repr__(self) -> str:
        """字符串表示"""
        parts = [f"t={self.timestamp:.2f}"]
        
        if self.local_state is not None:
            pos = self.local_state.position
            yaw = self.local_state.orientation.yaw if self.local_state.orientation else 0.0
            vel_mag = self.local_state.linear_velocity.magnitude() if self.local_state.linear_velocity else 0.0
            parts.append(f"local=({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}, yaw={yaw:.2f}rad, vel={vel_mag:.2f}m/s)")
        
        if self.global_state is not None:
            pos = self.global_state.position
            yaw = self.global_state.euler_angles.yaw if self.global_state.euler_angles else 0.0
            vel_mag = self.global_state.linear_velocity.magnitude() if self.global_state.linear_velocity else 0.0
            parts.append(f"global=({pos.latitude:.6f}, {pos.longitude:.6f}, {pos.altitude:.2f}, yaw={yaw:.2f}rad, vel={vel_mag:.2f}m/s)")
        
        return f"EgoVehicleState({', '.join(parts)})"


# 工厂函数
def create_local_ego_state(
    timestamp: float,
    x: float,
    y: float,
    yaw: float,
    velocity_x: float,
    velocity_y: float = 0.0,
    z: float = 0.0,
    velocity_z: float = 0.0,
    roll: float = 0.0,
    pitch: float = 0.0,
    acceleration_x: float = 0.0,
    acceleration_y: float = 0.0,
    acceleration_z: float = 0.0,
    angular_velocity_x: float = 0.0,
    angular_velocity_y: float = 0.0,
    angular_velocity_z: float = 0.0,
    origin: Optional[LocalCoordinateOrigin] = None
) -> EgoVehicleState:
    """
    创建局部坐标系下的自车状态对象
    
    Args:
        timestamp: 时间戳（秒）
        x: X坐标
        y: Y坐标
        yaw: 偏航角（弧度）
        velocity_x: X方向速度（米/秒）
        velocity_y: Y方向速度（米/秒），默认为0.0
        z: Z坐标，默认为0.0
        velocity_z: Z方向速度（米/秒），默认为0.0
        roll: 横滚角（弧度），默认为0.0
        pitch: 俯仰角（弧度），默认为0.0
        acceleration_x: X方向加速度（米/秒²），默认为0.0
        acceleration_y: Y方向加速度（米/秒²），默认为0.0
        acceleration_z: Z方向加速度（米/秒²），默认为0.0
        angular_velocity_x: X方向角速度（弧度/秒），默认为0.0
        angular_velocity_y: Y方向角速度（弧度/秒），默认为0.0
        angular_velocity_z: Z方向角速度（弧度/秒），默认为0.0
        origin: 局部坐标系原点，默认为None
    
    Returns:
        EgoVehicleState: 自车状态对象
    """
    return EgoVehicleState(
        timestamp=timestamp,
        local_state=LocalState(
            position=Point3D(x=x, y=y, z=z),
            origin=origin,
            orientation=EulerAngles(roll=roll, pitch=pitch, yaw=yaw),
            linear_velocity=Vector3D(x=velocity_x, y=velocity_y, z=velocity_z),
            linear_acceleration=Vector3D(x=acceleration_x, y=acceleration_y, z=acceleration_z),
            angular_velocity=Vector3D(x=angular_velocity_x, y=angular_velocity_y, z=angular_velocity_z)
        )
    )


def create_global_ego_state(
    timestamp: float,
    latitude: float,
    longitude: float,
    yaw: float,
    velocity_x: float,
    velocity_y: float = 0.0,
    altitude: float = 0.0,
    velocity_z: float = 0.0,
    roll: float = 0.0,
    pitch: float = 0.0,
    acceleration_x: float = 0.0,
    acceleration_y: float = 0.0,
    acceleration_z: float = 0.0,
    angular_velocity_x: float = 0.0,
    angular_velocity_y: float = 0.0,
    angular_velocity_z: float = 0.0
) -> EgoVehicleState:
    """
    创建全局坐标系下的自车状态对象
    
    Args:
        timestamp: 时间戳（秒）
        latitude: 纬度（度）
        longitude: 经度（度）
        yaw: 偏航角（弧度）
        velocity_x: X方向速度（米/秒）
        velocity_y: Y方向速度（米/秒），默认为0.0
        altitude: 高度（米），默认为0.0
        velocity_z: Z方向速度（米/秒），默认为0.0
        roll: 横滚角（弧度），默认为0.0
        pitch: 俯仰角（弧度），默认为0.0
        acceleration_x: X方向加速度（米/秒²），默认为0.0
        acceleration_y: Y方向加速度（米/秒²），默认为0.0
        acceleration_z: Z方向加速度（米/秒²），默认为0.0
        angular_velocity_x: X方向角速度（弧度/秒），默认为0.0
        angular_velocity_y: Y方向角速度（弧度/秒），默认为0.0
        angular_velocity_z: Z方向角速度（弧度/秒），默认为0.0
    
    Returns:
        EgoVehicleState: 自车状态对象
    """
    euler_angles = EulerAngles(roll=roll, pitch=pitch, yaw=yaw)
    return EgoVehicleState(
        timestamp=timestamp,
        global_state=GlobalState(
            position=GlobalPosition(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude
            ),
            euler_angles=euler_angles,
            linear_velocity=Vector3D(x=velocity_x, y=velocity_y, z=velocity_z),
            linear_acceleration=Vector3D(x=acceleration_x, y=acceleration_y, z=acceleration_z),
            angular_velocity=Vector3D(x=angular_velocity_x, y=angular_velocity_y, z=angular_velocity_z)
        )
    )


def create_empty_ego_state() -> EgoVehicleState:
    """
    创建空的自车状态对象
    
    Returns:
        EgoVehicleState: 空的自车状态对象
    """
    return create_local_ego_state(
        timestamp=0.0,
        x=0.0,
        y=0.0,
        yaw=0.0,
        velocity_x=0.0
    )
