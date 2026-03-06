"""
限速规则（时间段版本）

检测车辆是否超过道路限速，基于时间段判定。

改进点：
1. 从单帧判定改为时间段判定
2. 记录超速开始时间和结束时间
3. 根据超速持续时间判定违规等级
"""

from typing import Optional, Dict, Any
from pathlib import Path
import sys
import math

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from env_node.env_model import EnvironmentModel
from traffic_rule.models import Violation, ViolationLevel
from traffic_rule.rules.base import StatefulTrafficRule


class SpeedLimitRule(StatefulTrafficRule):
    """
    限速规则（时间段版本）
    
    检测车辆是否超过道路限速，基于超速持续时间判定违规。
    
    设计思路：
    1. 从 ego_lane_info 获取当前车道的限速
    2. 从 ego_state 获取当前车辆速度
    3. 记录超速开始时间和结束时间
    4. 根据超速持续时间判定违规等级
    
    状态管理：
    - overspeed_start_time: 超速开始时间戳
    - overspeed_start_frame: 超速开始帧索引
    - max_overspeed: 本次超速过程中的最大超速值
    - last_speed_limit: 上一次的限速值（用于检测限速变化）
    """
    
    # 允许的超速阈值（m/s），约 3.6 km/h
    SPEED_TOLERANCE = 1.0  # m/s
    
    # 严重超速阈值（超过限速的百分比）
    MAJOR_OVERSPEED_THRESHOLD = 0.2  # 20%
    
    # 最小超速时间阈值（秒）：短于此时间的超速不算违规
    MIN_OVERSPEED_DURATION = 2.0  # 秒
    
    # 轻微超速时长阈值（秒）
    MINOR_OVERSPEED_DURATION = 5.0  # 秒
    
    # 中度超速时长阈值（秒）
    MODERATE_OVERSPEED_DURATION = 10.0  # 秒
    
    def _get_rule_name(self) -> str:
        return "限速规则（时间段）"
    
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
        执行限速检查（时间段版本）
        
        流程：
        1. 调用 should_check 判断是否需要检查
        2. 获取当前速度和限速
        3. 检测超速状态变化
        4. 更新超速状态
        5. 当超速结束时，根据持续时间判定违规
        """
        # 第二级过滤：规则自判断
        if not self.should_check(env_model):
            return None
        
        # 获取当前时间戳和帧索引
        current_time = env_model.timestamp
        current_frame = env_model.frame_index
        
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
        is_overspeeding = overspeed > self.SPEED_TOLERANCE
        
        # 获取当前状态
        overspeed_start_time = self.get_state('overspeed_start_time')
        overspeed_start_frame = self.get_state('overspeed_start_frame')
        max_overspeed = self.get_state('max_overspeed', 0.0)
        last_speed_limit = self.get_state('last_speed_limit')
        
        violation = None
        
        # 检测限速变化（换道进入不同限速区域）
        if last_speed_limit is not None and last_speed_limit != speed_limit:
            # 限速变化，如果之前在超速，先结算
            if overspeed_start_time is not None:
                violation = self._create_violation(
                    env_model, 
                    overspeed_start_time, 
                    overspeed_start_frame,
                    current_time,
                    current_frame,
                    max_overspeed,
                    last_speed_limit
                )
                # 重置状态
                self._reset_overspeed_state()
        
        # 更新限速
        self.update_state('last_speed_limit', speed_limit)
        
        if is_overspeeding:
            # 当前正在超速
            if overspeed_start_time is None:
                # 超速开始
                self.update_state('overspeed_start_time', current_time)
                self.update_state('overspeed_start_frame', current_frame)
                self.update_state('max_overspeed', overspeed)
                self.update_state('overspeed_start_speed', current_speed)
            else:
                # 继续超速，更新最大超速值
                if overspeed > max_overspeed:
                    self.update_state('max_overspeed', overspeed)
        else:
            # 当前没有超速
            if overspeed_start_time is not None:
                # 超速结束，判定是否违规
                violation = self._create_violation(
                    env_model,
                    overspeed_start_time,
                    overspeed_start_frame,
                    current_time,
                    current_frame,
                    max_overspeed,
                    speed_limit
                )
                # 重置状态
                self._reset_overspeed_state()
        
        return violation
    
    def _create_violation(
        self,
        env_model: EnvironmentModel,
        start_time: float,
        start_frame: int,
        end_time: float,
        end_frame: int,
        max_overspeed: float,
        speed_limit: float
    ) -> Optional[Violation]:
        """
        根据超速时间段创建违规记录
        
        Args:
            env_model: 环境模型
            start_time: 超速开始时间
            start_frame: 超速开始帧
            end_time: 超速结束时间
            end_frame: 超速结束帧
            max_overspeed: 最大超速值（m/s）
            speed_limit: 限速值（m/s）
        
        Returns:
            Violation 或 None
        """
        # 计算超速持续时间
        duration = end_time - start_time
        duration_seconds = duration if duration < 100000 else (end_frame - start_frame) * 0.1  # 备用计算
        
        # 如果超速时间太短，不算违规
        if duration_seconds < self.MIN_OVERSPEED_DURATION:
            return None
        
        # 计算超速百分比
        overspeed_percentage = max_overspeed / speed_limit
        
        # 判定违规等级（综合考虑超速程度和持续时间）
        level, level_str = self._determine_violation_level(
            overspeed_percentage, 
            duration_seconds
        )
        
        # 构建违规描述
        max_speed = speed_limit + max_overspeed
        description = (
            f"{level_str}：超速持续 {duration_seconds:.1f} 秒 "
            f"(帧 {start_frame} - {end_frame})，"
            f"最高速度 {max_speed*3.6:.1f} km/h，"
            f"限速 {speed_limit*3.6:.1f} km/h，"
            f"最大超速 {max_overspeed*3.6:.1f} km/h ({overspeed_percentage*100:.1f}%)"
        )
        
        # 获取位置信息
        ego_state = env_model.ego_state
        position = {
            'x': ego_state.local_state.position.x if ego_state.local_state else None,
            'y': ego_state.local_state.position.y if ego_state.local_state else None,
        }
        
        return Violation(
            rule_id=self.id,
            rule_name=self.name,
            level=level,
            description=description,
            timestamp=end_time,
            frame_index=end_frame,
            speed=max_speed,
            speed_limit=speed_limit,
            position=position,
            # 新增字段：时间段信息
            duration_seconds=duration_seconds,
            start_frame=start_frame,
            end_frame=end_frame,
            max_overspeed=max_overspeed
        )
    
    def _determine_violation_level(
        self, 
        overspeed_percentage: float, 
        duration_seconds: float
    ) -> tuple:
        """
        综合超速程度和持续时间判定违规等级
        
        Args:
            overspeed_percentage: 超速百分比（0.2 表示 20%）
            duration_seconds: 持续时间（秒）
        
        Returns:
            (ViolationLevel, 等级描述字符串)
        """
        # 严重超速（>20%）且持续时间 > 5秒
        if overspeed_percentage >= self.MAJOR_OVERSPEED_THRESHOLD:
            if duration_seconds >= self.MODERATE_OVERSPEED_DURATION:
                return ViolationLevel.MAJOR, "严重超速（长时间）"
            elif duration_seconds >= self.MINOR_OVERSPEED_DURATION:
                return ViolationLevel.MAJOR, "严重超速（中等时长）"
            else:
                return ViolationLevel.MINOR, "严重超速（短时间）"
        
        # 轻微超速（<20%）
        if duration_seconds >= self.MODERATE_OVERSPEED_DURATION:
            return ViolationLevel.MINOR, "轻微超速（长时间）"
        elif duration_seconds >= self.MINOR_OVERSPEED_DURATION:
            return ViolationLevel.MINOR, "轻微超速（中等时长）"
        else:
            return ViolationLevel.MINOR, "轻微超速（短时间）"
    
    def _reset_overspeed_state(self):
        """重置超速相关状态"""
        self.update_state('overspeed_start_time', None)
        self.update_state('overspeed_start_frame', None)
        self.update_state('max_overspeed', 0.0)
        self.update_state('overspeed_start_speed', None)
    
    def reset_state(self) -> None:
        """
        重置所有状态（轨迹结束时调用）
        """
        super().reset_state()
        self._reset_overspeed_state()
        self.update_state('last_speed_limit', None)
