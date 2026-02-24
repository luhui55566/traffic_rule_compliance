"""
Base class for traffic rule checking.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from ..types import VehicleState, Violation, ViolationSeverity


class TrafficRuleBase(ABC):
    """
    Abstract base class for traffic rule checking.
    
    All traffic rule implementations should inherit from this class
    and implement the check() method.
    """
    
    def __init__(self, rule_id: str, rule_name: str, enabled: bool = True):
        """
        Initialize traffic rule.
        
        Args:
            rule_id: Unique rule identifier (e.g., "R001")
            rule_name: Human-readable rule name
            enabled: Whether this rule is enabled
        """
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.enabled = enabled
    
    @abstractmethod
    def check(self, 
             current_state: VehicleState,
             history: List[VehicleState],
             environment_data: Dict[str, Any]) -> Optional[Violation]:
        """
        Check if traffic rule is violated.
        
        Args:
            current_state: Current vehicle state
            history: List of historical vehicle states
            environment_data: Environment data from map API
            
        Returns:
            Violation object if rule is violated, None otherwise
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if rule is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable this rule."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable this rule."""
        self.enabled = False
    
    def __repr__(self) -> str:
        return f"TrafficRuleBase(id={self.rule_id}, name={self.rule_name}, enabled={self.enabled})"
