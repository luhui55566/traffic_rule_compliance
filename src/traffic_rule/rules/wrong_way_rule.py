"""
Wrong way driving traffic rule implementation.
"""

import logging
import math
from typing import Optional, List, Dict, Any
from .base import TrafficRuleBase
from ..types import VehicleState, Violation, ViolationSeverity

logger = logging.getLogger(__name__)


class WrongWayRule(TrafficRuleBase):
    """
    Wrong way driving violation detection rule.
    
    Checks if vehicle is driving in the wrong direction on a lane.
    """
    
    def __init__(self, heading_tolerance: float = 45.0, enabled: bool = True):
        """
        Initialize wrong way rule.
        
        Args:
            heading_tolerance: Heading tolerance in degrees (default: 45°)
            enabled: Whether this rule is enabled
        """
        super().__init__("R005", "逆行检测", enabled)
        self.heading_tolerance = heading_tolerance
    
    def check(self, 
             current_state: VehicleState,
             history: List[VehicleState],
             environment_data: Dict[str, Any]) -> Optional[Violation]:
        """
        Check if wrong way rule is violated.
        
        Args:
            current_state: Current vehicle state
            history: List of historical vehicle states
            environment_data: Environment data from map API
            
        Returns:
            Violation object if rule is violated, None otherwise
        """
        if not self.enabled:
            return None
        
        # Get current lanelet from environment data
        current_lanelet = environment_data.get('current_lanelet')
        
        if current_lanelet is None:
            # Not on any lanelet
            return None
        
        # Get lane direction from lanelet
        lane_direction = self._get_lane_direction(current_lanelet)
        
        if lane_direction is None:
            # Cannot determine lane direction
            return None
        
        # Calculate heading difference
        heading = current_state.get_heading()
        heading_diff = abs(heading - lane_direction)
        
        # Normalize to [0, 2π]
        heading_diff = heading_diff % (2 * math.pi)
        
        # Check if heading is opposite to lane direction
        # Opposite means difference > π - tolerance
        tolerance_rad = math.radians(self.heading_tolerance)
        if heading_diff > math.pi - tolerance_rad:
            logger.warning(
                f"Wrong way violation: heading diff {math.degrees(heading_diff):.1f}° "
                f"(tolerance: {self.heading_tolerance}°)"
            )
            
            pos = current_state.get_position()
            return Violation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=ViolationSeverity.CRITICAL,
                description="逆行行驶",
                latitude=pos[0],
                longitude=pos[1],
                lane_id=current_state.lane_id,
                start_time=current_state.timestamp,
                end_time=current_state.timestamp,
                details={
                    'vehicle_heading': math.degrees(heading),
                    'lane_direction': math.degrees(lane_direction),
                    'heading_diff': math.degrees(heading_diff)
                }
            )
        
        return None
    
    def _get_lane_direction(self, lanelet) -> Optional[float]:
        """
        Get lane direction from lanelet.
        
        Args:
            lanelet: Lanelet object
            
        Returns:
            Lane direction in radians, or None if cannot determine
        """
        try:
            # Calculate direction from centerline
            centerline = lanelet.centerline()
            
            if len(centerline) < 2:
                return None
            
            # Use first and last points of centerline
            p1 = centerline[0]
            p2 = centerline[-1]
            
            # Calculate direction using atan2
            lat_diff = p2.latitude - p1.latitude
            lon_diff = p2.longitude - p1.longitude
            
            # Convert to meters for more accurate direction
            lat_diff_m = lat_diff * 111000  # Approximate meters per degree latitude
            lon_diff_m = lon_diff * 111000 * math.cos(math.radians(p1.latitude))
            
            direction = math.atan2(lon_diff_m, lat_diff_m)
            
            # Normalize to [0, 2π]
            if direction < 0:
                direction += 2 * math.pi
            
            return direction
            
        except Exception as e:
            logger.warning(f"Failed to get lane direction: {e}")
            return None
