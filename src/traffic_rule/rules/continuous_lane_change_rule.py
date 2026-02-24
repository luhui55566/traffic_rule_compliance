"""
Continuous lane change traffic rule implementation.
"""

import logging
from typing import Optional, List, Dict, Any
from .base import TrafficRuleBase
from ..types import VehicleState, Violation, ViolationSeverity

logger = logging.getLogger(__name__)


class ContinuousLaneChangeRule(TrafficRuleBase):
    """
    Continuous lane change violation detection rule.
    
    Checks if vehicle changes lanes too frequently within a time window.
    """
    
    def __init__(self, time_window: float = 10.0, max_changes: int = 2, enabled: bool = True):
        """
        Initialize continuous lane change rule.
        
        Args:
            time_window: Time window in seconds (default: 10s)
            max_changes: Maximum allowed lane changes in time window (default: 2)
            enabled: Whether this rule is enabled
        """
        super().__init__("R002", "连续换道检测", enabled)
        self.time_window = time_window
        self.max_changes = max_changes
    
    def check(self, 
             current_state: VehicleState,
             history: List[VehicleState],
             environment_data: Dict[str, Any]) -> Optional[Violation]:
        """
        Check if continuous lane change rule is violated.
        
        Args:
            current_state: Current vehicle state
            history: List of historical vehicle states
            environment_data: Environment data from map API
            
        Returns:
            Violation object if rule is violated, None otherwise
        """
        if not self.enabled:
            return None
        
        # Get lane changes within time window
        lane_changes = self._count_lane_changes(history, self.time_window)
        
        if lane_changes > self.max_changes:
            logger.warning(
                f"Continuous lane change violation: {lane_changes} changes "
                f"in {self.time_window}s (max: {self.max_changes})"
            )
            
            pos = current_state.get_position()
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=ViolationSeverity.MINOR,
                description=f"{self.time_window}秒内连续换道{lane_changes}次",
                latitude=pos[0],
                longitude=pos[1],
                lane_id=current_state.lane_id,
                start_time=current_state.timestamp - self.time_window,
                end_time=current_state.timestamp,
                details={
                    'lane_changes': lane_changes,
                    'time_window': self.time_window,
                    'max_changes': self.max_changes
                }
            )
        
        return None
    
    def _count_lane_changes(self, history: List[VehicleState], time_window: float) -> int:
        """
        Count lane changes within time window.
        
        Args:
            history: List of historical vehicle states
            time_window: Time window in seconds
            
        Returns:
            Number of lane changes
        """
        if not history:
            return 0
        
        # Filter states within time window
        current_time = history[-1].timestamp if history else 0
        window_start = current_time - time_window
        
        recent_states = [
            s for s in history 
            if s.timestamp >= window_start
        ]
        
        if len(recent_states) < 2:
            return 0
        
        # Count lane changes
        lane_changes = 0
        current_lane = recent_states[0].lane_id
        
        for state in recent_states[1:]:
            if state.lane_id is not None and state.lane_id != current_lane:
                lane_changes += 1
                current_lane = state.lane_id
        
        return lane_changes
