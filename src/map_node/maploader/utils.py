"""
Utility functions and classes for map module.
"""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

try:
    from lanelet2.core import BasicPoint2d, GPSPoint
    from lanelet2.projection import UtmProjector
    from lanelet2.io import Origin
    LANELET2_AVAILABLE = True
except ImportError:
    LANELET2_AVAILABLE = False
    BasicPoint2d = None
    GPSPoint = None
    UtmProjector = None
    Origin = None

from map_node.map_common.base import Position

if TYPE_CHECKING:
    from lanelet2.core import BasicPoint2d as Lanelet2BasicPoint2d
    from lanelet2.io import Origin as Lanelet2Origin
    from lanelet2.projection import UtmProjector as Lanelet2UtmProjector
else:
    Lanelet2BasicPoint2d = object  # type: ignore
    Lanelet2Origin = object  # type: ignore
    Lanelet2UtmProjector = object  # type: ignore


class Projector(ABC):
    """Projector interface for coordinate transformation."""
    
    @abstractmethod
    def forward(self, gps: Position) -> BasicPoint2d:
        """
        Convert GPS coordinates to map coordinates.
        
        Args:
            gps: GPS position
            
        Returns:
            Map coordinate point
        """
        pass
    
    @abstractmethod
    def reverse(self, point: BasicPoint2d) -> Position:
        """
        Convert map coordinates to GPS coordinates.
        
        Args:
            point: Map coordinate point
            
        Returns:
            GPS position
        """
        pass


class UtmProjectorWrapper(Projector):
    """UTM projector wrapper using Lanelet2's UtmProjector."""
    
    def __init__(self, origin: Lanelet2Origin):
        """
        Initialize UTM projector.
        
        Args:
            origin: Map origin (Origin object with GPSPoint)
        """
        if not LANELET2_AVAILABLE:
            raise ImportError("Lanelet2 is not installed. Please install it first.")
        self.projector = UtmProjector(origin)
        self.origin = origin
    
    def forward(self, gps: Position) -> BasicPoint2d:
        """Convert GPS coordinates to map coordinates."""
        gps_point = GPSPoint(lat=gps.latitude, lon=gps.longitude)
        return self.projector.forward(gps_point)
    
    def reverse(self, point: BasicPoint2d) -> Position:
        """Convert map coordinates to GPS coordinates."""
        gps_point = self.projector.reverse(point)
        return Position(latitude=gps_point.lat, longitude=gps_point.lon)
    
    def __repr__(self) -> str:
        return f"UtmProjectorWrapper(origin=({self.origin.lat}, {self.origin.lon}))"
