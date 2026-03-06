"""
规则基类

定义规则的基本接口和有状态规则的状态管理。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# 添加项目路径
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from env_node.env_model import EnvironmentModel
from traffic_rule.models import Violation


class TrafficRule(ABC):
    """
    规则基类
    
    所有交通规则都应继承此基类。
    规则内部管理自判断逻辑（should_check由规则内部的check方法调用）。
    """
    
    def __init__(self):
        """初始化规则"""
        self.id = self.__class__.__name__
        self.name = self._get_rule_name()
        self.priority = self._get_priority()
    
    @abstractmethod
    def _get_rule_name(self) -> str:
        """
        获取规则名称（子类必须实现）
        
        Returns:
            str: 规则名称
        """
        pass
    
    @abstractmethod
    def _get_priority(self) -> int:
        """
        获取规则优先级（子类必须实现）
        
        Returns:
            int: 优先级（0-100，数字越大优先级越高）
        """
        pass
    
    @abstractmethod
    def should_check(self, env_model: EnvironmentModel) -> bool:
        """
        规则自判断：是否需要执行检查
        
        ⚠️ 调用位置：由规则内部的 check() 方法调用
        
        作用：第二级过滤（细粒度）
        - 访问 env_model 的丰富环境信息
        - 自主判断是否需要执行检查
        - 返回 True=需要检查, False=跳过
        
        Args:
            env_model: 环境模型
            
        Returns:
            bool: True=需要检查, False=跳过
        """
        pass
    
    @abstractmethod
    def check(self, env_model: EnvironmentModel) -> Optional[Violation]:
        """
        执行规则检查（子类必须实现）
        
        流程：
        1. 调用 should_check(env_model) 判断是否需要检查
        2. 如果需要检查，执行检查逻辑
        3. 如果不需要检查，返回 None
        
        Args:
            env_model: 环境模型
            
        Returns:
            Optional[Violation]: 违规对象或None
        """
        pass


class StatefulTrafficRule(TrafficRule):
    """
    有状态规则基类
    
    针对长时序场景（如连续变道、累计超速等），提供统一的状态管理。
    """
    
    def __init__(self):
        """初始化有状态规则"""
        super().__init__()
        self._state: Dict[str, Any] = {}
        self._state_history: List[Dict[str, Any]] = []
    
    def update_state(self, key: str, value: Any) -> None:
        """
        更新状态
        
        Args:
            key: 状态键
            value: 状态值
        """
        self._state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        获取状态
        
        Args:
            key: 状态键
            default: 默认值
            
        Returns:
            状态值，如果不存在则返回默认值
        """
        return self._state.get(key, default)
    
    def record_history(self, timestamp: float, data: Dict[str, Any]) -> None:
        """
        记录历史（用于长时序判断）
        
        Args:
            timestamp: 时间戳
            data: 历史数据
        """
        self._state_history.append({
            'timestamp': timestamp,
            'data': data
        })
    
    def get_recent_history(
        self, 
        time_window: float, 
        current_time: float
    ) -> List[Dict[str, Any]]:
        """
        获取时间窗口内的历史
        
        Args:
            time_window: 时间窗口（秒）
            current_time: 当前时间戳
            
        Returns:
            时间窗口内的历史记录列表
        """
        return [
            h for h in self._state_history
            if current_time - h['timestamp'] <= time_window
        ]
    
    def clear_old_history(self, time_window: float, current_time: float) -> None:
        """
        清理过期的历史记录（防止内存泄漏）
        
        Args:
            time_window: 保留时间窗口（秒）
            current_time: 当前时间戳
        """
        self._state_history = [
            h for h in self._state_history
            if current_time - h['timestamp'] <= time_window
        ]
    
    def reset_state(self) -> None:
        """
        重置状态（轨迹结束时调用）
        """
        self._state = {}
        self._state_history = []
