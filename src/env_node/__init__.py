"""
EnvNode - 环境模型节点模块

该模块负责将车辆状态数据和地图数据统一融合，输出标准化的环境模型。

主要类:
    - EnvNode: 环境模型节点
    - EnvironmentModel: 环境模型数据结构
    - EgoLaneInfo: 自车车道信息
    - EgoLaneContainmentType: 自车与车道边界的包含关系枚举

子模块:
    - CoordinateConverter: 坐标系转换器
    - HistoryManager: 历史轨迹管理器
    - LocalMapProcessor: 局部地图处理器

Usage:
    from src.env_node import EnvNode, EnvironmentModel, EgoLaneInfo
    
    env_node = EnvNode(config)
    env_node.init()
    env_model = env_node.process(veh_ego_state, local_map, map_node)
    
    # 获取自车车道信息
    if env_model.ego_lane_info:
        print(f"自车车道ID: {env_model.ego_lane_info.lane_id}")
        print(f"包含类型: {env_model.ego_lane_info.containment_type.name}")
"""

from .env_model import EnvironmentModel, EgoLaneInfo, EgoLaneContainmentType
from .env_node import EnvNode
from .coordinate_converter import CoordinateConverter
from .history_manager import HistoryManager
from .local_map_processor import LocalMapProcessor

__all__ = [
    'EnvNode',
    'EnvironmentModel',
    'EgoLaneInfo',
    'EgoLaneContainmentType',
    'CoordinateConverter',
    'HistoryManager',
    'LocalMapProcessor',
]
