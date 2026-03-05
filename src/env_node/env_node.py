#!/usr/bin/env python3
"""
EnvNode - 环境模型节点模块

该模块负责将车辆状态数据和地图数据统一融合，输出标准化的环境模型。

主要功能:
    - 坐标系转换: 将veh_status模块输出的自车状态转换为统一的EgoVehicleState格式
    - 局部地图处理: 将map_node模块生成的局部地图透传到环境模型，判定自车所在车道
    - 历史轨迹管理: 管理自车历史轨迹数据

局部坐标系说明:
    - 局部坐标系原点: 由LocalMapMetadata.ego_vehicle_x/y定义（在地图坐标系中的位置）
    - 局部坐标系X轴: 指向LocalMapMetadata.ego_vehicle_heading方向
    - 自车在局部坐标系中的位置需要根据当前地图坐标和原点坐标计算

Usage:
    from src.env_node import EnvNode
    
    env_node = EnvNode(config)
    env_node.init()
    env_model = env_node.process(veh_ego_state, local_map, map_node)
"""

import math
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

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

# 导入局部地图数据类型
from common.local_map.local_map_data import LocalMap, LocalMapMetadata

# 导入环境模型
from .env_model import EnvironmentModel, EgoLaneInfo, EgoLaneContainmentType

# 导入子模块
from .coordinate_converter import CoordinateConverter
from .history_manager import HistoryManager
from .local_map_processor import LocalMapProcessor

# 导入veh_status的数据类型（用于类型提示）
from veh_status.veh_status import EgoVehicleState as VehEgoVehicleState

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnvNode:
    """
    环境模型节点
    
    负责将车辆状态数据和地图数据统一融合，输出标准化的环境模型。
    
    坐标系说明:
        - 地图坐标系: 通过map_node的project_gps_with_heading将GPS投影得到
        - 局部坐标系: 以LocalMapMetadata中记录的位置为原点，X轴指向航向方向
        - 自车在局部坐标系中的位置 = 当前地图坐标 - 原点地图坐标（经旋转）
    
    Example:
        >>> env_node = EnvNode(config)
        >>> env_node.init()
        >>> env_model = env_node.process(veh_ego_state, local_map, map_node)
        >>> print(f"自车位置: {env_model.ego_state.local_state.position}")
        >>> print(f"自车车道: {env_model.ego_lane_info.lane_id if env_model.ego_lane_info else 'N/A'}")
    """
    
    # 历史轨迹最大长度（默认值，可被配置覆盖）
    MAX_HISTORY_LENGTH = 150
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化环境模型节点
        
        Args:
            config: 配置字典
        """
        self.config = config
        self._initialized: bool = False
        
        # 历史轨迹缓存（存储统一格式的自车状态）
        self._ego_history: List[CommonEgoVehicleState] = []
        
        # 当前局部地图原点信息（用于检测原点变化并重新计算历史轨迹）
        self._current_origin: Optional[tuple] = None
        
        # 地图节点引用（用于坐标转换）
        self._map_node: Any = None
        
        # 配置参数
        env_config = config.get('env_node', {})
        self.max_history_length = env_config.get('max_history_length', self.MAX_HISTORY_LENGTH)
        
        # 初始化子模块
        self._coordinate_converter = CoordinateConverter()
        self._history_manager = HistoryManager(config)
        self._local_map_processor = LocalMapProcessor(config)
    
    def init(self) -> bool:
        """
        初始化模块
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 清空历史轨迹
            self._ego_history = []
            self._current_origin = None
            self._map_node = None
            
            # 重置子模块
            self._history_manager.reset()
            self._local_map_processor.reset()
            
            self._initialized = True
            logger.info("EnvNode初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"EnvNode初始化失败: {e}")
            return False
    
    def process(
        self,
        veh_ego_state: VehEgoVehicleState,
        local_map: Optional[LocalMap],
        map_node: Any,
        frame_index: int = 0
    ) -> EnvironmentModel:
        """
        处理单帧数据
        
        将veh_status格式的自车状态转换为统一格式，并结合局部地图生成环境模型。
        
        当局部地图更新时（原点改变），会重新计算所有历史轨迹的local_state，
        使它们都统一到当前局部坐标系下。
        
        Args:
            veh_ego_state: veh_status模块输出的自车状态
            local_map: map_node模块生成的局部地图
            map_node: 地图节点实例（用于坐标转换）
            frame_index: 帧索引
            
        Returns:
            EnvironmentModel: 统一的环境模型
        """
        if not self._initialized:
            raise RuntimeError("EnvNode未初始化，请先调用init()")
        
        # 保存地图节点引用
        self._map_node = map_node
        self._history_manager.set_map_node(map_node)
        
        # 检测局部地图原点是否变化
        new_origin = self._get_local_map_origin_tuple(local_map)
        origin_changed = self._check_origin_changed(new_origin)
        
        # 如果原点变化，重新计算所有历史轨迹的local_state
        if origin_changed and self._ego_history:
            self._recalculate_history_local_states(new_origin)
        
        # 更新当前原点
        self._current_origin = new_origin
        
        # 转换自车状态格式
        common_ego_state = self.convert_ego_state(veh_ego_state, local_map, map_node)
        
        # 添加到历史轨迹
        self._add_to_history(common_ego_state)
        
        # 判定自车所在车道
        ego_lane_info = None
        if local_map is not None:
            ego_lane_info = self._find_ego_lane(common_ego_state, local_map)
        
        # 创建环境模型
        env_model = EnvironmentModel(
            timestamp=common_ego_state.timestamp,
            frame_index=frame_index,
            frame_name=veh_ego_state.frame_name,
            local_map=local_map,
            ego_state=common_ego_state,
            ego_history=list(self._ego_history),  # 复制历史轨迹
            ego_lane_info=ego_lane_info
        )
        
        logger.debug(f"处理帧 {frame_index}: {env_model}")
        return env_model
    
    def _get_local_map_origin_tuple(self, local_map: Optional[LocalMap]) -> Optional[tuple]:
        """
        获取局部地图原点的元组表示（用于比较）
        
        Args:
            local_map: 局部地图
            
        Returns:
            Optional[tuple]: (x, y, heading) 元组，如果没有局部地图则返回None
        """
        return self._local_map_processor.get_local_map_origin_tuple(local_map)
    
    def _check_origin_changed(self, new_origin: Optional[tuple]) -> bool:
        """
        检查局部地图原点是否变化
        
        Args:
            new_origin: 新的原点元组
            
        Returns:
            bool: 原点是否变化
        """
        if new_origin is None:
            return False
        if self._current_origin is None:
            return True
        return new_origin != self._current_origin
    
    def _recalculate_history_local_states(self, new_origin: tuple) -> None:
        """
        重新计算所有历史轨迹的local_state，使它们统一到当前局部坐标系下
        
        Args:
            new_origin: 新的局部地图原点 (x, y, heading)
        """
        if self._map_node is None:
            logger.warning("无法重新计算历史轨迹：地图节点未设置")
            return
        
        for hist_state in self._ego_history:
            self._coordinate_converter.recalculate_local_state(hist_state, new_origin, self._map_node)
        
        logger.debug(f"已重新计算 {len(self._ego_history)} 个历史轨迹点的局部坐标")
    
    def _find_ego_lane(
        self,
        ego_state: CommonEgoVehicleState,
        local_map: LocalMap
    ) -> Optional[EgoLaneInfo]:
        """
        查找自车所在车道并返回车道信息
        
        Args:
            ego_state: 自车状态（统一格式）
            local_map: 局部地图
            
        Returns:
            Optional[EgoLaneInfo]: 自车车道信息，如果未找到则返回None
        """
        result = self._local_map_processor.find_ego_lane(ego_state, local_map)
        
        if result.lane is None:
            return None
        
        lane = result.lane
        
        # 获取限速信息
        speed_limit = None
        if lane.max_speed_limits:
            speed_limit = lane.max_speed_limits[0]
        
        return EgoLaneInfo(
            lane_id=lane.lane_id,
            lane=lane,
            containment_type=result.containment_type,
            distance_to_centerline=result.distance_to_centerline,
            distance_to_left_boundary=result.distance_to_left_boundary,
            distance_to_right_boundary=result.distance_to_right_boundary,
            longitudinal_ratio=result.longitudinal_ratio,
            heading_diff=result.heading_diff,
            lane_type=lane.lane_type.name if lane.lane_type else None,
            speed_limit=speed_limit,
            left_lane_id=lane.left_adjacent_lane_id,
            right_lane_id=lane.right_adjacent_lane_id,
            original_road_id=lane.original_road_id,
            original_lane_id=lane.original_lane_id
        )
    
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
        return self._coordinate_converter.convert_ego_state(veh_ego_state, local_map, map_node)
    
    def _add_to_history(self, ego_state: CommonEgoVehicleState) -> None:
        """
        添加自车状态到历史轨迹
        
        Args:
            ego_state: 统一格式的自车状态
        """
        self._ego_history.append(ego_state)
        
        # 限制历史轨迹长度
        if len(self._ego_history) > self.max_history_length:
            self._ego_history = self._ego_history[-self.max_history_length:]
    
    def get_history(self) -> List[CommonEgoVehicleState]:
        """
        获取历史轨迹
        
        Returns:
            List[CommonEgoVehicleState]: 历史自车状态列表
        """
        return list(self._ego_history)
    
    def clear_history(self) -> None:
        """清空历史轨迹"""
        self._ego_history = []
        logger.debug("历史轨迹已清空")
    
    def get_history_length(self) -> int:
        """
        获取历史轨迹长度
        
        Returns:
            int: 历史轨迹长度
        """
        return len(self._ego_history)


def main():
    """主函数 - 演示模块使用"""
    import yaml
    from veh_status import VehStatusReader
    from map_node import MapNode
    
    # 加载配置
    config_path = Path(__file__).parent.parent.parent / "configs" / "traffic_rule_config.yaml"
    
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 初始化各模块
    env_node = EnvNode(config)
    if not env_node.init():
        print("EnvNode初始化失败")
        return
    
    # 初始化veh_status
    veh_reader = VehStatusReader(config)
    if not veh_reader.init():
        print("VehStatusReader初始化失败")
        return
    
    # 初始化map_node
    map_node = MapNode(config)
    if not map_node.init():
        print("MapNode初始化失败")
        return
    
    # 获取车辆状态
    ego_states = veh_reader.process()
    print(f"读取到 {len(ego_states)} 帧数据")
    
    # 处理第一帧
    if ego_states:
        first_state = ego_states[0]
        local_map = map_node.process(first_state)
        
        env_model = env_node.process(first_state, local_map, map_node, 0)
        
        print(f"\n环境模型:")
        print(f"  时间戳: {env_model.timestamp}")
        print(f"  帧名: {env_model.frame_name}")
        print(f"  自车状态: {env_model.ego_state}")
        print(f"  局部地图: {'有' if env_model.has_local_map() else '无'}")
        print(f"  历史长度: {env_model.get_history_length()}")
        
        # 打印局部坐标
        if env_model.ego_state and env_model.ego_state.local_state:
            pos = env_model.ego_state.local_state.position
            yaw = env_model.ego_state.local_state.orientation.yaw
            print(f"\n局部坐标:")
            print(f"  位置: ({pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f})")
            print(f"  航向: {yaw:.4f} rad ({math.degrees(yaw):.2f} deg)")
        
        # 打印自车车道信息
        if env_model.ego_lane_info:
            print(f"\n自车车道信息:")
            print(f"  车道ID: {env_model.ego_lane_info.lane_id}")
            print(f"  包含类型: {env_model.ego_lane_info.containment_type.name}")
            print(f"  到中心线距离: {env_model.ego_lane_info.distance_to_centerline:.2f}m")
        
        # 打印局部地图元数据
        if local_map is not None:
            print(f"\n局部地图元数据:")
            print(f"  地图范围: ({local_map.metadata.map_range_x}, {local_map.metadata.map_range_y})")
            print(f"  自车位置(地图坐标): ({local_map.metadata.ego_vehicle_x:.2f}, {local_map.metadata.ego_vehicle_y:.2f})")
            print(f"  自车航向: {local_map.metadata.ego_vehicle_heading:.4f} rad")


if __name__ == "__main__":
    main()
