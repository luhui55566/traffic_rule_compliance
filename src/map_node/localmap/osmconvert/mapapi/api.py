"""
MapAPI module for querying map data.
"""

import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING

try:
    import lanelet2
    from lanelet2.core import LaneletMap, BasicPoint2d
    LANELET2_AVAILABLE = True
except ImportError:
    LANELET2_AVAILABLE = False
    LaneletMap = None
    BasicPoint2d = None

from map_node.map_common.base import Position, MapInfo
from map_node.maploader.utils import Projector
from .types import Lanelet, TrafficSign, SignType, LaneletType, FishboneLine, ConstructionSign, RampInfo

if TYPE_CHECKING:
    from lanelet2.core import LaneletMap as Lanelet2LaneletMap
    from lanelet2.core import BasicPoint2d as Lanelet2BasicPoint2d
else:
    Lanelet2LaneletMap = object  # type: ignore
    Lanelet2BasicPoint2d = object  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapAPI:
    """
    Map query API for accessing map data.
    
    This class provides methods to query lanelet information, speed limits,
    traffic signs, and other map-related data. It serves as main entry
    point for accessing map data in traffic rule compliance system.
    
    The MapAPI is initialized with map_data parameter containing:
    - lanelet_map: LaneletMap object from Lanelet2
    - projector: Projector for coordinate transformation
    - map_info: MapInfo with map metadata
    
    This parameter-based approach is suitable for ROS distributed nodes.
    """
    
    def __init__(self, map_data: dict):
        """
        Initialize MapAPI with map data.
        
        Args:
            map_data: Dictionary containing lanelet_map, projector, and map_info.
                      This parameter-based approach is suitable for ROS distributed nodes.
        """
        if not LANELET2_AVAILABLE:
            raise ImportError(
                "Lanelet2 is not installed. Please install it first:\n"
                "  sudo apt-get install liblanelet2-dev python3-lanelet2"
            )
        
        # Get data from parameter
        self.lanelet_map: Optional[Lanelet2LaneletMap] = map_data.get('lanelet_map')
        self.projector: Optional[Projector] = map_data.get('projector')
        self.map_info: Optional[MapInfo] = map_data.get('map_info')
        
        # Determine if using local coordinates based on map_info
        self.use_local_coords = (
            self.map_info is not None and
            self.map_info.coordinate_system == "local"
        )
        
        # Cache for performance optimization
        self._lanelet_cache: Dict[str, Lanelet] = {}
        self._cache_enabled = True
        
        if self.lanelet_map is not None:
            logger.info(f"MapAPI initialized with loaded map (coordinate_system={self.map_info.coordinate_system if self.map_info else 'unknown'})")
        else:
            logger.warning("No map loaded. MapAPI will not function properly.")
    
    def get_lanelet(self, position: Position, use_local_coords: bool = None) -> Optional[Lanelet]:
        """
        Get lanelet at given position.
        
        Args:
            position: Position (GPS or local coordinates depending on use_local_coords)
            use_local_coords: If True, treat position as local coordinates (x, y).
                            If False, treat as GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            Lanelet information, or None if not on any lanelet
        """
        if self.lanelet_map is None:
            return None
        
        # Determine coordinate system to use
        if use_local_coords is None:
            use_local_coords = self.use_local_coords
        
        try:
            # Convert position to map coordinates
            if use_local_coords:
                # For local coordinates, use position.latitude as x, position.longitude as y
                point = BasicPoint2d(position.latitude, position.longitude)
            else:
                # For GPS coordinates, convert using projector
                if self.projector is None:
                    logger.warning("Projector not available for GPS coordinates")
                    return None
                point = self._gps_to_map_point(position)
            
            # Find nearest lanelet using Lanelet2
            nearest = lanelet2.geometry.findNearest(
                self.lanelet_map.laneletLayer, point, 1
            )
            
            if not nearest:
                return None
            
            # findNearest returns list of (distance, lanelet) tuples
            lanelet2_lanelet = nearest[0][1]
            
            # Check if point is actually inside lanelet
            if not lanelet2.geometry.inside(lanelet2_lanelet, point):
                return None
            
            # Convert to unified Lanelet format
            return self._convert_lanelet(lanelet2_lanelet, use_local_coords)
            
        except Exception as e:
            logger.error(f"Error getting lanelet: {e}")
            return None
    
    def get_lanelet_by_id(self, lanelet_id: str, use_local_coords: bool = None) -> Optional[Lanelet]:
        """
        Get lanelet by ID.
        
        Args:
            lanelet_id: Lanelet ID
            use_local_coords: If True, use local coordinates (x, y) for boundaries.
                            If False, convert to GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            Lanelet information, or None if not found
        """
        if self.lanelet_map is None:
            return None
        
        # Check cache first
        if self._cache_enabled and lanelet_id in self._lanelet_cache:
            return self._lanelet_cache[lanelet_id]
        
        try:
            # Search for lanelet by ID
            for lanelet2_lanelet in self.lanelet_map.laneletLayer:
                if str(lanelet2_lanelet.id) == lanelet_id:
                    converted = self._convert_lanelet(lanelet2_lanelet, use_local_coords)
                    # Cache the result
                    if self._cache_enabled:
                        self._lanelet_cache[lanelet_id] = converted
                    return converted
            return None
        except Exception as e:
            logger.error(f"Error getting lanelet by ID: {e}")
            return None
    
    def get_speed_limit(self, position: Position, use_local_coords: bool = None) -> Optional[float]:
        """
        Get speed limit at given position.
        
        Args:
            position: Position (GPS or local coordinates depending on use_local_coords)
            use_local_coords: If True, treat position as local coordinates (x, y).
                            If False, treat as GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            Speed limit in km/h, or None if no limit
        """
        lanelet = self.get_lanelet(position, use_local_coords)
        if lanelet is None:
            return None
        return lanelet.speed_limit
    
    def get_traffic_signs(self, position: Position, radius: float = 100.0, use_local_coords: bool = None) -> List[TrafficSign]:
        """
        Get traffic signs within a radius of given position.
        
        Args:
            position: Center position
            radius: Search radius in meters
            use_local_coords: If True, treat position as local coordinates (x, y).
                            If False, treat as GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            List of traffic signs
        """
        if self.lanelet_map is None:
            return []
        
        # Determine coordinate system to use
        if use_local_coords is None:
            use_local_coords = self.use_local_coords
        
        try:
            # Convert position to map coordinates
            if use_local_coords:
                point = BasicPoint2d(position.latitude, position.longitude)
            else:
                if self.projector is None:
                    logger.warning("Projector not available for GPS coordinates")
                    return []
                point = self._gps_to_map_point(position)
            
            signs = []
            
            # Search in regulatory element layer for traffic signs
            for element in self.lanelet_map.regulatoryElementLayer:
                # Check if this is a traffic sign element
                if hasattr(element, 'parameters'):
                    params = element.parameters
                    if 'subtype' in params:
                        sign_type = self._parse_sign_type(params['subtype'])
                        if sign_type != SignType.UNKNOWN:
                            # Get position from the element
                            element_pos = self._get_element_position(element, use_local_coords)
                            if element_pos:
                                distance = self._calculate_distance(position, element_pos, use_local_coords)
                                if distance <= radius:
                                    value = params.get('value', None)
                                    signs.append(TrafficSign(
                                        id=str(element.id),
                                        sign_type=sign_type,
                                        position=element_pos,
                                        value=value
                                    ))
            
            return signs
            
        except Exception as e:
            logger.error(f"Error getting traffic signs: {e}")
            return []
    
    def get_nearby_lanelets(self, position: Position, radius: float = 50.0,
                           max_count: int = 10, use_local_coords: bool = None) -> List[Lanelet]:
        """
        Get nearby lanelets within a radius.
        
        Args:
            position: Center position
            radius: Search radius in meters
            max_count: Maximum number of lanelets to return
            use_local_coords: If True, treat position as local coordinates (x, y).
                            If False, treat as GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            List of nearby lanelets
        """
        if self.lanelet_map is None:
            return []
        
        # Determine coordinate system to use
        if use_local_coords is None:
            use_local_coords = self.use_local_coords
        
        try:
            # Convert position to map coordinates
            if use_local_coords:
                point = BasicPoint2d(position.latitude, position.longitude)
            else:
                if self.projector is None:
                    logger.warning("Projector not available for GPS coordinates")
                    return []
                point = self._gps_to_map_point(position)
            
            # Find nearest lanelets
            nearest = lanelet2.geometry.findNearest(
                self.lanelet_map.laneletLayer, point, max_count
            )
            
            lanelets = []
            for distance, lanelet2_lanelet in nearest:
                if distance <= radius:
                    lanelets.append(self._convert_lanelet(lanelet2_lanelet, use_local_coords))
            
            return lanelets
            
        except Exception as e:
            logger.error(f"Error getting nearby lanelets: {e}")
            return []
    
    def get_lanelet_topology(self, lanelet_id: str) -> Dict[str, List[str]]:
        """
        Get lanelet topology information.
        
        Args:
            lanelet_id: Lanelet ID
            
        Returns:
            Dictionary with 'left', 'right', 'following', 'preceding' keys
        """
        if self.lanelet_map is None:
            return {}
        
        try:
            # Find the lanelet
            lanelet2_lanelet = None
            for ll in self.lanelet_map.laneletLayer:
                if str(ll.id) == lanelet_id:
                    lanelet2_lanelet = ll
                    break
            
            if lanelet2_lanelet is None:
                return {}
            
            topology = {
                'left': [str(l.id) for l in lanelet2_lanelet.left],
                'right': [str(l.id) for l in lanelet2_lanelet.right],
                'following': [str(l.id) for l in lanelet2_lanelet.following],
                'preceding': [str(l.id) for l in lanelet2_lanelet.preceding]
            }
            
            return topology
            
        except Exception as e:
            logger.error(f"Error getting lanelet topology: {e}")
            return {}
    
    def get_map_info(self) -> Optional[MapInfo]:
        """
        Get map information.
        
        Returns:
            Map information, or None if not available
        """
        return self.map_info
    
    def is_loaded(self) -> bool:
        """
        Check if map is loaded.
        
        Returns:
            True if map is loaded
        """
        return self.lanelet_map is not None
    
    def clear_cache(self) -> None:
        """Clear lanelet cache."""
        self._lanelet_cache.clear()
        logger.info("Lanelet cache cleared")
    
    def enable_cache(self, enabled: bool = True) -> None:
        """
        Enable or disable caching.
        
        Args:
            enabled: Whether to enable caching
        """
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
        logger.info(f"Cache {'enabled' if enabled else 'disabled'}")
    
    # ==================== Custom Query Methods ====================
    
    def query_ramp_info(self, position: Position, use_local_coords: bool = None) -> Optional[RampInfo]:
        """
        Query ramp information at given position.
        
        This is a custom query method for identifying ramps (entry/exit lanes).
        
        Args:
            position: Position (GPS or local coordinates depending on use_local_coords)
            use_local_coords: If True, treat position as local coordinates (x, y).
                            If False, treat as GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            Ramp information, or None if not on a ramp
        """
        lanelet = self.get_lanelet(position, use_local_coords)
        if lanelet is None:
            return None
        
        # Check if lanelet type is ramp-related
        if lanelet.lanelet_type in [LaneletType.RAMP, LaneletType.ENTRY, LaneletType.EXIT]:
            # Get connected lanelets
            topology = self.get_lanelet_topology(lanelet.id)
            
            # Determine ramp type based on topology
            ramp_type = "connector"
            if lanelet.lanelet_type == LaneletType.ENTRY:
                ramp_type = "entry"
            elif lanelet.lanelet_type == LaneletType.EXIT:
                ramp_type = "exit"
            
            return RampInfo(
                id=lanelet.id,
                ramp_type=ramp_type,
                position=position,
                length=lanelet.length(),
                connected_lanelets=topology.get('following', []) + topology.get('preceding', [])
            )
        
        return None
    
    def query_structured_road(self, position: Position, use_local_coords: bool = None) -> bool:
        """
        Query if position is on a structured road.
        
        This is a custom query method for identifying structured roads
        (highways, main roads with clear lane markings).
        
        Args:
            position: Position (GPS or local coordinates depending on use_local_coords)
            use_local_coords: If True, treat position as local coordinates (x, y).
                            If False, treat as GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            True if on a structured road
        """
        lanelet = self.get_lanelet(position, use_local_coords)
        if lanelet is None:
            return False
        
        # Structured roads are typically highway or rural types
        return lanelet.lanelet_type in [LaneletType.HIGHWAY, LaneletType.RURAL]
    
    def query_fishbone_lines(self, position: Position, radius: float = 100.0, use_local_coords: bool = None) -> List[FishboneLine]:
        """
        Query fishbone lines near given position.
        
        This is a custom query method for identifying fishbone lines
        (deceleration markings on highways).
        
        Args:
            position: Center position
            radius: Search radius in meters
            use_local_coords: If True, treat position as local coordinates (x, y).
                            If False, treat as GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            List of fishbone lines
        """
        # This would typically query from a custom layer or attribute
        # For now, we'll search for traffic signs with fishbone type
        signs = self.get_traffic_signs(position, radius, use_local_coords)
        fishbone_lines = []
        
        for sign in signs:
            if sign.sign_type == SignType.FISHBONE:
                fishbone_lines.append(FishboneLine(
                    id=sign.id,
                    position=sign.position,
                    direction=sign.direction if sign.direction else 0.0,
                    length=50.0  # Default length, should be from map data
                ))
        
        return fishbone_lines
    
    def query_construction_signs(self, position: Position, radius: float = 200.0, use_local_coords: bool = None) -> List[ConstructionSign]:
        """
        Query construction signs near given position.
        
        This is a custom query method for identifying construction zones.
        
        Args:
            position: Center position
            radius: Search radius in meters
            use_local_coords: If True, treat position as local coordinates (x, y).
                            If False, treat as GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            List of construction signs
        """
        signs = self.get_traffic_signs(position, radius, use_local_coords)
        construction_signs = []
        
        for sign in signs:
            if sign.sign_type == SignType.CONSTRUCTION:
                construction_signs.append(ConstructionSign(
                    id=sign.id,
                    position=sign.position,
                    direction=sign.direction if sign.direction else 0.0,
                    distance_threshold=100.0  # Default threshold
                ))
        
        return construction_signs
    
    # ==================== Private Helper Methods ====================
    
    def _gps_to_map_point(self, position: Position) -> Lanelet2BasicPoint2d:
        """
        Convert GPS coordinates to map coordinates.
        
        Args:
            position: GPS position
            
        Returns:
            Map coordinate point
        """
        if self.projector is None:
            raise ValueError("Projector not set")
        return self.projector.forward(position)
    
    def _map_point_to_gps(self, point: Lanelet2BasicPoint2d) -> Position:
        """
        Convert map coordinates to GPS coordinates.
        
        Args:
            point: Map coordinate point
            
        Returns:
            GPS position
        """
        if self.projector is None:
            raise ValueError("Projector not set")
        return self.projector.reverse(point)
    
    def _convert_lanelet(self, lanelet2_lanelet, use_local_coords: bool = None) -> Lanelet:
        """
        Convert Lanelet2 lanelet to unified Lanelet format.
        
        Args:
            lanelet2_lanelet: Lanelet2 lanelet object
            use_local_coords: If True, use local coordinates (x, y) for boundaries.
                            If False, convert to GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            Unified Lanelet object
        """
        # Determine coordinate system to use
        if use_local_coords is None:
            use_local_coords = self.use_local_coords
        
        # Convert left boundary
        left_bound = []
        for point in lanelet2_lanelet.leftBound:
            if use_local_coords:
                # For local coordinates, use x, y directly
                gps_pos = Position(latitude=point.x, longitude=point.y)
            else:
                # For GPS coordinates, convert using projector
                gps_pos = self._map_point_to_gps(Lanelet2BasicPoint2d(point.x, point.y))
            left_bound.append(gps_pos)
        
        # Convert right boundary
        right_bound = []
        for point in lanelet2_lanelet.rightBound:
            if use_local_coords:
                # For local coordinates, use x, y directly
                gps_pos = Position(latitude=point.x, longitude=point.y)
            else:
                # For GPS coordinates, convert using projector
                gps_pos = self._map_point_to_gps(Lanelet2BasicPoint2d(point.x, point.y))
            right_bound.append(gps_pos)
        
        # Get speed limit from traffic rules
        speed_limit = None
        try:
            for rule in lanelet2_lanelet.trafficRules:
                if hasattr(rule, 'speedLimit'):
                    speed_limit = rule.speedLimit
                    break
        except Exception:
            pass
        
        # Determine lanelet type from attributes
        lanelet_type = LaneletType.UNKNOWN
        try:
            if hasattr(lanelet2_lanelet, 'attributes'):
                attrs = lanelet2_lanelet.attributes
                if 'subtype' in attrs:
                    subtype = attrs['subtype'].lower()
                    if 'highway' in subtype:
                        lanelet_type = LaneletType.HIGHWAY
                    elif 'rural' in subtype:
                        lanelet_type = LaneletType.RURAL
                    elif 'urban' in subtype:
                        lanelet_type = LaneletType.URBAN
                    elif 'ramp' in subtype:
                        lanelet_type = LaneletType.RAMP
                    elif 'exit' in subtype:
                        lanelet_type = LaneletType.EXIT
                    elif 'entry' in subtype:
                        lanelet_type = LaneletType.ENTRY
        except Exception:
            pass
        
        return Lanelet(
            id=str(lanelet2_lanelet.id),
            left_bound=left_bound,
            right_bound=right_bound,
            speed_limit=speed_limit,
            lanelet_type=lanelet_type
        )
    
    def _parse_sign_type(self, subtype: str) -> SignType:
        """
        Parse sign type from subtype string.
        
        Args:
            subtype: Sign subtype string
            
        Returns:
            SignType enum value
        """
        subtype_lower = subtype.lower()
        
        if 'speed' in subtype_lower:
            return SignType.SPEED_LIMIT
        elif 'stop' in subtype_lower:
            return SignType.STOP
        elif 'yield' in subtype_lower or 'give' in subtype_lower:
            return SignType.YIELD
        elif 'no_entry' in subtype_lower or 'forbidden' in subtype_lower:
            return SignType.NO_ENTRY
        elif 'one_way' in subtype_lower:
            return SignType.ONE_WAY
        elif 'construction' in subtype_lower or 'work' in subtype_lower:
            return SignType.CONSTRUCTION
        elif 'fishbone' in subtype_lower or 'deceleration' in subtype_lower:
            return SignType.FISHBONE
        elif 'traffic_light' in subtype_lower or 'light' in subtype_lower:
            return SignType.TRAFFIC_LIGHT
        else:
            return SignType.UNKNOWN
    
    def _get_element_position(self, element, use_local_coords: bool = None) -> Optional[Position]:
        """
        Get position from a regulatory element.
        
        Args:
            element: Regulatory element
            use_local_coords: If True, use local coordinates (x, y).
                            If False, convert to GPS coordinates (lat, lon).
                            If None, use the map's coordinate system setting.
            
        Returns:
            Position, or None if not available
        """
        # Determine coordinate system to use
        if use_local_coords is None:
            use_local_coords = self.use_local_coords
        
        try:
            # Try to get position from element's parameters
            if hasattr(element, 'parameters'):
                params = element.parameters
                if 'position' in params:
                    pos = params['position']
                    if use_local_coords:
                        # For local coordinates, use x, y directly
                        return Position(latitude=pos.x if hasattr(pos, 'x') else pos.lat,
                                     longitude=pos.y if hasattr(pos, 'y') else pos.lon)
                    else:
                        # For GPS coordinates, use lat, lon
                        return Position(latitude=pos.lat, longitude=pos.lon)
            
            # Try to get position from element's references
            if hasattr(element, 'refers'):
                for ref in element.refers:
                    if hasattr(ref, 'x') and hasattr(ref, 'y'):
                        if use_local_coords:
                            # For local coordinates, use x, y directly
                            return Position(latitude=ref.x, longitude=ref.y)
                        else:
                            # For GPS coordinates, convert using projector
                            return self._map_point_to_gps(BasicPoint2d(ref.x, ref.y))
            
            return None
        except Exception:
            return None
    
    def _calculate_distance(self, pos1: Position, pos2: Position, use_local_coords: bool = None) -> float:
        """
        Calculate distance between two positions.
        
        Args:
            pos1: First position
            pos2: Second position
            use_local_coords: If True, use Euclidean distance for local coordinates.
                            If False, use Haversine formula for GPS coordinates.
                            If None, use the map's coordinate system setting.
            
        Returns:
            Distance in meters
        """
        # Determine coordinate system to use
        if use_local_coords is None:
            use_local_coords = self.use_local_coords
        
        import math
        
        if use_local_coords:
            # For local coordinates, use Euclidean distance
            dx = pos2.latitude - pos1.latitude  # Using latitude as x
            dy = pos2.longitude - pos1.longitude  # Using longitude as y
            return math.sqrt(dx * dx + dy * dy)
        else:
            # For GPS coordinates, use Haversine formula
            lat1, lon1 = math.radians(pos1.latitude), math.radians(pos1.longitude)
            lat2, lon2 = math.radians(pos2.latitude), math.radians(pos2.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            
            R = 6371000  # Earth's radius in meters
            return R * c
