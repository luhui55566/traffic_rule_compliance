#!/usr/bin/env python3
"""
HistoryManager - 历史轨迹管理子模块

负责管理自车历史轨迹数据。

主要功能:
    - 添加新的自车状态到历史轨迹
    - 限制历史轨迹长度
    - 当局部地图原点变化时重新计算历史轨迹的局部坐标
"""

import math
import logging
from typing import Dict, Any, List, Optional

# 导入通用数据类型
from common.ego_vehicle_state import EgoVehicleState as CommonEgoVehicleState

# 配置日志
logger = logging.getLogger(__name__)


class HistoryManager:
    """
    历史轨迹管理器
    
    负责管理自车历史轨迹数据，包括添加、截断和坐标重新计算。
    """
    
    # 默认历史轨迹最大长度
    DEFAULT_MAX_HISTORY_LENGTH = 150
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化历史轨迹管理器
        
        Args:
            config: 配置字典
        """
        # 历史轨迹缓存（存储统一格式的自车状态）
        self._ego_history: List[CommonEgoVehicleState] = []
        
        # 当前局部地图原点信息（用于检测原点变化）
        self._current_origin: Optional[tuple] = None
        
        # 地图节点引用（用于坐标转换）
        self._map_node: Any = None
        
        # 配置参数
        env_config = config.get('env_node', {})
        self.max_history_length = env_config.get('max_history_length', self.DEFAULT_MAX_HISTORY_LENGTH)
    
    def reset(self) -> None:
        """重置历史轨迹管理器"""
        self._ego_history = []
        self._current_origin = None
        self._map_node = None
    
    def set_map_node(self, map_node: Any) -> None:
        """
        设置地图节点引用
        
        Args:
            map_node: 地图节点实例
        """
        self._map_node = map_node
    
    def get_current_origin(self) -> Optional[tuple]:
        """
        获取当前局部地图原点
        
        Returns:
            Optional[tuple]: 当前原点 (x, y, heading)
        """
        return self._current_origin
    
    def set_current_origin(self, origin: Optional[tuple]) -> None:
        """
        设置当前局部地图原点
        
        Args:
            origin: 原点元组 (x, y, heading)
        """
        self._current_origin = origin
    
    def check_origin_changed(self, new_origin: Optional[tuple]) -> bool:
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
    
    def add_to_history(self, ego_state: CommonEgoVehicleState) -> None:
        """
        添加自车状态到历史轨迹
        
        Args:
            ego_state: 统一格式的自车状态
        """
        self._ego_history.append(ego_state)
        
        # 限制历史轨迹长度
        if len(self._ego_history) > self.max_history_length:
            self._ego_history = self._ego_history[-self.max_history_length:]
    
    def recalculate_history_local_states(self, new_origin: tuple, coordinate_converter: Any) -> None:
        """
        重新计算所有历史轨迹的local_state，使它们统一到当前局部坐标系下
        
        Args:
            new_origin: 新的局部地图原点 (x, y, heading)
            coordinate_converter: 坐标转换器实例
        """
        if self._map_node is None:
            logger.warning("无法重新计算历史轨迹：地图节点未设置")
            return
        
        for hist_state in self._ego_history:
            coordinate_converter.recalculate_local_state(hist_state, new_origin, self._map_node)
        
        logger.debug(f"已重新计算 {len(self._ego_history)} 个历史轨迹点的局部坐标")
    
    def get_history(self) -> List[CommonEgoVehicleState]:
        """
        获取历史轨迹
        
        Returns:
            List[CommonEgoVehicleState]: 历史自车状态列表
        """
        return list(self._ego_history)
    
    def get_history_length(self) -> int:
        """
        获取历史轨迹长度
        
        Returns:
            int: 历史轨迹长度
        """
        return len(self._ego_history)
    
    def clear_history(self) -> None:
        """清空历史轨迹"""
        self._ego_history = []
        logger.debug("历史轨迹已清空")
