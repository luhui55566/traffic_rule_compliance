"""
场景识别器

基于 EnvironmentModel 识别当前场景类型。
"""

from typing import Dict, Any
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from env_node.env_model import EnvironmentModel
from traffic_rule.models import SceneType, SceneResult
from common.local_map.local_map_data import LaneType, IntersectionType


class SceneIdentifier:
    """
    场景识别器
    
    基于 EnvironmentModel 识别当前场景类型，为第一级过滤提供依据。
    """
    
    def identify_scene(self, env_model: EnvironmentModel) -> SceneResult:
        """
        识别当前场景类型
        
        Args:
            env_model: 环境模型
            
        Returns:
            SceneResult: 场景识别结果
        """
        # 默认场景
        scene_type = SceneType.URBAN
        scene_elements = {}
        
        # 检查是否有局部地图
        if env_model.local_map is None:
            return SceneResult(
                scene_type=SceneType.UNKNOWN,
                confidence=0.0,
                scene_elements={'error': 'No local map available'}
            )
        
        local_map = env_model.local_map
        
        # 1. 检查是否在交叉口
        if self._check_intersection(env_model):
            scene_type = SceneType.INTERSECTION
            scene_elements['intersection'] = True
        
        # 2. 检查是否在学校区域
        elif self._check_school_zone(env_model):
            scene_type = SceneType.SCHOOL_ZONE
            scene_elements['school_zone'] = True
        
        # 3. 检查是否在人行横道
        elif self._check_crosswalk(env_model):
            scene_type = SceneType.CROSSWALK
            scene_elements['crosswalk'] = True
        
        # 4. 检查是否在高速公路（通过道路类型判断）
        elif self._check_highway(env_model):
            scene_type = SceneType.HIGHWAY
            scene_elements['highway'] = True
        
        # 5. 检查是否在匝道
        elif self._check_ramp(env_model):
            scene_type = SceneType.RAMP
            scene_elements['ramp'] = True
        
        # 6. 默认城市道路
        else:
            scene_type = SceneType.URBAN
            scene_elements['urban'] = True
        
        return SceneResult(
            scene_type=scene_type,
            confidence=1.0,
            scene_elements=scene_elements
        )
    
    def _check_intersection(self, env_model: EnvironmentModel) -> bool:
        """
        检查是否在交叉口
        
        Args:
            env_model: 环境模型
            
        Returns:
            bool: 是否在交叉口
        """
        if env_model.local_map is None:
            return False
        
        # 检查车道是否关联交叉口
        if env_model.ego_lane_info and env_model.ego_lane_info.lane:
            lane = env_model.ego_lane_info.lane
            if lane.junction_id is not None or lane.is_junction_lane:
                return True
        
        # 检查局部地图中的交叉口
        for intersection in env_model.local_map.intersections:
            # 简单判断：自车位置在交叉口多边形内
            # 实际实现需要点在多边形内的算法
            if intersection.intersection_type != IntersectionType.UNKNOWN:
                return True
        
        return False
    
    def _check_school_zone(self, env_model: EnvironmentModel) -> bool:
        """
        检查是否在学校区域
        
        Args:
            env_model: 环境模型
            
        Returns:
            bool: 是否在学校区域
        """
        if env_model.local_map is None:
            return False
        
        # 检查交通标志
        for sign in env_model.local_map.traffic_signs:
            # 检查是否有学校区域标志
            if sign.sign_type.name == 'SCHOOL_ZONE':
                return True
        
        return False
    
    def _check_crosswalk(self, env_model: EnvironmentModel) -> bool:
        """
        检查是否在人行横道附近
        
        Args:
            env_model: 环境模型
            
        Returns:
            bool: 是否在人行横道附近
        """
        if env_model.local_map is None:
            return False
        
        # 检查车道是否关联人行横道
        if env_model.ego_lane_info and env_model.ego_lane_info.lane:
            if len(env_model.ego_lane_info.lane.associated_crosswalk_ids) > 0:
                return True
        
        # 检查局部地图中的人行横道
        if len(env_model.local_map.crosswalks) > 0:
            # TODO: 计算自车到人行横道的距离
            return True
        
        return False
    
    def _check_highway(self, env_model: EnvironmentModel) -> bool:
        """
        检查是否在高速公路
        
        Args:
            env_model: 环境模型
            
        Returns:
            bool: 是否在高速公路
        """
        if env_model.local_map is None:
            return False
        
        # 检查道路类型
        for road in env_model.local_map.roads:
            if road.road_type and 'highway' in road.road_type.lower():
                return True
        
        # 检查车道类型
        if env_model.ego_lane_info and env_model.ego_lane_info.lane:
            # 高速公路通常限速较高（>80 km/h）
            if env_model.ego_lane_info.speed_limit:
                speed_limit_kmh = env_model.ego_lane_info.speed_limit * 3.6
                if speed_limit_kmh >= 80:
                    return True
        
        return False
    
    def _check_ramp(self, env_model: EnvironmentModel) -> bool:
        """
        检查是否在匝道
        
        Args:
            env_model: 环境模型
            
        Returns:
            bool: 是否在匝道
        """
        if env_model.ego_lane_info and env_model.ego_lane_info.lane:
            lane = env_model.ego_lane_info.lane
            # 检查车道类型
            if lane.lane_type in [LaneType.ENTRY, LaneType.EXIT, LaneType.MERGE]:
                return True
        
        return False
