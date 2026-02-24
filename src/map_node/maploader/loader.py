"""
Map loader for loading OSM format maps using Lanelet2.
"""

import logging
from typing import Optional, TYPE_CHECKING

try:
    import lanelet2
    from lanelet2.core import LaneletMap, BasicPoint2d, GPSPoint
    from lanelet2.io import Origin
    LANELET2_AVAILABLE = True
except ImportError:
    LANELET2_AVAILABLE = False
    LaneletMap = None
    BasicPoint2d = None
    GPSPoint = None
    Origin = None

from map_node.map_common.base import Position, BoundingBox, MapInfo
from .utils import Projector

if TYPE_CHECKING:
    from lanelet2.core import LaneletMap as Lanelet2LaneletMap
else:
    Lanelet2LaneletMap = object  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapLoader:
    """OSM map loader using Lanelet2."""
    
    def __init__(self):
        """Initialize map loader."""
        if not LANELET2_AVAILABLE:
            raise ImportError(
                "Lanelet2 is not installed. Please install it first:\n"
                "  sudo apt-get install liblanelet2-dev python3-lanelet2"
            )
        self.lanelet_map: Optional[Lanelet2LaneletMap] = None
        self.projector: Optional[Projector] = None
        self.map_info: Optional[MapInfo] = None
    
    def load_map(self, file_path: str, coordinate_type: str = "local",
                 projector: Optional[Projector] = None) -> bool:
        """
        Load OSM map file.
        
        Args:
            file_path: Path to OSM file
            coordinate_type: Coordinate type - "local" or "geographic"
                - "local": Map uses local_x/local_y tags. Loads with Origin(0,0) to preserve values.
                - "geographic": Map uses lat/lon coordinates. Loads without origin.
            projector: Optional projector for coordinate transformation after loading.
                Not used during loading, only for post-load transformations.
            
        Returns:
            True if loading succeeded, False otherwise
        """
        try:
            logger.info(f"Loading OSM map from: {file_path}")
            logger.info(f"Coordinate type: {coordinate_type}")
            
            # Load OSM file using Lanelet2 based on coordinate_type
            if coordinate_type == "local":
                # Use Origin(0,0) to preserve local_x/local_y values from OSM tags
                # This prevents Lanelet2 from incorrectly projecting relative lat/lon offsets
                gps_point_zero = GPSPoint(lat=0.0, lon=0.0)
                origin_zero = Origin(gps_point_zero)
                self.lanelet_map = lanelet2.io.load(file_path, origin_zero)
                logger.info("Loaded map with local coordinates (local_x/local_y preserved)")
            else:  # geographic
                # Load without origin, use lat/lon directly from OSM file
                self.lanelet_map = lanelet2.io.load(file_path)
                logger.info("Loaded map with geographic coordinates (lat/lon)")
            
            if self.lanelet_map is None:
                logger.error("Failed to load map: lanelet_map is None")
                return False
            
            # Set projector (for post-load transformations, not for loading)
            self.projector = projector
            
            # Generate map information
            self.map_info = self._generate_map_info(file_path, coordinate_type)
            
            logger.info(f"Map loaded successfully: {self.map_info}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Map file not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load OSM map: {e}")
            return False
    
    def get_map_data(self):
        """
        Get loaded map data for passing to MapManager.
        
        This method returns all map data as a dictionary, which can be
        passed to MapManager.initialize() for distributed ROS node scenarios.
        
        Returns:
            Dictionary containing lanelet_map, projector, and map_info
        """
        return {
            'lanelet_map': self.lanelet_map,
            'projector': self.projector,
            'map_info': self.map_info
        }
    
    def get_map_info(self) -> Optional[MapInfo]:
        """
        Get map information.
        
        Returns:
            Map information, or None if map not loaded
        """
        return self.map_info
    
    def is_loaded(self) -> bool:
        """
        Check if map is loaded.
        
        Returns:
            True if map is loaded
        """
        return self.lanelet_map is not None
    
    def _generate_map_info(self, file_path: str, coordinate_type: str = "local") -> MapInfo:
        """
        Generate map information.
        
        Args:
            file_path: Path to map file
            coordinate_type: Coordinate type used for loading
            
        Returns:
            Map information
        """
        if self.lanelet_map is None:
            raise ValueError("Map not loaded")
        
        # Use default bounding box for now
        # TODO: Implement proper bounding box calculation using lanelet2.geometry
        bounds = BoundingBox(
            min_lat=0.0,
            max_lat=0.0,
            min_lon=0.0,
            max_lon=0.0
        )
        
        # Set coordinate system based on coordinate_type
        coord_system = "local" if coordinate_type == "local" else "WGS84"
        
        return MapInfo(
            map_type="osm",
            file_path=file_path,
            num_lanelets=len(self.lanelet_map.laneletLayer),
            bounds=bounds,
            coordinate_system=coord_system,
            projector=self.projector,
            is_loaded=True
        )
