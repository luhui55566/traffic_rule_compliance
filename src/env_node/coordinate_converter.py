#!/usr/bin/env python3
"""
CoordinateConverter - 坐标系转换子模块

负责将veh_status模块输出的自车状态转换为统一的EgoVehicleState格式。

主要功能:
    - GPS坐标到地图坐标的投影
    - 地图坐标到局部坐标的转换
    - 速度、加速度等向量的坐标旋转
"""

import math
import logging
from typing import Dict, Any, Optional

# 导入通用数据类型
from common.ego_vehicle_state import (
    EgoVehicleState as CommonEgoVehicleState,
    LocalState,
    GlobalState,
    GlobalPosition,
    Point3D,
    Vector3D,
    EulerAngles,
    LocalCoordinateOrigin,
    Quaternion
)

# 导入veh_status的数据类型（用于类型提示）
from veh_status.veh_status import EgoVehicleState as VehEgoVehicleState

# 导入局部地图数据类型
from common.local_map.local_map_data import LocalMap

# 配置日志
logger = logging.getLogger(__name__)


class CoordinateConverter:
    """
    坐标系转换器
    
    负责将veh_status格式的自车状态转换为统一格式，并计算局部坐标。
    
    坐标系说明:
        - 地图坐标系: 通过map_node的project_gps_with_heading将GPS投影得到
        - 局部坐标系: 以LocalMapMetadata中记录的位置为原点，X轴指向航向方向
        - 自车在局部坐标系中的位置 = 当前地图坐标 - 原点地图坐标（经旋转）
    """
    
    def __init__(self):
        """初始化坐标系转换器"""
        pass
    
    def convert_ego_state(
        self,
        veh_ego_state: VehEgoVehicleState,
        local_map: Optional[LocalMap],
        map_node: Any
    ) -> CommonEgoVehicleState:
        """
        将veh_status的EgoVehicleState转换为common的EgoVehicleState
        
        数据映射关系:
        - timestamp -> timestamp
        - latitude, longitude, altitude -> global_state.position
        - heading, pitch, roll -> global_state.euler_angles
        - velocity_east, velocity_north, velocity_up -> global_state.linear_velocity
        - acc_x, acc_y, acc_z -> global_state.linear_acceleration
        - gyro_x, gyro_y, gyro_z -> global_state.angular_velocity
        - 局部坐标: 根据当前地图坐标和LocalMapMetadata中的原点计算
        
        Args:
            veh_ego_state: veh_status模块输出的自车状态
            local_map: 局部地图（包含局部坐标系原点信息）
            map_node: 地图节点实例
            
        Returns:
            CommonEgoVehicleState: 统一格式的自车状态
        """
        # 构建全局状态
        global_state = GlobalState(
            position=GlobalPosition(
                latitude=veh_ego_state.latitude,
                longitude=veh_ego_state.longitude,
                altitude=veh_ego_state.altitude
            ),
            euler_angles=EulerAngles(
                roll=veh_ego_state.roll,
                pitch=veh_ego_state.pitch,
                yaw=veh_ego_state.heading
            ),
            linear_velocity=Vector3D(
                x=veh_ego_state.velocity_east,
                y=veh_ego_state.velocity_north,
                z=veh_ego_state.velocity_up
            ),
            linear_acceleration=Vector3D(
                x=veh_ego_state.acc_x,
                y=veh_ego_state.acc_y,
                z=veh_ego_state.acc_z
            ),
            angular_velocity=Vector3D(
                x=veh_ego_state.gyro_x,
                y=veh_ego_state.gyro_y,
                z=veh_ego_state.gyro_z
            )
        )
        
        # 构建局部状态（根据当前坐标和局部地图原点计算）
        local_state = self._build_local_state(veh_ego_state, local_map, map_node)
        
        # 创建统一格式的自车状态
        # 时间戳转换：veh_status的timestamp通常是纳秒级，需要转换为秒
        timestamp = float(veh_ego_state.timestamp)
        if timestamp > 1e12:  # 纳秒级时间戳
            timestamp = timestamp / 1e9
        
        common_ego_state = CommonEgoVehicleState(
            timestamp=timestamp,
            local_state=local_state,
            global_state=global_state
        )
        
        return common_ego_state
    
    def _build_local_state(
        self,
        veh_ego_state: VehEgoVehicleState,
        local_map: Optional[LocalMap],
        map_node: Any
    ) -> LocalState:
        """
        构建局部坐标系下的自车状态
        
        计算方法:
        1. 获取当前帧的地图坐标 (current_map_x, current_map_y, current_heading)
        2. 从LocalMapMetadata获取局部坐标系原点 (origin_map_x, origin_map_y, origin_heading)
        3. 计算相对位置: dx = current_map_x - origin_map_x, dy = current_map_y - origin_map_y
        4. 旋转到局部坐标系: local_x = dx*cos(-origin_heading) - dy*sin(-origin_heading)
                           local_y = dx*sin(-origin_heading) + dy*cos(-origin_heading)
        5. 计算相对航向: local_yaw = current_heading - origin_heading
        
        Args:
            veh_ego_state: veh_status模块输出的自车状态
            local_map: 局部地图
            map_node: 地图节点实例
            
        Returns:
            LocalState: 局部坐标系下的自车状态
        """
        # 获取当前帧的地图坐标
        current_coord = self._get_map_coordinates(veh_ego_state, map_node)
        current_map_x = current_coord['x']
        current_map_y = current_coord['y']
        current_map_z = current_coord['z']
        current_heading = current_coord['heading']
        
        # 获取局部坐标系原点
        origin_coord = self._get_local_map_origin(local_map, current_coord)
        origin_map_x = origin_coord['x']
        origin_map_y = origin_coord['y']
        origin_map_z = origin_coord['z']
        origin_heading = origin_coord['heading']
        
        # 计算相对于原点的偏移（在地图坐标系中）
        dx = current_map_x - origin_map_x
        dy = current_map_y - origin_map_y
        dz = current_map_z - origin_map_z
        
        # 旋转到局部坐标系（以origin_heading为基准）
        # 旋转角度为 -origin_heading，将地图坐标系旋转到局部坐标系
        cos_h = math.cos(-origin_heading)
        sin_h = math.sin(-origin_heading)
        
        local_x = dx * cos_h - dy * sin_h
        local_y = dx * sin_h + dy * cos_h
        local_z = dz
        
        # 计算局部坐标系中的航向
        local_yaw = current_heading - origin_heading
        # 归一化到 [-pi, pi]
        while local_yaw > math.pi:
            local_yaw -= 2 * math.pi
        while local_yaw < -math.pi:
            local_yaw += 2 * math.pi
        
        # 构建局部位置
        local_position = Point3D(x=local_x, y=local_y, z=local_z)
        
        # 构建局部姿态
        local_orientation = EulerAngles(roll=veh_ego_state.roll, pitch=veh_ego_state.pitch, yaw=local_yaw)
        
        # 速度转换到局部坐标系
        # 在地图坐标系中: velocity_east(X), velocity_north(Y)
        # 需要旋转到局部坐标系
        vel_east = veh_ego_state.velocity_east
        vel_north = veh_ego_state.velocity_north
        local_vel_x = vel_east * cos_h - vel_north * sin_h
        local_vel_y = vel_east * sin_h + vel_north * cos_h
        
        local_linear_velocity = Vector3D(
            x=local_vel_x,
            y=local_vel_y,
            z=veh_ego_state.velocity_up
        )
        
        # 加速度转换到局部坐标系
        acc_x = veh_ego_state.acc_x
        acc_y = veh_ego_state.acc_y
        local_acc_x = acc_x * cos_h - acc_y * sin_h
        local_acc_y = acc_x * sin_h + acc_y * cos_h
        
        local_linear_acceleration = Vector3D(
            x=local_acc_x,
            y=local_acc_y,
            z=veh_ego_state.acc_z
        )
        
        # 角速度（航向角速度需要转换）
        # TODO: 完整的角速度转换需要考虑坐标系旋转
        local_angular_velocity = Vector3D(
            x=veh_ego_state.gyro_x,
            y=veh_ego_state.gyro_y,
            z=veh_ego_state.gyro_z
        )
        
        # 构建局部坐标系原点信息
        origin = None
        if local_map is not None and hasattr(local_map, 'metadata'):
            metadata = local_map.metadata
            origin = LocalCoordinateOrigin(
                global_position=GlobalPosition(
                    latitude=veh_ego_state.latitude,  # 简化处理
                    longitude=veh_ego_state.longitude,
                    altitude=veh_ego_state.altitude
                ),
                orientation=Quaternion.from_euler(EulerAngles(
                    roll=0.0,
                    pitch=0.0,
                    yaw=metadata.ego_vehicle_heading
                ))
            )
        
        # 构建局部状态
        local_state = LocalState(
            position=local_position,
            origin=origin,
            orientation=local_orientation,
            linear_velocity=local_linear_velocity,
            linear_acceleration=local_linear_acceleration,
            angular_velocity=local_angular_velocity
        )
        
        return local_state
    
    def _get_map_coordinates(
        self,
        veh_ego_state: VehEgoVehicleState,
        map_node: Any
    ) -> Dict[str, float]:
        """
        获取当前帧在地图坐标系中的坐标
        
        Args:
            veh_ego_state: veh_status模块输出的自车状态
            map_node: 地图节点实例
            
        Returns:
            Dict[str, float]: 包含 x, y, z, heading 的坐标字典
        """
        if map_node is not None:
            return map_node.project_gps_with_heading(
                veh_ego_state.latitude,
                veh_ego_state.longitude,
                veh_ego_state.altitude if hasattr(veh_ego_state, 'altitude') else 0.0,
                veh_ego_state.heading
            )
        else:
            # 如果没有map_node，返回默认值
            return {
                'x': veh_ego_state.longitude,
                'y': veh_ego_state.latitude,
                'z': veh_ego_state.altitude,
                'heading': math.radians(veh_ego_state.heading)
            }
    
    def _get_local_map_origin(
        self,
        local_map: Optional[LocalMap],
        current_coord: Dict[str, float]
    ) -> Dict[str, float]:
        """
        获取局部坐标系原点在地图坐标系中的位置
        
        如果local_map为None，则使用当前坐标作为原点（此时局部坐标为0,0,0）
        
        Args:
            local_map: 局部地图
            current_coord: 当前帧的地图坐标
            
        Returns:
            Dict[str, float]: 包含 x, y, z, heading 的原点坐标字典
        """
        if local_map is not None and hasattr(local_map, 'metadata'):
            metadata = local_map.metadata
            return {
                'x': metadata.ego_vehicle_x,
                'y': metadata.ego_vehicle_y,
                'z': 0.0,  # metadata中没有记录z
                'heading': metadata.ego_vehicle_heading
            }
        else:
            # 如果没有局部地图，使用当前坐标作为原点
            return current_coord
    
    def recalculate_local_state(
        self,
        ego_state: CommonEgoVehicleState,
        new_origin: tuple,
        map_node: Any
    ) -> None:
        """
        重新计算单个自车状态的local_state
        
        Args:
            ego_state: 自车状态（会被原地修改）
            new_origin: 新的局部地图原点 (x, y, heading)
            map_node: 地图节点实例
        """
        if ego_state.global_state is None:
            return
        
        origin_map_x, origin_map_y, origin_heading = new_origin
        
        # 旋转参数：将地图坐标系旋转到局部坐标系
        cos_h = math.cos(-origin_heading)
        sin_h = math.sin(-origin_heading)
        
        global_pos = ego_state.global_state.position
        global_euler = ego_state.global_state.euler_angles
        
        # 将GPS坐标投影到地图坐标系
        try:
            map_coord = map_node.project_gps_with_heading(
                global_pos.latitude,
                global_pos.longitude,
                global_pos.altitude,
                math.degrees(global_euler.yaw)
            )
            current_map_x = map_coord['x']
            current_map_y = map_coord['y']
            current_map_z = map_coord['z']
            current_heading = map_coord['heading']
        except Exception as e:
            logger.warning(f"重新计算局部坐标失败: {e}")
            return
        
        # 计算相对于当前原点的偏移
        dx = current_map_x - origin_map_x
        dy = current_map_y - origin_map_y
        dz = current_map_z  # 原点z设为0
        
        # 旋转到局部坐标系
        local_x = dx * cos_h - dy * sin_h
        local_y = dx * sin_h + dy * cos_h
        local_z = dz
        
        # 计算局部坐标系中的航向
        local_yaw = current_heading - origin_heading
        # 归一化到 [-pi, pi]
        while local_yaw > math.pi:
            local_yaw -= 2 * math.pi
        while local_yaw < -math.pi:
            local_yaw += 2 * math.pi
        
        # 更新local_state
        if ego_state.local_state is not None:
            ego_state.local_state.position.x = local_x
            ego_state.local_state.position.y = local_y
            ego_state.local_state.position.z = local_z
            ego_state.local_state.orientation.yaw = local_yaw
            
            # 速度转换到局部坐标系
            vel = ego_state.global_state.linear_velocity
            if vel is not None:
                local_vel_x = vel.x * cos_h - vel.y * sin_h
                local_vel_y = vel.x * sin_h + vel.y * cos_h
                ego_state.local_state.linear_velocity.x = local_vel_x
                ego_state.local_state.linear_velocity.y = local_vel_y
            
            # 加速度转换到局部坐标系
            acc = ego_state.global_state.linear_acceleration
            if acc is not None:
                local_acc_x = acc.x * cos_h - acc.y * sin_h
                local_acc_y = acc.x * sin_h + acc.y * cos_h
                ego_state.local_state.linear_acceleration.x = local_acc_x
                ego_state.local_state.linear_acceleration.y = local_acc_y
