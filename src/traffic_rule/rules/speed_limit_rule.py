"""
Speed limit traffic rule implementation.
"""

import logging
from typing import Optional, List, Dict, Any
from .base import TrafficRuleBase
from ..types import VehicleState, Violation, ViolationSeverity

logger = logging.getLogger(__name__)


class SpeedLimitRule(TrafficRuleBase):
    """
    Speed limit violation detection rule.
    
    Checks if the vehicle exceeds the speed limit at its current location.
    """
    
    def __init__(self, tolerance: float = 5.0, enabled: bool = True):
        """
        Initialize speed limit rule.
        
        Args:
            tolerance: Speed tolerance in km/h (default: 5 km/h)
            enabled: Whether this rule is enabled
        """
        super().__init__("R001", "超速检测", enabled)
        self.tolerance = tolerance  # km/h
    
    def check(self, 
             current_state: VehicleState,
             history: List[VehicleState],
             environment_data: Dict[str, Any]) -> Optional[Violation]:
        """
        Check if speed limit is violated.
        
        Args:
            current_state: Current vehicle state
            history: List of historical vehicle states
            environment_data: Environment data from map API
            
        Returns:
            Violation object if speed limit is exceeded, None otherwise
        """
        if not self.enabled:
            return None
        
        # Get speed limit from environment data
        speed_limit = environment_data.get('speed_limit')
        
        if speed_limit is None:
            # No speed limit at this location
            return None
        
        # Convert speed from m/s to km/h
        current_speed_kmh = current_state.speed * 3.6
        
        # Check if speed exceeds limit with tolerance
        if current_speed_kmh > speed_limit + self.tolerance:
            logger.warning(
                f"Speed limit violation: {current_speed_kmh:.1f} km/h "
                f"(limit: {speed_limit} km/h, tolerance: {self.tolerance} km/h)"
            )
            
            pos = current_state.get_position()
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=ViolationSeverity.MAJOR,
                description=f"超速行驶: {current_speed_kmh:.1f} km/h (限速 {speed_limit} km/h)",
                latitude=pos[0],
                longitude=pos[1],
                lane_id=current_state.lane_id,
                start_time=current_state.timestamp,
                end_time=current_state.timestamp,
                details={
                    'current_speed_kmh': current_speed_kmh,
                    'speed_limit': speed_limit,
                    'excess': current_speed_kmh - speed_limit
                }
            )
        
        return None
