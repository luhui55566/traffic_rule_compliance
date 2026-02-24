"""
Base data structures for map module.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Position:
    """Position information in WGS84 coordinate system."""
    
    latitude: float  # Latitude in degrees
    longitude: float  # Longitude in degrees
    altitude: Optional[float] = None  # Altitude in meters (optional)
    
    def to_tuple(self) -> tuple:
        """Convert to tuple format."""
        return (self.latitude, self.longitude, self.altitude)
    
    def __repr__(self) -> str:
        return f"Position(lat={self.latitude:.6f}, lon={self.longitude:.6f}, alt={self.altitude})"


@dataclass
class BoundingBox:
    """Map bounding box."""
    
    min_lat: float  # Minimum latitude
    max_lat: float  # Maximum latitude
    min_lon: float  # Minimum longitude
    max_lon: float  # Maximum longitude
    
    def contains(self, position: Position) -> bool:
        """
        Check if a position is within the bounding box.
        
        Args:
            position: Position to check
            
        Returns:
            True if position is within the bounding box
        """
        return (self.min_lat <= position.latitude <= self.max_lat and
                self.min_lon <= position.longitude <= self.max_lon)
    
    def __repr__(self) -> str:
        return (f"BoundingBox(lat=[{self.min_lat:.6f}, {self.max_lat:.6f}], "
                f"lon=[{self.min_lon:.6f}, {self.max_lon:.6f}])")


@dataclass
class MapInfo:
    """Map metadata information."""
    
    map_type: str  # Map type, e.g., "osm"
    file_path: str  # Path to the map file
    num_lanelets: int  # Number of lanelets in the map
    bounds: BoundingBox  # Map bounding box
    coordinate_system: str  # Coordinate system, e.g., "WGS84"
    projector: Optional['Projector'] = None  # Projector used for coordinate transformation
    is_loaded: bool = False  # Whether the map is loaded
    
    def __repr__(self) -> str:
        return (f"MapInfo(type={self.map_type}, file={self.file_path}, "
                f"lanelets={self.num_lanelets}, loaded={self.is_loaded})")
    
    def to_dict(self) -> dict:
        """Convert MapInfo to dictionary format."""
        return {
            'map_type': self.map_type,
            'file_path': self.file_path,
            'num_lanelets': self.num_lanelets,
            'bounds': {
                'min_lat': self.bounds.min_lat,
                'max_lat': self.bounds.max_lat,
                'min_lon': self.bounds.min_lon,
                'max_lon': self.bounds.max_lon
            },
            'coordinate_system': self.coordinate_system,
            'is_loaded': self.is_loaded
        }
