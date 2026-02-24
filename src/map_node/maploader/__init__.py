"""
MapLoader module for loading OSM and XODR format maps.
"""

from .loader import MapLoader
from .loader_xodr import XODRLoader, XODRMapData
from .utils import Projector, UtmProjectorWrapper

__all__ = [
    'MapLoader',
    'XODRLoader',
    'XODRMapData',
    'Projector',
    'UtmProjectorWrapper',
]


def create_loader(map_format: str):
    """
    Factory function to create appropriate loader based on map format.
    
    Args:
        map_format: Map format type - "osm" or "xodr"
        
    Returns:
        MapLoader or XODRLoader instance
        
    Raises:
        ValueError: If map_format is not supported
    """
    if map_format.lower() == "osm":
        return MapLoader()
    elif map_format.lower() == "xodr":
        return XODRLoader()
    else:
        raise ValueError(f"Unsupported map format: {map_format}. Supported formats: 'osm', 'xodr'")
