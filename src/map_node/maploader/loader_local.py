"""
Map loader for loading OSM format maps using local_x/local_y tags directly.
"""

import logging
from typing import Optional, TYPE_CHECKING
import xml.etree.ElementTree as ET

try:
    from lanelet2.core import LaneletMap, Point3d, LineString3d, Lanelet, RegulatoryElement
    from lanelet2.io import Origin
    LANELET2_AVAILABLE = True
except ImportError:
    LANELET2_AVAILABLE = False
    LaneletMap = None
    Point3d = None
    LineString3d = None
    Lanelet = None
    RegulatoryElement = None
    Origin = None

from map_node.map_common.base import Position, BoundingBox, MapInfo

if TYPE_CHECKING:
    from lanelet2.core import LaneletMap as Lanelet2LaneletMap
else:
    Lanelet2LaneletMap = object  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalMapLoader:
    """OSM map loader using local_x/local_y tags directly."""
    
    def __init__(self):
        """Initialize map loader."""
        if not LANELET2_AVAILABLE:
            raise ImportError(
                "Lanelet2 is not installed. Please install it first:\n"
                "  sudo apt-get install liblanelet2-dev python3-lanelet2"
            )
        self.lanelet_map: Optional[Lanelet2LaneletMap] = None
        self.map_info: Optional[MapInfo] = None
        self.points = {}  # Store points by ID
        self.linestrings = {}  # Store linestrings by ID
        self.lanelets = {}  # Store lanelets by ID
    
    def load_map(self, file_path: str) -> bool:
        """
        Load OSM map file using local_x/local_y tags.
        
        Args:
            file_path: Path to OSM file
            
        Returns:
            True if loading succeeded, False otherwise
        """
        try:
            logger.info(f"Loading OSM map from: {file_path}")
            
            # Parse OSM file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Clear previous data
            self.points = {}
            self.linestrings = {}
            self.lanelets = {}
            
            # Parse points
            self._parse_points(root)
            logger.info(f"Loaded {len(self.points)} points")
            
            # Parse linestrings
            self._parse_linestrings(root)
            logger.info(f"Loaded {len(self.linestrings)} linestrings")
            
            # Parse lanelets
            self._parse_lanelets(root)
            logger.info(f"Loaded {len(self.lanelets)} lanelets")
            
            # Create LaneletMap
            self.lanelet_map = LaneletMap()
            
            # Add points to map
            for point in self.points.values():
                self.lanelet_map.add(point)
            
            # Add linestrings to map
            for linestring in self.linestrings.values():
                self.lanelet_map.add(linestring)
            
            # Add lanelets to map
            for lanelet in self.lanelets.values():
                self.lanelet_map.add(lanelet)
            
            # Generate map information
            self.map_info = self._generate_map_info(file_path)
            
            logger.info(f"Map loaded successfully: {self.map_info}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Map file not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load OSM map: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _parse_points(self, root):
        """Parse points from OSM file."""
        for node in root.findall('node'):
            node_id = node.get('id')
            local_x = None
            local_y = None
            ele = 0.0
            
            for tag in node.findall('tag'):
                k = tag.get('k')
                v = tag.get('v')
                if k == 'local_x':
                    local_x = float(v)
                elif k == 'local_y':
                    local_y = float(v)
                elif k == 'ele':
                    ele = float(v)
            
            if local_x is not None and local_y is not None:
                # Create Point3d using local_x/local_y
                point = Point3d(int(node_id), local_x, local_y, ele)
                self.points[node_id] = point
    
    def _parse_linestrings(self, root):
        """Parse linestrings from OSM file."""
        for way in root.findall('way'):
            way_id = way.get('id')
            node_refs = []
            
            for nd in way.findall('nd'):
                ref = nd.get('ref')
                node_refs.append(ref)
            
            # All ways are linestrings in this format
            if node_refs:
                # Get points for this linestring
                points = []
                for ref in node_refs:
                    if ref in self.points:
                        points.append(self.points[ref])
                
                if len(points) >= 2:
                    # Create LineString3d
                    linestring = LineString3d(int(way_id), points)
                    self.linestrings[way_id] = linestring
    
    def _parse_lanelets(self, root):
        """Parse lanelets from OSM file."""
        for relation in root.findall('relation'):
            relation_id = relation.get('id')
            
            # Check if this relation is a lanelet
            is_lanelet = False
            left_bound_id = None
            right_bound_id = None
            
            for tag in relation.findall('tag'):
                k = tag.get('k')
                v = tag.get('v')
                if k == 'type' and v == 'lanelet':
                    is_lanelet = True
            
            if not is_lanelet:
                continue
            
            # Get boundary references
            for member in relation.findall('member'):
                role = member.get('role')
                ref = member.get('ref')
                if role == 'left':
                    left_bound_id = ref
                elif role == 'right':
                    right_bound_id = ref
            
            # If we have boundary references, create lanelet
            if left_bound_id and right_bound_id:
                if left_bound_id in self.linestrings and right_bound_id in self.linestrings:
                    left_bound = self.linestrings[left_bound_id]
                    right_bound = self.linestrings[right_bound_id]
                    
                    # Create lanelet
                    lanelet = Lanelet(int(relation_id), left_bound, right_bound)
                    self.lanelets[relation_id] = lanelet
    
    def get_map_data(self):
        """
        Get loaded map data for passing to MapManager.
        
        Returns:
            Dictionary containing lanelet_map and map_info
        """
        return {
            'lanelet_map': self.lanelet_map,
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
    
    def _generate_map_info(self, file_path: str) -> MapInfo:
        """
        Generate map information.
        
        Args:
            file_path: Path to map file
            
        Returns:
            Map information
        """
        if self.lanelet_map is None:
            raise ValueError("Map not loaded")
        
        # Use default bounding box for now
        # TODO: Implement proper bounding box calculation
        bounds = BoundingBox(
            min_lat=0.0,
            max_lat=0.0,
            min_lon=0.0,
            max_lon=0.0
        )
        
        return MapInfo(
            map_type="osm_local",
            file_path=file_path,
            num_lanelets=len(self.lanelet_map.laneletLayer),
            bounds=bounds,
            coordinate_system="local",
            projector=None,
            is_loaded=True
        )
