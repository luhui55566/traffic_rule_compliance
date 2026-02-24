"""
Fishbone line deceleration traffic rule implementation.
"""

import logging
import math
from typing import Optional, List, Dict, Any
from .base import TrafficRuleBase
from ..types import VehicleState, Violation, ViolationSeverity

logger = logging.getLogger(__name__)


class FishboneRule(TrafficRuleBase):
    """
    Fishbone line deceleration violation detection rule.
    
    Checks if vehicle decelerates sufficiently when approaching fishbone lines.
    """
    
    def __init__(self, 
                 required_deceleration: float = 2.0,
                 trigger_distance: float = 100.0,
                 max_speed_to_trigger: float = 40.0,
                 enabled: bool = True):
        """
        Initialize fishbone rule.
        
        Args:
            required_deceleration: Required deceleration in m/s² (default: 2.0)
            trigger_distance: Distance to trigger rule in meters (default: 100m)
            max_speed_to_trigger: Max speed to trigger in km/h (default: 40 km/h)
            enabled: Whether this rule is enabled
        """
        super().__init__("R003", "鱼骨线减速检测", enabled)
        self.required_deceleration = required_deceleration
        self.trigger_distance = trigger_distance
        self.max_speed_to_trigger = max_speed_to_trigger
    
    def check(self, 
             current_state: VehicleState,
             history: List[VehicleState],
             environment_data: Dict[str, Any]) -> Optional[Violation]:
        """
        Check if fishbone deceleration rule is violated.
        
        Args:
            current_state: Current vehicle state
            history: List of historical vehicle states
            environment_data: Environment data from map API
            
        Returns:
            Violation object if rule is violated, None otherwise
        """
        if not self.enabled:
            return None
        
        # Get nearby fishbone lines from environment data
        nearby_fishbones = environment_data.get('nearby_fishbones', [])
        
        if not nearby_fishbones:
            return None
        
        # Convert speed to km/h
        current_speed_kmh = current_state.speed * 3.6
        
        # Check if approaching any fishbone line
        pos = current_state.get_position()
        for fishbone in nearby_fishbones:
            distance = self._calculate_distance(
                pos[0], pos[1],
                fishbone['latitude'], fishbone['longitude']
            )
            
            # Check if within trigger distance and speed is high enough
            if distance < self.trigger_distance and current_speed_kmh > self.max_speed_to_trigger:
                # Calculate deceleration from history
                deceleration = self._calculate_deceleration(history)
                
                if deceleration < self.required_deceleration:
                    logger.warning(
                        f"Fishbone deceleration violation: {deceleration:.2f} m/s² "
                        f"(required: {self.required_deceleration} m/s²)"
                    )
                    
                    return Violation(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=ViolationSeverity.MAJOR,
                        description=f"经过鱼骨线未充分减速 (减速: {deceleration:.2f} m/s²)",
                        latitude=pos[0],
                        longitude=pos[1],
                        lane_id=current_state.lane_id,
                        start_time=current_state.timestamp,
                        end_time=current_state.timestamp,
                        details={
                            'deceleration': deceleration,
                            'required_deceleration': self.required_deceleration,
                            'distance_to_fishbone': distance,
                            'current_speed_kmh': current_speed_kmh
                        }
                    )
        
        return None
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 + 
               math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _calculate_deceleration(self, history: List[VehicleState]) -> float:
        """
        Calculate average deceleration from history.
        
        Args:
            history: List of historical vehicle states
            
        Returns:
            Average deceleration in m/s²
        """
        if len(history) < 2:
            return 0.0
        
        # Calculate deceleration from recent states
        decelerations = []
        for i in range(1, min(len(history), 5)):
            dt = history[i].timestamp - history[i-1].timestamp
            if dt > 0:
                dv = history[i].speed - history[i-1].speed
                decel = -dv / dt  # Negative acceleration = deceleration
                if decel > 0:
                    decelerations.append(decel)
        
        if not decelerations:
            return 0.0
        
        return sum(decelerations) / len(decelerations)
