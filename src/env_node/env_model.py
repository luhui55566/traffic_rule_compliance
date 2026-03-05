#!/usr/bin/env python3
"""
Environment Model - 环境模型数据结构

定义统一的环境模型数据结构，包含局部地图、自车状态、历史轨迹和自车车道信息。

Usage:
    from src.env_node.env_model import EnvironmentModel, EgoLaneInfo
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import IntEnum

# 导入通用数据类型
from common.ego_vehicle_state import EgoVehicleState
from common.local_map.local_map_data import LocalMap, Lane


class EgoLaneContainmentType(IntEnum):
    """自车与车道边界的包含关系枚举"""
    UNKNOWN = 0                # 未知（无法判定）
    CENTER_INSIDE = 1          # 自车中心点在车道边界内，但轮廓部分在边界外
    FULLY_INSIDE = 2           # 车辆外轮廓都在边界内
    CENTER_OUTSIDE = 3         # 自车中心点在车道边界外


@dataclass
class EgoLaneInfo:
    """
    自车车道信息
    
    包含自车所在车道的详细信息和包含关系。
    """
    # 车道ID
    lane_id: Optional[int] = None
    
    # 车道对象（可选，用于获取更多车道信息）
    lane: Optional[Lane] = None
    
    # 包含关系类型
    containment_type: EgoLaneContainmentType = EgoLaneContainmentType.UNKNOWN
    
    # 距离信息
    distance_to_centerline: float = float('inf')       # 到中心线的距离（米）
    distance_to_left_boundary: float = float('inf')    # 到左边界的距离（米）
    distance_to_right_boundary: float = float('inf')   # 到右边界的距离（米）
    
    # 位置信息
    longitudinal_ratio: float = 0.0                    # 纵向位置比例（0-1）
    heading_diff: float = 0.0                          # 航向差（弧度）
    
    # 车道属性
    lane_type: Optional[str] = None                    # 车道类型
    speed_limit: Optional[float] = None                # 限速（m/s）
    
    # 相邻车道ID
    left_lane_id: Optional[int] = None
    right_lane_id: Optional[int] = None
    
    # 原始地图信息
    original_road_id: Optional[int] = None
    original_lane_id: Optional[int] = None


@dataclass
class EnvironmentModel:
    """
    环境模型
    
    统一的环境数据容器，包含当前帧的所有环境信息。
    """
    # 时间信息
    timestamp: float  # 时间戳（秒）
    frame_index: int = 0  # 帧索引
    frame_name: str = ""  # 帧文件名
    
    # 地图数据
    local_map: Optional[LocalMap] = None  # 局部地图
    
    # 自车状态
    ego_state: Optional[EgoVehicleState] = None  # 当前帧自车状态（统一格式）
    
    # 历史轨迹
    ego_history: List[EgoVehicleState] = field(default_factory=list)  # 历史自车状态列表
    
    # 自车车道信息
    ego_lane_info: Optional[EgoLaneInfo] = None  # 自车所在车道信息
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp,
            'frame_index': self.frame_index,
            'frame_name': self.frame_name,
            'local_map': self.local_map.to_dict() if self.local_map else None,
            'ego_state': self.ego_state.to_dict() if self.ego_state else None,
            'ego_history': [state.to_dict() for state in self.ego_history],
            'ego_lane_info': self._ego_lane_info_to_dict(),
            'created_at': self.created_at
        }
    
    def _ego_lane_info_to_dict(self) -> Optional[Dict[str, Any]]:
        """将ego_lane_info转换为字典"""
        if self.ego_lane_info is None:
            return None
        
        info = self.ego_lane_info
        return {
            'lane_id': info.lane_id,
            'containment_type': info.containment_type.name,
            'distance_to_centerline': info.distance_to_centerline,
            'distance_to_left_boundary': info.distance_to_left_boundary,
            'distance_to_right_boundary': info.distance_to_right_boundary,
            'longitudinal_ratio': info.longitudinal_ratio,
            'heading_diff': info.heading_diff,
            'lane_type': info.lane_type,
            'speed_limit': info.speed_limit,
            'left_lane_id': info.left_lane_id,
            'right_lane_id': info.right_lane_id
        }
    
    def has_local_map(self) -> bool:
        """是否有局部地图"""
        return self.local_map is not None
    
    def has_ego_state(self) -> bool:
        """是否有自车状态"""
        return self.ego_state is not None
    
    def has_ego_lane_info(self) -> bool:
        """是否有自车车道信息"""
        return self.ego_lane_info is not None and self.ego_lane_info.lane_id is not None
    
    def get_history_length(self) -> int:
        """获取历史轨迹长度"""
        return len(self.ego_history)
    
    def __repr__(self) -> str:
        """字符串表示"""
        parts = [
            f"timestamp={self.timestamp:.2f}",
            f"frame={self.frame_index}"
        ]
        
        if self.ego_state is not None:
            if self.ego_state.local_state is not None:
                pos = self.ego_state.local_state.position
                parts.append(f"pos=({pos.x:.2f}, {pos.y:.2f})")
            if self.ego_state.global_state is not None:
                gp = self.ego_state.global_state.position
                parts.append(f"gps=({gp.latitude:.6f}, {gp.longitude:.6f})")
        
        if self.local_map is not None:
            parts.append(f"roads={len(self.local_map.roads)}")
        
        parts.append(f"history={len(self.ego_history)}")
        
        if self.ego_lane_info is not None and self.ego_lane_info.lane_id is not None:
            parts.append(f"ego_lane={self.ego_lane_info.lane_id}")
        
        return f"EnvironmentModel({', '.join(parts)})"
