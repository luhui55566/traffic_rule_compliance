"""
连续变道规则

检测车辆是否在短时间内连续变道（基于压线量判断，不依赖车道ID）。
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import math

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from env_node.env_model import EnvironmentModel, EgoLaneContainmentType
from traffic_rule.models import Violation, ViolationLevel
from traffic_rule.rules.base import StatefulTrafficRule


class ContinuousLaneChangeRule(StatefulTrafficRule):
    """
    连续变道规则
    
    检测车辆是否在短时间内连续变道。
    
    设计思路（参考论文MTL方法，基于压线量判断）：
    1. 不依赖车道ID变化（因为ID会变）
    2. 使用 containment_type 判断车辆与车道边界的关系：
       - FULLY_INSIDE: 完全在车道内
       - CENTER_INSIDE: 中心在车道内，但轮廓部分在边界外（压线）
       - CENTER_OUTSIDE: 中心在车道边界外（跨线/变道中）
    3. 检测压线-跨线-压线-完全进入的变道过程
    4. 记录变道事件，检查时间窗口内的变道次数
    
    参考：
    - env_model.ego_lane_info.containment_type: 包含关系类型
    - env_model.ego_lane_info.distance_to_left_boundary: 到左边界距离
    - env_model.ego_lane_info.distance_to_right_boundary: 到右边界距离
    """
    
    # 判定时间窗口（秒）
    TIME_WINDOW = 10.0  # 10秒内不得连续同方向变道
    
    # 判定连续变道次数阈值
    LANE_CHANGE_THRESHOLD = 2  # 10秒内变道2次以上视为连续变道
    
    # 压线距离阈值（米）
    LINE_PRESSING_THRESHOLD = 0.3  # 距离边界小于0.3米视为压线
    
    # 最小变道时间间隔（秒），避免误判
    MIN_LANE_CHANGE_INTERVAL = 1.0
    
    def _get_rule_name(self) -> str:
        return "连续变道规则"
    
    def _get_priority(self) -> int:
        return 70
    
    def should_check(self, env_model: EnvironmentModel) -> bool:
        """
        规则自判断：是否需要检查连续变道
        
        检查条件：
        1. 有车辆状态
        2. 有车道信息
        """
        if env_model.ego_state is None:
            return False
        
        if env_model.ego_lane_info is None:
            return False
        
        return True
    
    def check(self, env_model: EnvironmentModel) -> Optional[Violation]:
        """
        执行连续变道检查
        
        流程（基于压线量判断）：
        1. 检测当前车辆与车道边界的关系
        2. 识别变道事件（压线 -> 跨线 -> 压线 -> 完全进入）
        3. 记录变道历史
        4. 检查时间窗口内的变道次数
        """
        # 第二级过滤：规则自判断
        if not self.should_check(env_model):
            return None
        
        current_time = env_model.timestamp
        
        # 获取当前状态
        containment_type = env_model.ego_lane_info.containment_type
        dist_to_left = env_model.ego_lane_info.distance_to_left_boundary
        dist_to_right = env_model.ego_lane_info.distance_to_right_boundary
        
        # 判断当前是否在压线或跨线
        is_pressing_line = self._is_pressing_line(containment_type, dist_to_left, dist_to_right)
        
        # 获取上一次的状态
        last_state = self.get_state('last_state')
        last_time = self.get_state('last_time', current_time)
        
        # 检测变道事件
        lane_change_event = self._detect_lane_change(
            last_state, 
            containment_type, 
            is_pressing_line,
            dist_to_left,
            dist_to_right,
            current_time,
            last_time
        )
        
        # 如果检测到变道事件，记录到历史
        if lane_change_event is not None:
            # 避免短时间内重复记录
            recent_changes = self.get_recent_history(self.MIN_LANE_CHANGE_INTERVAL, current_time)
            if len(recent_changes) == 0:
                self.record_history(current_time, lane_change_event)
                
                # 判断变道方向
                direction = lane_change_event.get('direction', 'unknown')
                
                # 更新状态
                self.update_state('last_lane_change_time', current_time)
                self.update_state('last_lane_change_direction', direction)
        
        # 更新当前状态
        self.update_state('last_state', {
            'containment_type': containment_type,
            'is_pressing_line': is_pressing_line,
            'dist_to_left': dist_to_left,
            'dist_to_right': dist_to_right,
        })
        self.update_state('last_time', current_time)
        
        # 检查时间窗口内的变道次数
        recent_changes = self.get_recent_history(self.TIME_WINDOW, current_time)
        
        # 判定是否连续变道
        if len(recent_changes) >= self.LANE_CHANGE_THRESHOLD:
            # 检查是否同方向连续变道
            directions = [change['data'].get('direction', 'unknown') for change in recent_changes]
            
            # 如果大部分是同方向，判定为连续变道
            if self._is_same_direction(directions):
                # 清理过期历史
                self.clear_old_history(self.TIME_WINDOW, current_time)
                
                # 构建违规描述
                direction_str = "左侧" if directions[0] == 'left' else "右侧" if directions[0] == 'right' else "混合方向"
                
                return Violation(
                    rule_id=self.id,
                    rule_name=self.name,
                    level=ViolationLevel.MINOR,
                    description=f"连续变道：{self.TIME_WINDOW:.0f}秒内{len(recent_changes)}次变道（{direction_str}）",
                    timestamp=current_time,
                    frame_index=env_model.frame_index,
                )
        
        # 定期清理过期历史（防止内存泄漏）
        if len(self._state_history) > 100:
            self.clear_old_history(self.TIME_WINDOW, current_time)
        
        return None
    
    def _is_pressing_line(
        self, 
        containment_type: EgoLaneContainmentType,
        dist_to_left: float,
        dist_to_right: float
    ) -> bool:
        """
        判断是否压线
        
        Args:
            containment_type: 包含关系类型
            dist_to_left: 到左边界距离
            dist_to_right: 到右边界距离
            
        Returns:
            bool: 是否压线
        """
        # 方法1：基于包含关系类型
        if containment_type == EgoLaneContainmentType.CENTER_INSIDE:
            return True  # 中心在车道内，但轮廓在边界外，说明压线
        
        # 方法2：基于距离判断
        if dist_to_left < self.LINE_PRESSING_THRESHOLD:
            return True
        
        if dist_to_right < self.LINE_PRESSING_THRESHOLD:
            return True
        
        return False
    
    def _detect_lane_change(
        self,
        last_state: Optional[Dict[str, Any]],
        current_containment: EgoLaneContainmentType,
        is_pressing_line: bool,
        dist_to_left: float,
        dist_to_right: float,
        current_time: float,
        last_time: float
    ) -> Optional[Dict[str, Any]]:
        """
        检测变道事件
        
        变道过程：
        1. 完全在车道内（FULLY_INSIDE）
        2. 压线（CENTER_INSIDE 或 距离边界很近）
        3. 跨线/变道中（CENTER_OUTSIDE）
        4. 压线（进入新车道）
        5. 完全进入新车道（FULLY_INSIDE）
        
        简化检测：
        - 从完全在车道内 -> 压线/跨线 -> 完全在车道内
        - 或者：压线/跨线状态变化
        
        Args:
            last_state: 上一次的状态
            current_containment: 当前包含关系
            is_pressing_line: 当前是否压线
            dist_to_left: 到左边界距离
            dist_to_right: 到右边界距离
            current_time: 当前时间
            last_time: 上一次时间
            
        Returns:
            Optional[Dict]: 变道事件信息，如果检测到则返回
        """
        if last_state is None:
            return None
        
        last_containment = last_state.get('containment_type', EgoLaneContainmentType.UNKNOWN)
        last_is_pressing = last_state.get('is_pressing_line', False)
        
        # 检测变道方向
        direction = 'unknown'
        if dist_to_left < dist_to_right:
            direction = 'left'
        elif dist_to_right < dist_to_left:
            direction = 'right'
        
        # 变道事件判定：
        # 1. 从完全在车道内 -> 压线或跨线
        if (last_containment == EgoLaneContainmentType.FULLY_INSIDE and 
            current_containment != EgoLaneContainmentType.FULLY_INSIDE):
            return {
                'type': 'start_lane_change',
                'direction': direction,
                'from_containment': last_containment.name,
                'to_containment': current_containment.name,
            }
        
        # 2. 从压线/跨线 -> 完全在车道内（完成变道）
        if (last_containment != EgoLaneContainmentType.FULLY_INSIDE and 
            current_containment == EgoLaneContainmentType.FULLY_INSIDE):
            return {
                'type': 'complete_lane_change',
                'direction': direction,
                'from_containment': last_containment.name,
                'to_containment': current_containment.name,
            }
        
        # 3. 从跨线 -> 压线（变道中）
        if (last_containment == EgoLaneContainmentType.CENTER_OUTSIDE and 
            current_containment == EgoLaneContainmentType.CENTER_INSIDE):
            return {
                'type': 'entering_new_lane',
                'direction': direction,
                'from_containment': last_containment.name,
                'to_containment': current_containment.name,
            }
        
        # 4. 压线状态变化
        if last_is_pressing != is_pressing_line:
            return {
                'type': 'pressing_line_change',
                'direction': direction,
                'from_pressing': last_is_pressing,
                'to_pressing': is_pressing_line,
            }
        
        return None
    
    def _is_same_direction(self, directions: List[str]) -> bool:
        """
        判断是否大部分是同方向
        
        Args:
            directions: 方向列表
            
        Returns:
            bool: 是否同方向
        """
        if not directions:
            return False
        
        # 统计方向
        left_count = directions.count('left')
        right_count = directions.count('right')
        unknown_count = directions.count('unknown')
        
        total = len(directions)
        
        # 如果某一方向占比超过50%，视为同方向
        if left_count > total * 0.5:
            return True
        
        if right_count > total * 0.5:
            return True
        
        return False
