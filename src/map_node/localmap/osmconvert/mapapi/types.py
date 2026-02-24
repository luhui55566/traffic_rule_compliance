"""
Data types for MapAPI module.
"""

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from map_node.map_common.base import Position as BasePosition
else:
    BasePosition = object  # type: ignore


class LaneletType(Enum):
    """Lanelet type enumeration."""
    HIGHWAY = "highway"
    RURAL = "rural"
    URBAN = "urban"
    RAMP = "ramp"
    EXIT = "exit"
    ENTRY = "entry"
    UNKNOWN = "unknown"


class SignType(Enum):
    """Traffic sign type enumeration."""
    SPEED_LIMIT = "speed_limit"
    STOP = "stop"
    YIELD = "yield"
    NO_ENTRY = "no_entry"
    ONE_WAY = "one_way"
    CONSTRUCTION = "construction"
    FISHBONE = "fishbone"
    TRAFFIC_LIGHT = "traffic_light"
    UNKNOWN = "unknown"


@dataclass
class Lanelet:
    """Lanelet information."""
    id: str
    left_bound: List[BasePosition]  # Left boundary point sequence
    right_bound: List[BasePosition]  # Right boundary point sequence
    speed_limit: Optional[float] = None  # Speed limit (km/h)
    lanelet_type: LaneletType = LaneletType.UNKNOWN
    
    def centerline(self) -> List[BasePosition]:
        """
        Calculate lanelet centerline.
        
        Returns:
            List of centerline positions
        """
        if len(self.left_bound) != len(self.right_bound):
            # If bounds have different lengths, use the minimum
            min_len = min(len(self.left_bound), len(self.right_bound))
            left = self.left_bound[:min_len]
            right = self.right_bound[:min_len]
        else:
            left = self.left_bound
            right = self.right_bound
        
        from map_node.map_common.base import Position
        centerline = []
        for l, r in zip(left, right):
            centerline.append(Position(
                latitude=(l.latitude + r.latitude) / 2,
                longitude=(l.longitude + r.longitude) / 2,
                altitude=(l.altitude + r.altitude) / 2 if l.altitude and r.altitude else None
            ))
        return centerline
    
    def length(self) -> float:
        """
        Calculate lanelet length.
        
        Returns:
            Length in meters
        """
        import math
        centerline = self.centerline()
        if len(centerline) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(len(centerline) - 1):
            p1 = centerline[i]
            p2 = centerline[i + 1]
            # Haversine formula for distance calculation
            lat1, lon1 = math.radians(p1.latitude), math.radians(p1.longitude)
            lat2, lon2 = math.radians(p2.latitude), math.radians(p2.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth's radius in meters
            R = 6371000
            total_length += R * c
        
        return total_length
    
    def width(self) -> float:
        """
        Calculate average lanelet width.
        
        Returns:
            Average width in meters
        """
        import math
        if len(self.left_bound) != len(self.right_bound):
            min_len = min(len(self.left_bound), len(self.right_bound))
            left = self.left_bound[:min_len]
            right = self.right_bound[:min_len]
        else:
            left = self.left_bound
            right = self.right_bound
        
        if len(left) < 1:
            return 0.0
        
        total_width = 0.0
        for l, r in zip(left, right):
            # Calculate distance between left and right boundary points
            lat1, lon1 = math.radians(l.latitude), math.radians(l.longitude)
            lat2, lon2 = math.radians(r.latitude), math.radians(r.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            
            R = 6371000
            total_width += R * c
        
        return total_width / len(left)
    
    def __repr__(self) -> str:
        return (f"Lanelet(id={self.id}, type={self.lanelet_type.value}, "
                f"speed_limit={self.speed_limit}, "
                f"left_bound={len(self.left_bound)}pts, "
                f"right_bound={len(self.right_bound)}pts)")


@dataclass
class TrafficSign:
    """Traffic sign information."""
    id: str
    sign_type: SignType
    position: BasePosition
    value: Optional[str] = None  # Sign value (e.g., speed limit value)
    direction: Optional[float] = None  # Sign orientation (radians)
    
    def __repr__(self) -> str:
        return (f"TrafficSign(id={self.id}, type={self.sign_type.value}, "
                f"value={self.value}, pos={self.position})")


@dataclass
class FishboneLine:
    """Fishbone line information."""
    id: str
    position: BasePosition
    direction: float  # Direction in radians
    length: float  # Length in meters
    
    def __repr__(self) -> str:
        return (f"FishboneLine(id={self.id}, pos={self.position}, "
                f"direction={self.direction:.2f}, length={self.length:.1f}m)")


@dataclass
class ConstructionSign:
    """Construction sign information."""
    id: str
    position: BasePosition
    direction: float  # Direction in radians
    distance_threshold: float  # Distance threshold for deceleration (meters)
    
    def __repr__(self) -> str:
        return (f"ConstructionSign(id={self.id}, pos={self.position}, "
                f"direction={self.direction:.2f}, threshold={self.distance_threshold:.1f}m)")


@dataclass
class RampInfo:
    """Ramp information."""
    id: str
    ramp_type: str  # "entry", "exit", "connector"
    position: BasePosition
    length: float
    connected_lanelets: List[str]  # IDs of connected lanelets
    
    def __repr__(self) -> str:
        return (f"RampInfo(id={self.id}, type={self.ramp_type}, "
                f"length={self.length:.1f}m, connected={len(self.connected_lanelets)})")
