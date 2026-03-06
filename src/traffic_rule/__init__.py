"""
交规判断模块

基于环境模型检测交通规则违规。

模块组成：
- ViolationDetector：模块入口（对外唯一接口）
- SceneIdentifier：场景识别器（内部组件）
- RuleManager：规则管理器（内部组件）
- TrafficRule：规则基类
- StatefulTrafficRule：有状态规则基类
"""

from .models import Violation, ViolationLevel, SceneType, SceneResult
from .detector import ViolationDetector
from .scene_identifier import SceneIdentifier
from .rule_manager import RuleManager
from .rules.base import TrafficRule, StatefulTrafficRule
from .rules.speed_limit_rule import SpeedLimitRule
from .rules.continuous_lane_change_rule import ContinuousLaneChangeRule

__all__ = [
    # 核心接口
    'ViolationDetector',
    
    # 内部组件（对外不暴露，但可供测试）
    'SceneIdentifier',
    'RuleManager',
    
    # 规则基类
    'TrafficRule',
    'StatefulTrafficRule',
    
    # 已实现规则
    'SpeedLimitRule',
    'ContinuousLaneChangeRule',
    
    # 数据模型
    'Violation',
    'ViolationLevel',
    'SceneType',
    'SceneResult',
]
