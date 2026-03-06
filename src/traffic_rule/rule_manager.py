"""
规则管理器

管理所有规则，维护场景-规则映射表，实现第一级过滤（查表）。
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from traffic_rule.models import SceneType
from traffic_rule.rules.base import TrafficRule
from traffic_rule.rules.speed_limit_rule import SpeedLimitRule
from traffic_rule.rules.continuous_lane_change_rule import ContinuousLaneChangeRule


class RuleManager:
    """
    规则管理器 - 场景层过滤
    
    管理所有规则，维护场景-规则映射表，实现第一级过滤（查表）。
    """
    
    def __init__(self):
        """初始化规则管理器"""
        self.rules: Dict[str, TrafficRule] = {}
        self.scene_rules_map: Dict[SceneType, List[str]] = {}
        
        # 注册规则
        self._register_rules()
        
        # 构建场景-规则映射表
        self._build_scene_rules_map()
    
    def _register_rules(self):
        """注册所有规则"""
        # 限速规则
        speed_limit_rule = SpeedLimitRule()
        self.rules[speed_limit_rule.id] = speed_limit_rule
        
        # 连续变道规则
        lane_change_rule = ContinuousLaneChangeRule()
        self.rules[lane_change_rule.id] = lane_change_rule
        
        # TODO: 后续添加更多规则
    
    def _build_scene_rules_map(self):
        """
        构建场景-规则映射表
        
        配置方式：为每个场景指定适用的规则列表
        """
        # 通用规则（适用于所有场景）
        common_rules = [
            'SpeedLimitRule',           # 限速规则
        ]
        
        # 道路类场景规则
        road_rules = common_rules + [
            'ContinuousLaneChangeRule',  # 连续变道规则
        ]
        
        # 场景-规则映射
        self.scene_rules_map = {
            SceneType.URBAN: road_rules,           # 城市道路
            SceneType.HIGHWAY: road_rules,         # 高速公路
            SceneType.RESIDENTIAL: road_rules,     # 住宅区
            SceneType.RAMP: road_rules,            # 匝道
            SceneType.INTERSECTION: common_rules,  # 路口（连续变道在路口可能允许）
            SceneType.CROSSWALK: common_rules,     # 人行横道
            SceneType.SCHOOL_ZONE: common_rules,   # 学校区域
            SceneType.PARKING: common_rules,       # 停车场
            SceneType.UNKNOWN: common_rules,       # 未知场景
        }
    
    def get_rules_to_check(self, scene_type: SceneType) -> List[TrafficRule]:
        """
        获取候选规则列表（第一级过滤：查表）
        
        Args:
            scene_type: 场景类型
            
        Returns:
            List[TrafficRule]: 候选规则列表
        """
        # 查表得到规则ID列表
        rule_ids = self.scene_rules_map.get(scene_type, [])
        
        # 转换为规则对象列表
        candidate_rules = [
            self.rules[rid] 
            for rid in rule_ids 
            if rid in self.rules
        ]
        
        return candidate_rules
    
    def get_rule_by_id(self, rule_id: str) -> Optional[TrafficRule]:
        """
        根据规则ID获取规则对象
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Optional[TrafficRule]: 规则对象，如果不存在则返回None
        """
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> List[TrafficRule]:
        """
        获取所有规则
        
        Returns:
            List[TrafficRule]: 所有规则列表
        """
        return list(self.rules.values())
