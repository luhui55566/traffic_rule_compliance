"""
XODR map loader using pyOpenDRIVE.
"""

import logging
from typing import Optional, TYPE_CHECKING
from pathlib import Path

try:
    from pyOpenDRIVE.OpenDriveMap import PyOpenDriveMap
    from pyOpenDRIVE.Road import PyRoad
    from pyOpenDRIVE.Lane import PyLane
    from pyOpenDRIVE.LaneSection import PyLaneSection
    from pyOpenDRIVE.RoadMark import PyRoadMark
    from pyOpenDRIVE.Mesh import PyMesh
    PYOPENDRIVE_AVAILABLE = True
except ImportError:
    PYOPENDRIVE_AVAILABLE = False
    PyOpenDriveMap = None
    PyRoad = None
    PyLane = None
    PyLaneSection = None
    PyRoadMark = None
    PyMesh = None

from map_node.map_common.base import Position, BoundingBox, MapInfo

if TYPE_CHECKING:
    from pyOpenDRIVE.OpenDriveMap import PyOpenDriveMap as PyOpenDriveMapType
else:
    PyOpenDriveMapType = object  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XODRMapData:
    """Container for XODR map data compatible with existing map API."""
    
    def __init__(self, odr_map: PyOpenDriveMapType):
        """
        Initialize XODR map data.
        
        Args:
            odr_map: Loaded pyOpenDRIVE map object
        """
        self.odr_map = odr_map
        self.roads = odr_map.get_roads()
        
        # Cache for quick access
        self._road_by_id = {}
        for road in self.roads:
            self._road_by_id[road.id.decode()] = road
    
    def get_roads(self):
        """Get all roads in the map."""
        return self.roads
    
    def get_road_by_id(self, road_id: str) -> Optional[PyRoad]:
        """
        Get road by ID.
        
        Args:
            road_id: Road ID as string
            
        Returns:
            PyRoad object or None if not found
        """
        return self._road_by_id.get(road_id)
    
    def get_lanesections(self, road: PyRoad):
        """
        Get all lane sections for a road.
        
        Args:
            road: PyRoad object
            
        Returns:
            List of lane sections
        """
        return road.get_lanesections()
    
    def get_lanes(self, lanesection: PyLaneSection):
        """
        Get all lanes for a lane section.
        
        Args:
            lanesection: PyLaneSection object
            
        Returns:
            List of lanes
        """
        return lanesection.get_lanes()
    
    def get_roadmarks(self, lane: PyLane, s_start: float, s_end: float):
        """
        Get road marks for a lane within a section.
        
        Args:
            lane: PyLane object
            s_start: Start s coordinate
            s_end: End s coordinate
            
        Returns:
            List of road marks
        """
        return lane.get_roadmarks(s_start, s_end)
    
    def get_lane_mesh(self, road: PyRoad, lane: PyLane, eps: float = 0.1):
        """
        Get lane mesh for visualization.
        
        Args:
            road: PyRoad object
            lane: PyLane object
            eps: Sampling resolution
            
        Returns:
            PyMesh object with vertices and indices
        """
        return road.get_lane_mesh(lane=lane, eps=eps)
    
    def get_roadmark_mesh(self, road: PyRoad, lane: PyLane, roadmark: PyRoadMark, eps: float = 0.1):
        """
        Get roadmark mesh for visualization.
        
        Args:
            road: PyRoad object
            lane: PyLane object
            roadmark: PyRoadMark object
            eps: Sampling resolution
            
        Returns:
            PyMesh object with vertices and indices
        """
        return road.get_roadmark_mesh(lane, roadmark, eps)
    
    def get_road_object_mesh(self, road: PyRoad, road_object, eps: float = 0.1):
        """
        Get road object mesh for visualization.
        
        Args:
            road: PyRoad object
            road_object: Road object
            eps: Sampling resolution
            
        Returns:
            PyMesh object with vertices and indices
        """
        return road.get_road_object_mesh(road_object, eps)
    
    def get_road_signal_mesh(self, road: PyRoad, road_signal):
        """
        Get road signal mesh for visualization.
        
        Args:
            road: PyRoad object
            road_signal: Road signal object
            
        Returns:
            PyMesh object with vertices and indices
        """
        return road.get_road_signal_mesh(road_signal)
    
    def get_road_objects(self, road: PyRoad):
        """
        Get all road objects for a road.
        
        Args:
            road: PyRoad object
            
        Returns:
            List of road objects
        """
        return road.get_road_objects()
    
    def get_road_signals(self, road: PyRoad):
        """
        Get all road signals for a road.
        
        Args:
            road: PyRoad object
            
        Returns:
            List of road signals
        """
        return road.get_road_signals()
    
    def get_road_network_mesh(self, eps: float = 0.1):
        """
        Get complete road network mesh.
        
        Args:
            eps: Sampling resolution
            
        Returns:
            PyMesh object with all road network vertices and indices
        """
        return self.odr_map.get_road_network_mesh(eps)


class XODRLoader:
    """XODR map loader using pyOpenDRIVE."""
    
    def __init__(self):
        """Initialize XODR map loader."""
        if not PYOPENDRIVE_AVAILABLE:
            raise ImportError(
                "pyOpenDRIVE is not installed. Please install it first:\n"
                "  cd pyOpenDRIVE && python3 setup.py build_ext --inplace"
            )
        self.odr_map: Optional[PyOpenDriveMapType] = None
        self.map_data: Optional[XODRMapData] = None
        self.map_info: Optional[MapInfo] = None
    
    def load_map(self, file_path: str) -> bool:
        """
        Load XODR map file.
        
        Args:
            file_path: Path to XODR file
            
        Returns:
            True if loading succeeded, False otherwise
        """
        try:
            logger.info(f"Loading XODR map from: {file_path}")
            
            # Check if file exists
            if not Path(file_path).exists():
                logger.error(f"XODR file not found: {file_path}")
                return False
            
            # Load XODR file using pyOpenDRIVE
            # pyOpenDRIVE expects bytes for file path
            self.odr_map = PyOpenDriveMap(file_path.encode('utf-8'))
            
            if self.odr_map is None:
                logger.error("Failed to load map: odr_map is None")
                return False
            
            # Create map data wrapper
            self.map_data = XODRMapData(self.odr_map)
            
            # Generate map information
            self.map_info = self._generate_map_info(file_path)
            
            logger.info(f"XODR map loaded successfully: {self.map_info}")
            return True
            
        except FileNotFoundError:
            logger.error(f"XODR file not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load XODR map: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_map_data(self):
        """
        Get loaded map data.
        
        Returns:
            XODRMapData object containing all map information
        """
        return self.map_data
    
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
        return self.odr_map is not None
    
    def _generate_map_info(self, file_path: str) -> MapInfo:
        """
        Generate map information.
        
        Args:
            file_path: Path to map file
            
        Returns:
            Map information
        """
        if self.odr_map is None:
            raise ValueError("Map not loaded")
        
        # Calculate bounding box from all roads
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        
        roads = self.odr_map.get_roads()
        for road in roads:
            # Get road geometry bounds (simplified approach)
            # In a full implementation, we would calculate actual bounds from road geometries
            # For now, use road length as approximation
            # TODO: Implement proper bounding box calculation from road geometries
            pass
        
        # Use default bounding box for now
        # XODR uses local coordinates (meters), so we treat them as lat/lon for compatibility
        bounds = BoundingBox(
            min_lat=min_y if min_y != float('inf') else -100.0,
            max_lat=max_y if max_y != float('-inf') else 100.0,
            min_lon=min_x if min_x != float('inf') else -100.0,
            max_lon=max_x if max_x != float('-inf') else 100.0
        )
        
        return MapInfo(
            map_type="xodr",
            file_path=file_path,
            num_lanelets=0,  # XODR doesn't use lanelets
            bounds=bounds,
            coordinate_system="local",  # XODR uses local coordinates
            projector=None,  # No projector needed for XODR
            is_loaded=True
        )
