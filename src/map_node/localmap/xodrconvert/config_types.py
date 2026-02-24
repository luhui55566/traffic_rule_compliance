"""
Configuration and result types for XODR to LocalMap conversion.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConversionConfig:
    """Configuration for XODR to LocalMap conversion."""
    
    # Sampling resolution for geometry discretization
    eps: float = 0.1  # meters, default 10cm
    
    # Map range for local map generation
    map_range: float = 200.0  # meters
    
    # Whether to include junction internal lanes
    include_junction_lanes: bool = True
    
    # Whether to include road objects
    include_road_objects: bool = True
    
    # Whether to include traffic signals
    include_traffic_signals: bool = True
    
    # Whether to include road markings
    include_road_markings: bool = True
    
    # Ego vehicle pose for local coordinate transformation
    ego_x: float = 0.0
    ego_y: float = 0.0
    ego_heading: float = 0.0
    
    # Map source identifier
    map_source_id: str = "unknown"


@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    
    success: bool
    data: Any = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def get_summary(self) -> str:
        """Get a summary of the conversion result."""
        if self.success:
            summary = f"Conversion successful"
            if self.has_warnings():
                summary += f" with {len(self.warnings)} warning(s)"
            return summary
        else:
            return f"Conversion failed with {len(self.errors)} error(s)"


@dataclass
class LaneConversionResult:
    """Result of lane conversion."""
    
    lane_id: int
    success: bool
    lane: Optional[Any] = None
    left_boundary_indices: List[int] = field(default_factory=list)
    right_boundary_indices: List[int] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ConversionStatistics:
    """Statistics for XODR to LocalMap conversion."""
    
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Road statistics
    total_roads: int = 0
    total_lanes: int = 0
    total_lanesections: int = 0
    
    # Junction statistics
    total_junctions: int = 0
    total_connections: int = 0
    
    # Boundary statistics
    total_boundary_segments: int = 0
    shared_boundaries: int = 0
    
    # Traffic element statistics
    total_traffic_signs: int = 0
    total_traffic_lights: int = 0
    total_crosswalks: int = 0
    total_stop_lines: int = 0
    
    # Error statistics
    conversion_errors: List[str] = field(default_factory=list)
    conversion_warnings: List[str] = field(default_factory=list)
    
    def get_duration(self) -> Optional[float]:
        """Get conversion duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def get_summary(self) -> str:
        """Get a summary of conversion statistics."""
        summary = [
            f"XODR to LocalMap Conversion Summary:",
            f"  Roads: {self.total_roads}",
            f"  Lane Sections: {self.total_lanesections}",
            f"  Lanes: {self.total_lanes}",
            f"  Junctions: {self.total_junctions}",
            f"  Connections: {self.total_connections}",
            f"  Boundary Segments: {self.total_boundary_segments}",
            f"  Shared Boundaries: {self.shared_boundaries}",
            f"  Traffic Signs: {self.total_traffic_signs}",
            f"  Traffic Lights: {self.total_traffic_lights}",
            f"  Crosswalks: {self.total_crosswalks}",
            f"  Stop Lines: {self.total_stop_lines}",
        ]
        
        duration = self.get_duration()
        if duration:
            summary.append(f"  Duration: {duration:.2f} seconds")
        
        if self.conversion_errors:
            summary.append(f"  Errors: {len(self.conversion_errors)}")
        
        if self.conversion_warnings:
            summary.append(f"  Warnings: {len(self.conversion_warnings)}")
        
        return "\n".join(summary)
