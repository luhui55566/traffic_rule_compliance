"""
交规模块数据模型

定义违规、场景类型等核心数据结构。
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any


class ViolationLevel(Enum):
    """违规等级"""
    MINOR = auto()      # 轻微违规
    MAJOR = auto()      # 严重违规
    CRITICAL = auto()   # 致命违规


class SceneType(Enum):
    """场景类型"""
    UNKNOWN = auto()        # 未知
    INTERSECTION = auto()   # 路口
    HIGHWAY = auto()        # 高速公路
    URBAN = auto()          # 城市道路
    CROSSWALK = auto()      # 人行横道
    SCHOOL_ZONE = auto()    # 学校区域
    PARKING = auto()        # 停车场
    RESIDENTIAL = auto()    # 住宅区
    RAMP = auto()           # 匝道


@dataclass
class SceneResult:
    """场景识别结果"""
    scene_type: SceneType                          # 场景类型
    confidence: float = 1.0                        # 置信度
    scene_elements: Dict[str, Any] = field(default_factory=dict)  # 场景元素


@dataclass
class Violation:
    """违规记录"""
    rule_id: str                                   # 规则ID（类名）
    rule_name: str                                 # 规则名称
    level: ViolationLevel                          # 违规等级
    description: str                               # 违规描述
    timestamp: float                               # 时间戳（秒）
    frame_index: int = 0                           # 帧索引
    
    # 可选信息
    speed: Optional[float] = None                  # 速度（m/s）
    speed_limit: Optional[float] = None            # 限速（m/s）
    distance: Optional[float] = None               # 距离（米）
    position: Optional[Dict[str, float]] = None    # 位置信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'level': self.level.name,
            'description': self.description,
            'timestamp': self.timestamp,
            'frame_index': self.frame_index,
        }
        
        if self.speed is not None:
            result['speed'] = self.speed
        if self.speed_limit is not None:
            result['speed_limit'] = self.speed_limit
        if self.distance is not None:
            result['distance'] = self.distance
        if self.position is not None:
            result['position'] = self.position
            
        return result
    
    def __repr__(self) -> str:
        return f"Violation({self.rule_name}: {self.description})"
