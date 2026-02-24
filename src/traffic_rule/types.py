"""
Data types for traffic rule compliance verification system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ViolationSeverity(Enum):
    """Violation severity levels."""
    WARNING = "warning"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


@dataclass
class VehicleState:
    """
    Vehicle state information.
    
    This represents ego vehicle's current state including position,
    velocity, heading, and other relevant information.
    
    Supports both local coordinates (x, y, heading with origin at 0,0)
    and global coordinates (latitude, longitude, heading).
    """
    timestamp: float  # Timestamp in seconds
    speed: float  # Speed in m/s
    
    # Local coordinates (origin at 0,0)
    local_x: Optional[float] = None  # Local x position in meters
    local_y: Optional[float] = None  # Local y position in meters
    local_heading: Optional[float] = None  # Local heading angle in radians
    
    # Global coordinates (latitude, longitude)
    latitude: Optional[float] = None  # Latitude in degrees
    longitude: Optional[float] = None  # Longitude in degrees
    heading: Optional[float] = None  # Global heading angle in radians
    
    # Additional information
    acceleration: Optional[float] = None  # Acceleration in m/s²
    yaw_rate: Optional[float] = None  # Yaw rate in rad/s
    lane_id: Optional[str] = None  # Current lane ID
    altitude: Optional[float] = None  # Altitude in meters
    
    # Coordinate system flag
    use_local_coords: bool = False  # True if using local coords, False for global
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'speed': self.speed,
            'local_x': self.local_x,
            'local_y': self.local_y,
            'local_heading': self.local_heading,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'heading': self.heading,
            'acceleration': self.acceleration,
            'yaw_rate': self.yaw_rate,
            'lane_id': self.lane_id,
            'altitude': self.altitude,
            'use_local_coords': self.use_local_coords
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VehicleState':
        """Create VehicleState from dictionary."""
        return cls(
            timestamp=data.get('timestamp', 0.0),
            speed=data.get('speed', 0.0),
            local_x=data.get('local_x'),
            local_y=data.get('local_y'),
            local_heading=data.get('local_heading'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            heading=data.get('heading'),
            acceleration=data.get('acceleration'),
            yaw_rate=data.get('yaw_rate'),
            lane_id=data.get('lane_id'),
            altitude=data.get('altitude'),
            use_local_coords=data.get('use_local_coords', False)
        )
    
    def get_position(self) -> tuple:
        """
        Get position as (x, y) tuple based on coordinate system.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        if self.use_local_coords:
            return (self.local_x if self.local_x is not None else 0.0,
                    self.local_y if self.local_y is not None else 0.0)
        else:
            return (self.latitude if self.latitude is not None else 0.0,
                    self.longitude if self.longitude is not None else 0.0)
    
    def get_heading(self) -> float:
        """
        Get heading based on coordinate system.
        
        Returns:
            Heading angle in radians
        """
        if self.use_local_coords:
            return self.local_heading if self.local_heading is not None else 0.0
        else:
            return self.heading if self.heading is not None else 0.0
    
    def __repr__(self) -> str:
        if self.use_local_coords:
            return (f"VehicleState(t={self.timestamp:.2f}, "
                    f"local_pos=({self.local_x:.2f}, {self.local_y:.2f}), "
                    f"local_heading={self.local_heading:.2f}rad, "
                    f"speed={self.speed:.2f}m/s)")
        else:
            return (f"VehicleState(t={self.timestamp:.2f}, "
                    f"pos=({self.latitude:.6f}, {self.longitude:.6f}), "
                    f"heading={self.heading:.2f}rad, "
                    f"speed={self.speed:.2f}m/s)")


@dataclass
class Violation:
    """
    Single traffic rule violation record.
    
    Represents a detected traffic rule violation with details about
    violation type, location, and time interval.
    """
    rule_id: str  # Rule identifier (e.g., "R001", "R002")
    rule_name: str  # Human-readable rule name
    severity: ViolationSeverity  # Severity level
    description: str  # Description of violation
    
    # Position information
    latitude: float  # Latitude where violation occurred
    longitude: float  # Longitude where violation occurred
    lane_id: Optional[str] = None  # Lane ID where violation occurred
    
    # Time interval
    start_time: float = 0.0  # Start time of violation (seconds)
    end_time: Optional[float] = None  # End time of violation (seconds)
    
    # Additional details
    details: Dict[str, Any] = field(default_factory=dict)  # Additional violation details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'severity': self.severity.value,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'lane_id': self.lane_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'details': self.details
        }
    
    def __repr__(self) -> str:
        return (f"Violation({self.rule_id}: {self.rule_name}, "
                f"severity={self.severity.value}, "
                f"pos=({self.latitude:.6f}, {self.longitude:.6f}), "
                f"time=[{self.start_time:.2f}, {self.end_time:.2f}])")


@dataclass
class ViolationReport:
    """
    Traffic rule compliance verification report.
    
    Contains all violations detected during a verification session,
    along with summary statistics.
    """
    timestamp: datetime  # Report generation time
    vehicle_states: List[VehicleState]  # All vehicle states processed
    violations: List[Violation]  # All detected violations
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of report.
        
        Returns:
            Dictionary with summary statistics
        """
        total_violations = len(self.violations)
        severity_counts = {s.value: 0 for s in ViolationSeverity}
        
        for violation in self.violations:
            severity_counts[violation.severity.value] += 1
        
        rule_counts = {}
        for violation in self.violations:
            rule_counts[violation.rule_id] = rule_counts.get(violation.rule_id, 0) + 1
        
        return {
            'total_violations': total_violations,
            'severity_counts': severity_counts,
            'rule_counts': rule_counts,
            'is_compliant': total_violations == 0,
            'states_processed': len(self.vehicle_states)
        }
    
    def get_violations_by_severity(self, severity: ViolationSeverity) -> List[Violation]:
        """
        Get violations filtered by severity.
        
        Args:
            severity: Severity level to filter by
            
        Returns:
            List of violations with specified severity
        """
        return [v for v in self.violations if v.severity == severity]
    
    def get_violations_by_rule(self, rule_id: str) -> List[Violation]:
        """
        Get violations filtered by rule ID.
        
        Args:
            rule_id: Rule ID to filter by
            
        Returns:
            List of violations for specified rule
        """
        return [v for v in self.violations if v.rule_id == rule_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'summary': self.get_summary(),
            'violations': [v.to_dict() for v in self.violations]
        }
    
    def __repr__(self) -> str:
        summary = self.get_summary()
        return (f"ViolationReport(timestamp={self.timestamp.isoformat()}, "
                f"violations={summary['total_violations']}, "
                f"compliant={summary['is_compliant']})")
