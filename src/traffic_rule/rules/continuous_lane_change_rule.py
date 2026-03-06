"""
连续变道规则

检测车辆是否在短时间内连续变道（基于压线量判断，不依赖车道ID）。
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import math
import logging

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# 配置日志
logger = logging.getLogger(__name__)

from env_node.env_model import EnvironmentModel, EgoLaneContainmentType
from traffic_rule.models import Violation, ViolationLevel
from traffic_rule.rules.base import StatefulTrafficRule


class ContinuousLaneChangeRule(StatefulTrafficRule):
    """
    连续变道规则
    
    检测车辆是否在短时间内连续变道。
    
    设计思路（基于距离条件判断，不依赖车道ID）：
    1. 不依赖车道ID变化（因为ID会变）
    2. 使用距离条件判断变道：
       - 向右变道：前一帧 dist_left<1m && dist_right>2.5m →下一帧 dist_left>2.5m && dist_right<1m
       - 向左变道：前一帧 dist_left>2.5m && dist_right<1m → 下一帧 dist_left<1m && dist_right>2.5m
    3. 必须从 FULLY_INSIDE 状态开始才算一次有效变道
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
    
    # 距离判断阈值（米）
    NEAR_THRESHOLD = 1.0    # 靠近边界的阈值
    FAR_THRESHOLD = 2.5     # 远离边界的阈值
    
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
        
        流程（基于距离条件判断）：
        1. 检测当前车辆与车道边界的关系
        2. 使用距离条件识别变道事件
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
        
        # 调试日志：输出当前帧的状态
        logger.debug(
            f"[帧{env_model.frame_index}] 时间:{current_time:.2f}s | "
            f"containment={containment_type.name} | "
            f"dist_left={dist_to_left:.2f}m | dist_right={dist_to_right:.2f}m"
        )
        
        # 获取上一次的状态
        last_state = self.get_state('last_state')
        last_time = self.get_state('last_time', current_time)
        
        # 检测帧丢失：如果时间间隔过大，重置状态机
        time_gap = current_time - last_time
        if time_gap > 1:  # 超过100ms
            logger.debug(
                f"[帧{env_model.frame_index}] 检测到帧丢失: 时间间隔={time_gap:.3f}s"
            )
            # 重置状态机
            self.update_state('lane_change_in_progress', False)
            self.update_state('waiting_for_full_inside', True)  # 等待 FULLY_INSIDE 状态
            last_state = None
        
        # 检测变道事件
        lane_change_event = self._detect_lane_change(
            last_state,
            containment_type,
            dist_to_left,
            dist_to_right,
            current_time
        )
        
        # 如果检测到变道事件，记录到历史
        if lane_change_event is not None:
            # 避免短时间内重复记录
            recent_changes = self.get_recent_history(self.MIN_LANE_CHANGE_INTERVAL, current_time)
            if len(recent_changes) == 0:
                # 添加GPS位置信息到变道事件
                ego_state = env_model.ego_state
                if ego_state and ego_state.global_state and ego_state.global_state.position:
                    pos = ego_state.global_state.position
                    lane_change_event['latitude'] = pos.latitude
                    lane_change_event['longitude'] = pos.longitude
                    lane_change_event['altitude'] = pos.altitude
                
                # 添加帧索引
                lane_change_event['frame_index'] = env_model.frame_index
                
                self.record_history(current_time, lane_change_event)
                
                # 判断变道方向
                direction = lane_change_event.get('direction', 'unknown')
                
                # 更新状态
                self.update_state('last_lane_change_time', current_time)
                self.update_state('last_lane_change_direction', direction)
                
                # 调试日志：记录变道事件
                logger.info(
                    f"[变道检测] 帧{env_model.frame_index} 时间:{current_time:.2f}s | "
                    f"方向:{direction} | 类型:{lane_change_event.get('type')} | "
                    f"前一帧: left={lane_change_event.get('last_dist_left', 0):.2f}m, right={lane_change_event.get('last_dist_right', 0):.2f}m | "
                    f"当前帧: left={lane_change_event.get('curr_dist_left', 0):.2f}m, right={lane_change_event.get('curr_dist_right', 0):.2f}m"
                )
        
        # 更新当前状态
        self.update_state('last_state', {
            'containment_type': containment_type,
            'dist_to_left': dist_to_left,
            'dist_to_right': dist_to_right,
        })
        self.update_state('last_time', current_time)
        
        # 检查时间窗口内的变道次数
        recent_changes = self.get_recent_history(self.TIME_WINDOW, current_time)
        
        # 调试日志：输出当前变道历史数量
        if len(recent_changes) > 0:
            logger.debug(
                f"[帧{env_model.frame_index}] 时间窗口内变道次数: {len(recent_changes)} | "
                f"历史记录总数: {len(self._state_history)}"
            )
        
        # 判定是否连续变道
        if len(recent_changes) >= self.LANE_CHANGE_THRESHOLD:
            # 检查是否同方向连续变道
            directions = [change['data'].get('direction', 'unknown') for change in recent_changes]
            
            # 如果大部分是同方向，判定为连续变道
            if self._is_same_direction(directions):
                # 构建违规描述
                direction_str = "左侧" if directions[0] == 'left' else "右侧" if directions[0] == 'right' else "混合方向"
                
                # 构建每次变道的详细信息
                lane_change_details = []
                for i, change in enumerate(recent_changes):
                    detail = {
                        'sequence': i + 1,
                        'timestamp': change['timestamp'],
                        'frame_index': change['data'].get('frame_index'),
                        'direction': change['data'].get('direction'),
                        'latitude': change['data'].get('latitude'),
                        'longitude': change['data'].get('longitude'),
                        'position': {
                            'dist_to_left': change['data'].get('curr_dist_left'),
                            'dist_to_right': change['data'].get('curr_dist_right'),
                        }
                    }
                    lane_change_details.append(detail)
                
                logger.warning(
                    f"[连续变道违规] 帧{env_model.frame_index} 时间:{current_time:.2f}s | "
                    f"{self.TIME_WINDOW:.0f}秒内{len(recent_changes)}次变道（{direction_str}）"
                )
                
                # 只清除最早的那次变道，保留最新的变道记录
                # 这样如果再变一次，可以再次检测到连续变道违规
                if len(self._state_history) > 0:
                    self._state_history.pop(0)  # 移除最早的记录
                
                return Violation(
                    rule_id=self.id,
                    rule_name=self.name,
                    level=ViolationLevel.MINOR,
                    description=f"连续变道：{self.TIME_WINDOW:.0f}秒内{len(recent_changes)}次变道（{direction_str}）",
                    timestamp=current_time,
                    frame_index=env_model.frame_index,
                    details={'lane_changes': lane_change_details}
                )
        
        # 定期清理过期历史（防止内存泄漏）
        if len(self._state_history) > 100:
            self.clear_old_history(self.TIME_WINDOW, current_time)
        
        return None
    
    def _detect_lane_change(
        self,
        last_state: Optional[Dict[str, Any]],
        current_containment: EgoLaneContainmentType,
        dist_to_left: float,
        dist_to_right: float,
        current_time: float
    ) -> Optional[Dict[str, Any]]:
        """
        检测变道事件（状态机模式）
        
        状态机流程：
        1. 初始状态：等待 FULLY_INSIDE（waiting_for_full_inside=True）
        2. 检测到 FULLY_INSIDE：开始监控变道条件（waiting_for_full_inside=False）
        3. 检测到距离条件满足：记录变道事件，继续监控（不重置）
        
        距离条件：
        - 向右变道：前一帧 dist_left<1m && dist_right>2.5m → 下一帧 dist_left>2.5m && dist_right<1m
        - 向左变道：前一帧 dist_left>2.5m && dist_right<1m → 下一帧 dist_left<1m && dist_right>2.5m
        
        Args:
            last_state: 上一次的状态
            current_containment: 当前包含关系
            dist_to_left: 到左边界距离
            dist_to_right: 到右边界距离
            current_time: 当前时间
            
        Returns:
            Optional[Dict]: 变道事件信息，仅在变道完成时返回
        """
        # 获取状态机状态
        waiting_for_full_inside = self.get_state('waiting_for_full_inside', True)
        
        # 状态1：等待 FULLY_INSIDE 状态
        if waiting_for_full_inside:
            if current_containment == EgoLaneContainmentType.FULLY_INSIDE:
                # 检测到 FULLY_INSIDE，开始监控变道
                self.update_state('waiting_for_full_inside', False)
                logger.debug(f"[状态机] 检测到 FULLY_INSIDE，开始监控变道条件")
            return None
        
        # 状态2：监控变道条件（已经过 FULLY_INSIDE 状态）
        # 检查是否需要重置（重新回到 FULLY_INSIDE 状态）
        if current_containment == EgoLaneContainmentType.FULLY_INSIDE:
            # 车辆完全在车道内，保持监控状态，准备检测下一次变道
            self.update_state('waiting_for_full_inside', False)
            return None
        
        if last_state is None:
            return None
        
        last_dist_to_left = last_state.get('dist_to_left', float('inf'))
        last_dist_to_right = last_state.get('dist_to_right', float('inf'))
        last_containment = last_state.get('containment_type', EgoLaneContainmentType.UNKNOWN)
        
        # 前一帧的条件判断
        last_near_left = last_dist_to_left < self.NEAR_THRESHOLD
        last_far_right = last_dist_to_right > self.FAR_THRESHOLD
        last_near_right = last_dist_to_right < self.NEAR_THRESHOLD
        last_far_left = last_dist_to_left > self.FAR_THRESHOLD
        
        # 当前帧的条件判断
        curr_near_left = dist_to_left < self.NEAR_THRESHOLD
        curr_far_right = dist_to_right > self.FAR_THRESHOLD
        curr_near_right = dist_to_right < self.NEAR_THRESHOLD
        curr_far_left = dist_to_left > self.FAR_THRESHOLD
        
        direction = 'unknown'
        lane_change_detected = False
        
        # 检测向左变道：从靠近左边变成靠近右边
        # 前一帧: dist_left<1m && dist_right>2.5m
        # 当前帧: dist_left>2.5m && dist_right<1m
        if last_near_left and last_far_right and curr_far_left and curr_near_right:
            direction = 'left'
            lane_change_detected = True
            logger.info(
                f"[变道检测] 向左变道 | "
                f"前一帧: left={last_dist_to_left:.2f}m, right={last_dist_to_right:.2f}m | "
                f"当前帧: left={dist_to_left:.2f}m, right={dist_to_right:.2f}m"
            )
        
        # 检测向右变道：从靠近右边变成靠近左边
        # 前一帧: dist_left>2.5m && dist_right<1m
        # 当前帧: dist_left<1m && dist_right>2.5m
        elif last_far_left and last_near_right and curr_near_left and curr_far_right:
            direction = 'right'
            lane_change_detected = True
            logger.info(
                f"[变道检测] 向右变道 | "
                f"前一帧: left={last_dist_to_left:.2f}m, right={last_dist_to_right:.2f}m | "
                f"当前帧: left={dist_to_left:.2f}m, right={dist_to_right:.2f}m"
            )
        
        if lane_change_detected:
            # 不重置状态机，继续监控（连续变道场景中车辆可能一直在 CENTER_INSIDE 状态）
            # 只有在检测到 FULLY_INSIDE 后才会重新开始新的变道检测周期
            # self.update_state('waiting_for_full_inside', True)  # 注释掉，不重置
            
            left_dist_change = last_dist_to_left - dist_to_left
            right_dist_change = last_dist_to_right - dist_to_right
            
            return {
                'type': 'distance_based_lane_change',
                'direction': direction,
                'from_containment': last_containment.name if hasattr(last_containment, 'name') else str(last_containment),
                'to_containment': current_containment.name,
                'left_dist_change': left_dist_change,
                'right_dist_change': right_dist_change,
                'last_dist_left': last_dist_to_left,
                'last_dist_right': last_dist_to_right,
                'curr_dist_left': dist_to_left,
                'curr_dist_right': dist_to_right,
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
