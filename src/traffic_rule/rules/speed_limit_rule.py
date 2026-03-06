"""
限速规则

检测车辆是否超过道路限速。
"""

from typing import Optional
from pathlib import Path
import sys
import math

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from env_node.env_model import EnvironmentModel
from traffic_rule.models import Violation, ViolationLevel
from traffic_rule.rules.base import TrafficRule


class SpeedLimitRule(TrafficRule):
    """
    限速规则
    
    检测车辆是否超过道路限速。
    
    设计思路：
    1. 从 ego_lane_info 获取当前车道的限速
    2. 从 ego_state 获取当前车辆速度
    3. 比较速度与限速，判定是否违规
    
    参考：
    - env_model.ego_lane_info.speed_limit: 当前车道限速（m/s）
    - env_model.ego_state.global_state.linear_velocity: 当前速度向量
    """
    
    # 允许的超速阈值（m/s），约 3.6 km/h
    SPEED_TOLERANCE = 1.0  # m/s
    
    # 严重超速阈值（超过限速的百分比）
    MAJOR_OVERSPEED_THRESHOLD = 0.2  # 20%
    
    def _get_rule_name(self) -> str:
        return "限速规则"
    
    def _get_priority(self) -> int:
        return 90  # 高优先级
    
    def should_check(self, env_model: EnvironmentModel) -> bool:
        """
        规则自判断：是否需要检查限速
        
        检查条件：
        1. 有车辆状态
        2. 有车道信息
        3. 有限速信息
        """
        # 检查是否有车辆状态
        if env_model.ego_state is None:
            return False
        
        # 检查是否有车道信息
        if env_model.ego_lane_info is None:
            return False
        
        # 检查是否有限速信息
        if env_model.ego_lane_info.speed_limit is None:
            return False
        
        # 检查限速值是否有效
        if env_model.ego_lane_info.speed_limit <= 0:
            return False
        
        return True
    
    def check(self, env_model: EnvironmentModel) -> Optional[Violation]:
        """
        执行限速检查
        
        流程：
        1. 调用 should_check 判断是否需要检查
        2. 获取当前速度和限速
        3. 比较并判定违规
        """
        # 第二级过滤：规则自判断
        if not self.should_check(env_model):
            return None
        
        # 获取限速
        speed_limit = env_model.ego_lane_info.speed_limit  # m/s
        
        # 获取当前速度
        ego_state = env_model.ego_state
        if ego_state.global_state is None or ego_state.global_state.linear_velocity is None:
            return None
        
        velocity = ego_state.global_state.linear_velocity
        current_speed = velocity.magnitude()  # m/s
        
        # 计算超速量
        overspeed = current_speed - speed_limit
        
        # 判定是否超速（考虑容差）
        if overspeed > self.SPEED_TOLERANCE:
            # 计算超速百分比
            overspeed_percentage = overspeed / speed_limit
            
            # 判定违规等级
            if overspeed_percentage >= self.MAJOR_OVERSPEED_THRESHOLD:
                level = ViolationLevel.MAJOR
                level_str = "严重超速"
            else:
                level = ViolationLevel.MINOR
                level_str = "轻微超速"
            
            # 构建违规描述
            description = (
                f"{level_str}：当前速度 {current_speed*3.6:.1f} km/h，"
                f"限速 {speed_limit*3.6:.1f} km/h，"
                f"超速 {overspeed*3.6:.1f} km/h ({overspeed_percentage*100:.1f}%)"
            )
            
            return Violation(
                rule_id=self.id,
                rule_name=self.name,
                level=level,
                description=description,
                timestamp=env_model.timestamp,
                frame_index=env_model.frame_index,
                speed=current_speed,
                speed_limit=speed_limit,
                position={
                    'x': ego_state.local_state.position.x if ego_state.local_state else None,
                    'y': ego_state.local_state.position.y if ego_state.local_state else None,
                }
            )
        
        return None
