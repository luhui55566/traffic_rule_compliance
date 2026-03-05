"""
Utility for quickly finding which road(s) a position is on in an XODR map.

pyOpenDRIVE doesn't have a built-in method for this, so we need to iterate
through roads and check if the position projects onto each road.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

try:
    from pyOpenDRIVE.Road import PyRoad
    from pyOpenDRIVE.Lane import PyLane
    from pyOpenDRIVE.LaneSection import PyLaneSection
    PYOPENDRIVE_AVAILABLE = True
except ImportError:
    PYOPENDRIVE_AVAILABLE = False
    PyRoad = None
    PyLane = None
    PyLaneSection = None

logger = logging.getLogger(__name__)


@dataclass
class RoadPosition:
    """Represents a position on a road with full Frenet coordinates."""
    road_id: str
    s: float  # Longitudinal position along road (meters)
    t: float  # Lateral offset from road centerline (meters)
    h: float  # Height above road (meters)
    lane_id: Optional[int] = None
    lane_section_s0: Optional[float] = None
    distance_to_road: float = 0.0  # Distance from query point to road centerline
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'road_id': self.road_id,
            's': self.s,
            't': self.t,
            'h': self.h,
            'lane_id': self.lane_id,
            'lane_section_s0': self.lane_section_s0,
            'distance_to_road': self.distance_to_road
        }


class XODRRoadFinder:
    """
    Fast utility to find which road(s) a world position (x, y) is on.
    
    This class provides methods to:
    1. Find all roads near a position
    2. Find the closest road to a position
    3. Get the exact Frenet coordinates (s, t) on a road
    
    Usage:
        finder = XODRRoadFinder(odr_map)
        
        # Find closest road
        road_pos = finder.find_closest_road(x, y)
        if road_pos:
            print(f"On road {road_pos.road_id} at s={road_pos.s}, t={road_pos.t}")
        
        # Find all roads within 10 meters
        road_positions = finder.find_roads_near_position(x, y, max_distance=10.0)
    """
    
    def __init__(self, odr_map, cache_road_geometry: bool = True):
        """
        Initialize the road finder.
        
        Args:
            odr_map: pyOpenDRIVE map object
            cache_road_geometry: If True, cache road geometry samples for faster lookup
        """
        if not PYOPENDRIVE_AVAILABLE:
            raise ImportError("pyOpenDRIVE is not installed")
        
        self.odr_map = odr_map
        self.roads = odr_map.get_roads()
        self.cache_road_geometry = cache_road_geometry
        
        # Cache for road geometry samples: road_id -> [(s, x, y), ...]
        self._road_sample_cache: Dict[str, List[Tuple[float, float, float]]] = {}
        
        # Build road ID lookup
        self._road_by_id: Dict[str, PyRoad] = {}
        for road in self.roads:
            road_id = road.id.decode() if isinstance(road.id, bytes) else str(road.id)
            self._road_by_id[road_id] = road
        
        logger.info(f"XODRRoadFinder initialized with {len(self.roads)} roads")
    
    def get_road_by_id(self, road_id: str) -> Optional[PyRoad]:
        """Get road by ID."""
        return self._road_by_id.get(road_id)
    
    def _sample_road_geometry(self, road: PyRoad, sample_step: float = 5.0) -> List[Tuple[float, float, float]]:
        """
        Sample road centerline geometry at regular intervals.
        
        Args:
            road: PyRoad object
            sample_step: Sampling interval in meters
            
        Returns:
            List of (s, x, y) tuples
        """
        road_id = road.id.decode() if isinstance(road.id, bytes) else str(road.id)
        
        # Check cache
        if self.cache_road_geometry and road_id in self._road_sample_cache:
            return self._road_sample_cache[road_id]
        
        samples = []
        road_length = road.length
        
        # Sample along the road
        s = 0.0
        while s <= road_length:
            try:
                pos = road.get_xyz(s, 0.0, 0.0)
                samples.append((s, pos.array[0], pos.array[1]))
            except Exception:
                pass  # Skip points that fail
            s += sample_step
        
        # Always include end point
        if samples and samples[-1][0] < road_length:
            try:
                pos = road.get_xyz(road_length, 0.0, 0.0)
                samples.append((road_length, pos.array[0], pos.array[1]))
            except Exception:
                pass
        
        # Cache results
        if self.cache_road_geometry:
            self._road_sample_cache[road_id] = samples
        
        return samples
    
    def _project_point_to_line_segment(self, px: float, py: float,
                                        x1: float, y1: float,
                                        x2: float, y2: float) -> Tuple[float, float, float]:
        """
        Project a point onto a line segment.
        
        Args:
            px, py: Point coordinates
            x1, y1: Line segment start
            x2, y2: Line segment end
            
        Returns:
            Tuple of (distance, projected_x, projected_y)
        """
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            # Degenerate segment (point)
            dist = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
            return dist, x1, y1
        
        # Parameter t for projection onto infinite line
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        
        # Clamp to segment
        t = max(0.0, min(1.0, t))
        
        # Projected point
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        # Distance
        dist = ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5
        
        return dist, proj_x, proj_y
    
    def _find_closest_s_on_road(self, road: PyRoad, x: float, y: float,
                                 sample_step: float = 5.0,
                                 z: float = None) -> Tuple[float, float]:
        """
        Find the closest s coordinate on a road to a given (x, y) point.
        
        Uses a two-step approach:
        1. Sample road at regular intervals to find approximate region
        2. Binary search to refine the s value
        
        Args:
            road: PyRoad object
            x, y: World coordinates (horizontal)
            sample_step: Initial sampling step in meters
            z: World coordinate (height). If provided, 3D distance is used.
            
        Returns:
            Tuple of (s, distance) where s is the longitudinal coordinate
            and distance is the distance to road centerline (2D or 3D depending on z)
        """
        samples = self._sample_road_geometry(road, sample_step)
        
        if not samples:
            return 0.0, float('inf')
        
        # Find closest segment
        min_dist = float('inf')
        best_s = 0.0
        
        for i in range(len(samples) - 1):
            s1, x1, y1 = samples[i]
            s2, x2, y2 = samples[i + 1]
            
            dist, proj_x, proj_y = self._project_point_to_line_segment(x, y, x1, y1, x2, y2)
            
            if dist < min_dist:
                min_dist = dist
                # Interpolate s value
                segment_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if segment_length > 0:
                    t = ((proj_x - x1) * (x2 - x1) + (proj_y - y1) * (y2 - y1)) / (segment_length ** 2)
                    t = max(0.0, min(1.0, t))
                    best_s = s1 + t * (s2 - s1)
                else:
                    best_s = s1
        
        # Refine with binary search around best_s
        best_s, min_dist = self._refine_s_coordinate(road, x, y, best_s, search_range=sample_step * 2, z=z)
        
        return best_s, min_dist
    
    def _refine_s_coordinate(self, road: PyRoad, x: float, y: float,
                             s_guess: float, search_range: float = 10.0,
                             tolerance: float = 0.01,
                             z: float = None) -> Tuple[float, float]:
        """
        Refine s coordinate using golden section search.
        
        Args:
            road: PyRoad object
            x, y: World coordinates (horizontal)
            s_guess: Initial s estimate
            search_range: Search range around s_guess
            tolerance: Convergence tolerance in meters
            z: World coordinate (height). If provided, 3D distance is used.
            
        Returns:
            Tuple of (refined_s, distance)
        """
        road_length = road.length
        
        # Search bounds
        s_low = max(0.0, s_guess - search_range)
        s_high = min(road_length, s_guess + search_range)
        
        if s_high <= s_low:
            s_high = s_low + 0.1
        
        def distance_at_s(s: float) -> float:
            """Get distance from point to road at given s."""
            try:
                pos = road.get_xyz(s, 0.0, 0.0)
                if z is not None:
                    # Use 3D distance when z is provided
                    return ((x - pos.array[0]) ** 2 + (y - pos.array[1]) ** 2 + (z - pos.array[2]) ** 2) ** 0.5
                else:
                    # Use 2D distance (horizontal only)
                    return ((x - pos.array[0]) ** 2 + (y - pos.array[1]) ** 2) ** 0.5
            except Exception:
                return float('inf')
        
        # Golden section search
        phi = (1 + 5 ** 0.5) / 2  # Golden ratio
        resphi = 2 - phi
        
        s1 = s_low + resphi * (s_high - s_low)
        s2 = s_high - resphi * (s_high - s_low)
        
        f1 = distance_at_s(s1)
        f2 = distance_at_s(s2)
        
        iteration = 0
        max_iterations = 20
        
        while s_high - s_low > tolerance and iteration < max_iterations:
            if f1 > f2:
                s_low = s1
                s1 = s2
                f1 = f2
                s2 = s_high - resphi * (s_high - s_low)
                f2 = distance_at_s(s2)
            else:
                s_high = s2
                s2 = s1
                f2 = f1
                s1 = s_low + resphi * (s_high - s_low)
                f1 = distance_at_s(s1)
            iteration += 1
        
        best_s = (s_low + s_high) / 2
        best_dist = distance_at_s(best_s)
        
        return best_s, best_dist
    
    def _get_t_coordinate(self, road: PyRoad, s: float, x: float, y: float) -> float:
        """
        Calculate the lateral offset (t) from road centerline.
        
        The t coordinate is positive to the left of the road (when looking in
        the direction of increasing s) and negative to the right.
        
        Args:
            road: PyRoad object
            s: Longitudinal coordinate
            x, y: World coordinates
            
        Returns:
            Lateral offset t (meters)
        """
        try:
            # Get road centerline position at s
            center_pos = road.get_xyz(s, 0.0, 0.0)
            cx, cy = center_pos.array[0], center_pos.array[1]
            
            # Get road direction (heading) at s
            delta_s = 0.1  # Small delta for tangent calculation
            if s + delta_s <= road.length:
                pos_ahead = road.get_xyz(s + delta_s, 0.0, 0.0)
            else:
                pos_ahead = road.get_xyz(road.length, 0.0, 0.0)
            
            dx = pos_ahead.array[0] - cx
            dy = pos_ahead.array[1] - cy
            
            # Normalize direction vector
            length = (dx * dx + dy * dy) ** 0.5
            if length > 0:
                dx /= length
                dy /= length
            
            # Vector from centerline to point
            px = x - cx
            py = y - cy
            
            # Cross product to determine sign
            # Positive cross product means point is to the left
            cross = dx * py - dy * px
            
            # Distance is the magnitude of perpendicular component
            # Project point onto perpendicular direction
            # Perpendicular direction: (-dy, dx) for left side
            t = cross  # This gives signed distance
            
            return t
            
        except Exception as e:
            logger.warning(f"Error calculating t coordinate: {e}")
            return 0.0
    
    def _find_lane_at_position(self, road: PyRoad, s: float, t: float) -> Optional[int]:
        """
        Find the lane ID at a given (s, t) position.
        
        Args:
            road: PyRoad object
            s: Longitudinal coordinate
            t: Lateral offset from centerline
            
        Returns:
            Lane ID or None if not on any lane
        """
        try:
            lanesections = road.get_lanesections()
            
            for lanesection in lanesections:
                s0 = lanesection.s0 if hasattr(lanesection, 's0') else 0.0
                s_end = road.get_lanesection_end(lanesection)
                
                # Check if s is in this lane section
                if s0 <= s <= s_end:
                    lanes = lanesection.get_lanes()
                    
                    # Check each lane
                    for lane in lanes:
                        lane_id = lane.id if hasattr(lane, 'id') else lane.lane_id
                        
                        # Get lane width at s
                        # Lane width is typically defined relative to lane center or edge
                        # For positive lane IDs (right side), t is negative
                        # For negative lane IDs (left side), t is positive
                        
                        # Get lane boundaries at s
                        # This is simplified - actual implementation would need to
                        # calculate lane width from road profile
                        width = lane.get_width(s) if hasattr(lane, 'get_width') else 3.0
                        
                        # Approximate lane boundaries
                        if lane_id > 0:
                            # Right side lanes (t < 0)
                            t_outer = -((lane_id - 1) * width + width)
                            t_inner = -(lane_id - 1) * width
                            if t_outer <= t <= t_inner:
                                return lane_id
                        elif lane_id < 0:
                            # Left side lanes (t > 0)
                            t_inner = (abs(lane_id) - 1) * width
                            t_outer = (abs(lane_id) - 1) * width + width
                            if t_inner <= t <= t_outer:
                                return lane_id
                        else:
                            # Center lane (lane_id == 0)
                            if abs(t) < width / 2:
                                return 0
                    
                    return None
            
            return None
            
        except Exception as e:
            logger.warning(f"Error finding lane: {e}")
            return None
    
    def _get_road_width_at_s(self, road: PyRoad, s: float) -> Tuple[float, float]:
        """
        Calculate the left and right road widths at a given s coordinate.
        
        In XODR:
        - Left side (t > 0): negative lane IDs (-1, -2, ...)
        - Right side (t < 0): positive lane IDs (1, 2, ...)
        
        Args:
            road: PyRoad object
            s: Longitudinal coordinate
            
        Returns:
            Tuple of (left_width, right_width) in meters
        """
        try:
            left_width = 0.0   # Width on positive t side (negative lane IDs)
            right_width = 0.0  # Width on negative t side (positive lane IDs)
            
            lanesections = road.get_lanesections()
            
            for lanesection in lanesections:
                s0 = lanesection.s0 if hasattr(lanesection, 's0') else 0.0
                s_end = road.get_lanesection_end(lanesection)
                
                # Check if s is in this lane section
                if s0 <= s <= s_end:
                    lanes = lanesection.get_lanes()
                    
                    for lane in lanes:
                        lane_id = lane.id if hasattr(lane, 'id') else lane.lane_id
                        
                        # Skip center lane (lane_id == 0)
                        if lane_id == 0:
                            continue
                        
                        # Get lane width at s (relative to lane section start)
                        s_relative = s - s0
                        width = 3.5  # Default width
                        if hasattr(lane, 'get_width'):
                            try:
                                width = lane.get_width(s_relative)
                            except Exception:
                                pass
                        
                        # Negative lane IDs are on the left (positive t)
                        if lane_id < 0:
                            left_width += width
                        # Positive lane IDs are on the right (negative t)
                        else:
                            right_width += width
                    
                    break  # Found the right lane section
            
            # If no width calculated, use defaults
            if left_width == 0.0 and right_width == 0.0:
                left_width = 5.0
                right_width = 5.0
                
            return left_width, right_width
            
        except Exception as e:
            logger.debug(f"Error calculating road width: {e}")
            return 5.0, 5.0  # Default fallback
    
    def find_roads_near_position(self, x: float, y: float, z: float = None,
                                  max_distance: float = 50.0,
                                  sample_step: float = 5.0) -> List[RoadPosition]:
        """
        Find all roads near a given world position.
        
        Args:
            x, y: World coordinates (horizontal)
            z: World coordinate (height/altitude). If provided, 3D distance is used
               to distinguish between elevated roads and ground-level roads.
            max_distance: Maximum distance to search (meters)
            sample_step: Sampling step for road geometry (meters)
            
        Returns:
            List of RoadPosition objects sorted by distance
        """
        results = []
        
        for road in self.roads:
            road_id = road.id.decode() if isinstance(road.id, bytes) else str(road.id)
            
            # Find closest s and distance
            s, distance = self._find_closest_s_on_road(road, x, y, sample_step, z=z)
            
            if distance <= max_distance:
                # Calculate t coordinate
                t = self._get_t_coordinate(road, s, x, y)
                
                # Find lane
                lane_id = self._find_lane_at_position(road, s, t)
                
                # Find lane section s0
                lane_section_s0 = None
                for lanesection in road.get_lanesections():
                    s0 = lanesection.s0 if hasattr(lanesection, 's0') else 0.0
                    s_end = road.get_lanesection_end(lanesection)
                    if s0 <= s <= s_end:
                        lane_section_s0 = s0
                        break
                
                road_pos = RoadPosition(
                    road_id=road_id,
                    s=s,
                    t=t,
                    h=0.0,
                    lane_id=lane_id,
                    lane_section_s0=lane_section_s0,
                    distance_to_road=distance
                )
                results.append(road_pos)
        
        # Sort by distance
        results.sort(key=lambda rp: rp.distance_to_road)
        
        return results
    
    def find_closest_road(self, x: float, y: float, z: float = None,
                          sample_step: float = 5.0) -> Optional[RoadPosition]:
        """
        Find the closest road to a given world position.
        
        Args:
            x, y: World coordinates (horizontal)
            z: World coordinate (height). If provided, 3D distance is used
               to distinguish between elevated roads and ground-level roads.
            sample_step: Sampling step for road geometry (meters)
            
        Returns:
            RoadPosition object or None if no roads found
        """
        results = self.find_roads_near_position(x, y, z=z, max_distance=float('inf'), sample_step=sample_step)
        
        return results[0] if results else None
    
    def is_position_on_road(self, x: float, y: float, z: float = None,
                            max_lateral_distance: float = 10.0) -> bool:
        """
        Check if a position is on any road.
        
        Args:
            x, y: World coordinates (horizontal)
            z: World coordinate (height). If provided, 3D distance is used.
            max_lateral_distance: Maximum lateral distance from road centerline
            
        Returns:
            True if position is on a road
        """
        road_pos = self.find_closest_road(x, y, z=z)
        
        if road_pos is None:
            return False
        
        return road_pos.distance_to_road <= max_lateral_distance
    
    def get_frenet_coordinates(self, road_id: str, x: float, y: float) -> Optional[Tuple[float, float]]:
        """
        Get Frenet coordinates (s, t) for a position on a specific road.
        
        Args:
            road_id: Road ID
            x, y: World coordinates
            
        Returns:
            Tuple of (s, t) or None if road not found
        """
        road = self.get_road_by_id(road_id)
        if road is None:
            return None
        
        s, _ = self._find_closest_s_on_road(road, x, y)
        t = self._get_t_coordinate(road, s, x, y)
        
        return s, t
    
    def world_to_road(self, x: float, y: float, z: float = None,
                      max_distance: float = 10.0) -> Optional[RoadPosition]:
        """
        Convert world coordinates to road coordinates.
        
        This is an alias for find_closest_road with a distance limit.
        
        Args:
            x, y: World coordinates (horizontal)
            z: World coordinate (height). If provided, 3D distance is used.
            max_distance: Maximum distance to consider (meters)
            
        Returns:
            RoadPosition or None if no road within max_distance
        """
        road_pos = self.find_closest_road(x, y, z=z)
        
        if road_pos is None or road_pos.distance_to_road > max_distance:
            return None
        
        return road_pos
    
    def road_to_world(self, road_id: str, s: float, t: float = 0.0, h: float = 0.0) -> Optional[Tuple[float, float, float]]:
        """
        Convert road coordinates to world coordinates.
        
        Args:
            road_id: Road ID
            s: Longitudinal coordinate (meters)
            t: Lateral offset from centerline (meters)
            h: Height above road (meters)
            
        Returns:
            Tuple of (x, y, z) world coordinates or None if road not found
        """
        road = self.get_road_by_id(road_id)
        if road is None:
            return None
        
        try:
            pos = road.get_xyz(s, t, h)
            return pos.array[0], pos.array[1], pos.array[2]
        except Exception as e:
            logger.warning(f"Error converting road to world coordinates: {e}")
            return None


    def find_connected_roads_in_range(self, x: float, y: float, z: float = None,
                                       max_distance: float = 300.0,
                                       ego_road_threshold: float = 20.0,
                                       max_height_diff: float = 3.0) -> List[RoadPosition]:
        """
        Find all roads connected to ego's road(s) within the specified range.
        
        This method ensures only roads that are:
        1. Connected to the ego's current road via the road network
        2. Within the specified distance range
        3. Within the specified height difference (if z is provided)
        
        This prevents "dangling" road segments that are within range but not
        connected to the ego's driving path, and distinguishes between
        elevated roads and ground-level roads.
        
        Args:
            x, y: Ego world coordinates (horizontal)
            z: Ego world coordinate (height). If provided, height filtering is enabled.
            max_distance: Maximum horizontal distance from ego (meters)
            ego_road_threshold: Distance threshold to consider ego "on" a road
            max_height_diff: Maximum height difference from ego (meters).
                           Roads with height difference > this value are filtered out.
                           Default is 3.0m. Set to None to disable height filtering.
            
        Returns:
            List of RoadPosition objects for connected roads within range
        """
        from collections import deque
        
        # Step 1: Find all roads the ego is near (could be multiple at junctions)
        ego_roads = self.find_roads_near_position(x, y, z=z, max_distance=ego_road_threshold)
        
        if not ego_roads:
            logger.warning(f"No roads found near ego position ({x:.2f}, {y:.2f})")
            return []
        
        # Step 1.5: Filter ego roads - only keep roads where ego is actually within lane boundaries
        # This removes roads where ego is nearby but not actually on the road
        valid_ego_roads = []
        for rp in ego_roads:
            road = self.get_road_by_id(rp.road_id)
            if road is None:
                continue
            
            # Check if ego's t-coordinate is within the road's lane boundaries
            # Get left and right road widths at the ego's s position
            left_width, right_width = self._get_road_width_at_s(road, rp.s)
            
            # t > 0 means ego is on the left side (negative lane IDs)
            # t < 0 means ego is on the right side (positive lane IDs)
            # Allow some tolerance for GPS/positioning error (e.g., 2m)
            tolerance = 2.0
            if rp.t >= 0:
                # Ego on left side, check against left_width
                in_bounds = rp.t <= left_width + tolerance
            else:
                # Ego on right side, check against right_width (use absolute value of t)
                in_bounds = abs(rp.t) <= right_width + tolerance
            
            if in_bounds:
                valid_ego_roads.append(rp)
                logger.debug(f"Ego road {rp.road_id}: t={rp.t:.2f}m, left_width={left_width:.2f}m, right_width={right_width:.2f}m -> VALID")
            else:
                logger.info(f"Ego road {rp.road_id}: t={rp.t:.2f}m, left_width={left_width:.2f}m, right_width={right_width:.2f}m -> OUT OF BOUNDS, filtered out")
        
        if not valid_ego_roads:
            logger.warning(f"No valid ego roads found after lane boundary check")
            # Fall back to original behavior if all roads are filtered out
            valid_ego_roads = ego_roads
        
        ego_road_ids = [rp.road_id for rp in valid_ego_roads]
        logger.info(f"Ego is on {len(ego_road_ids)} road(s): {ego_road_ids}")
        
        # Step 2: Build road connectivity graph
        road_graph = self._build_road_graph()
        
        # Step 3: BFS to find all connected roads within range
        connected_roads = set()
        visited = set()
        queue = deque(ego_road_ids)
        visited.update(ego_road_ids)
        
        while queue:
            current_road_id = queue.popleft()
            
            # Check if this road is within range
            road = self.get_road_by_id(current_road_id)
            if road is None:
                continue
            
            # Sample points to check if in range
            in_range = False
            in_height_range = True  # Default to True if no height filtering
            road_length = road.length
            sample_step = min(50.0, road_length / 5)
            
            s = 0.0
            min_height_diff = float('inf')
            while s <= road_length:
                try:
                    pos = road.get_xyz(s, 0.0, 0.0)
                    dx = pos.array[0] - x
                    dy = pos.array[1] - y
                    
                    # Check horizontal distance (2D)
                    horiz_dist = (dx * dx + dy * dy) ** 0.5
                    
                    # Check height difference if z is provided
                    if z is not None and max_height_diff is not None:
                        dz = abs(pos.array[2] - z)
                        min_height_diff = min(min_height_diff, dz)
                        if dz <= max_height_diff and horiz_dist <= max_distance:
                            in_range = True
                            in_height_range = True
                            break
                        elif horiz_dist <= max_distance:
                            # Within horizontal range but outside height range
                            in_range = True
                            in_height_range = False
                    else:
                        # No height filtering, just check horizontal distance
                        if horiz_dist <= max_distance:
                            in_range = True
                            break
                except Exception:
                    pass
                s += sample_step
            
            # Only add road and explore neighbors if within range AND within height tolerance
            if in_range and in_height_range:
                connected_roads.add(current_road_id)
                
                # Explore neighbors - only if this road is in range
                # This optimization prevents searching roads that are connected to out-of-range roads
                if current_road_id in road_graph:
                    for neighbor_id in road_graph[current_road_id]:
                        if neighbor_id not in visited:
                            visited.add(neighbor_id)
                            queue.append(neighbor_id)
            elif in_range and not in_height_range:
                # Road is within horizontal range but outside height range
                # Log this for debugging but don't add it or explore its neighbors
                logger.debug(f"Road {current_road_id} filtered out: height_diff={min_height_diff:.2f}m > max_height_diff={max_height_diff:.2f}m")
        
        logger.info(f"Found {len(connected_roads)} connected roads within {max_distance}m")
        
        # Step 4: Build RoadPosition results for connected roads
        results = []
        for road_id in connected_roads:
            road = self.get_road_by_id(road_id)
            if road is None:
                continue
            
            s, distance = self._find_closest_s_on_road(road, x, y)
            t = self._get_t_coordinate(road, s, x, y)
            lane_id = self._find_lane_at_position(road, s, t)
            
            # Find lane section s0
            lane_section_s0 = None
            for lanesection in road.get_lanesections():
                s0 = lanesection.s0 if hasattr(lanesection, 's0') else 0.0
                s_end = road.get_lanesection_end(lanesection)
                if s0 <= s <= s_end:
                    lane_section_s0 = s0
                    break
            
            results.append(RoadPosition(
                road_id=road_id,
                s=s,
                t=t,
                h=0.0,
                lane_id=lane_id,
                lane_section_s0=lane_section_s0,
                distance_to_road=distance
            ))
        
        # Sort by distance
        results.sort(key=lambda rp: rp.distance_to_road)
        
        return results
    
    def _build_road_graph(self) -> Dict[str, set]:
        """
        Build road network connectivity graph.
        
        Returns:
            Dict mapping road_id -> set of connected road_ids
        """
        road_graph = {}
        
        # Build junction lookup
        junctions_by_id = {}
        if hasattr(self.odr_map, 'get_junctions'):
            for junction in self.odr_map.get_junctions():
                jct_id = junction.id
                if isinstance(jct_id, bytes):
                    jct_id = jct_id.decode()
                junctions_by_id[str(jct_id)] = junction
        
        for road in self.roads:
            road_id = road.id.decode() if isinstance(road.id, bytes) else str(road.id)
            
            if road_id not in road_graph:
                road_graph[road_id] = set()
            
            # Add predecessor connection
            if hasattr(road, 'predecessor') and road.predecessor:
                pred = road.predecessor
                pred_type = pred.element_type if hasattr(pred, 'element_type') else None
                pred_id = pred.id if hasattr(pred, 'id') else None
                if isinstance(pred_id, bytes):
                    pred_id = pred_id.decode()
                pred_id = str(pred_id) if pred_id is not None else None
                
                # Handle case where element_type is None (some maps don't set this)
                if pred_type is None and pred_id is not None:
                    # Try to determine type by checking if ID is a road or junction
                    if pred_id in self._road_by_id:
                        pred_type = 1  # Type_Road
                    elif pred_id in junctions_by_id:
                        pred_type = 2  # Type_Junction
                
                if pred_type is not None and pred_id is not None:
                    if pred_type == 1:  # Type_Road
                        road_graph[road_id].add(pred_id)
                        if pred_id not in road_graph:
                            road_graph[pred_id] = set()
                        road_graph[pred_id].add(road_id)
                    elif pred_type == 2:  # Type_Junction
                        if pred_id in junctions_by_id:
                            jct = junctions_by_id[pred_id]
                            if hasattr(jct, 'id_to_connection'):
                                for conn in jct.id_to_connection.values():
                                    conn_road_id = conn.connecting_road
                                    if isinstance(conn_road_id, bytes):
                                        conn_road_id = conn_road_id.decode()
                                    conn_road_id = str(conn_road_id)
                                    road_graph[road_id].add(conn_road_id)
                                    if conn_road_id not in road_graph:
                                        road_graph[conn_road_id] = set()
                                    road_graph[conn_road_id].add(road_id)
            
            # Add successor connection
            if hasattr(road, 'successor') and road.successor:
                succ = road.successor
                succ_type = succ.element_type if hasattr(succ, 'element_type') else None
                succ_id = succ.id if hasattr(succ, 'id') else None
                if isinstance(succ_id, bytes):
                    succ_id = succ_id.decode()
                succ_id = str(succ_id) if succ_id is not None else None
                
                # Handle case where element_type is None (some maps don't set this)
                if succ_type is None and succ_id is not None:
                    # Try to determine type by checking if ID is a road or junction
                    if succ_id in self._road_by_id:
                        succ_type = 1  # Type_Road
                    elif succ_id in junctions_by_id:
                        succ_type = 2  # Type_Junction
                
                if succ_type is not None and succ_id is not None:
                    if succ_type == 1:  # Type_Road
                        road_graph[road_id].add(succ_id)
                        if succ_id not in road_graph:
                            road_graph[succ_id] = set()
                        road_graph[succ_id].add(road_id)
                    elif succ_type == 2:  # Type_Junction
                        if succ_id in junctions_by_id:
                            jct = junctions_by_id[succ_id]
                            if hasattr(jct, 'id_to_connection'):
                                for conn in jct.id_to_connection.values():
                                    conn_road_id = conn.connecting_road
                                    if isinstance(conn_road_id, bytes):
                                        conn_road_id = conn_road_id.decode()
                                    conn_road_id = str(conn_road_id)
                                    road_graph[road_id].add(conn_road_id)
                                    if conn_road_id not in road_graph:
                                        road_graph[conn_road_id] = set()
                                    road_graph[conn_road_id].add(road_id)
        
        # Connect junction incoming roads to connecting roads
        for jct_id, jct in junctions_by_id.items():
            if hasattr(jct, 'id_to_connection'):
                incoming_roads = set()
                connecting_roads = set()
                for conn in jct.id_to_connection.values():
                    inc_road = conn.incoming_road
                    if isinstance(inc_road, bytes):
                        inc_road = inc_road.decode()
                    incoming_roads.add(str(inc_road))
                    
                    conn_road = conn.connecting_road
                    if isinstance(conn_road, bytes):
                        conn_road = conn_road.decode()
                    connecting_roads.add(str(conn_road))
                
                for inc_road in incoming_roads:
                    for conn_road in connecting_roads:
                        if inc_road not in road_graph:
                            road_graph[inc_road] = set()
                        road_graph[inc_road].add(conn_road)
                        if conn_road not in road_graph:
                            road_graph[conn_road] = set()
                        road_graph[conn_road].add(inc_road)
        
        return road_graph


# Convenience function for quick usage
def find_current_roads(odr_map, x: float, y: float, max_distance: float = 10.0) -> List[str]:
    """
    Quick function to find road IDs near a position.
    
    Args:
        odr_map: pyOpenDRIVE map object
        x, y: World coordinates
        max_distance: Maximum distance from road centerline (meters)
        
    Returns:
        List of road IDs sorted by distance
    """
    finder = XODRRoadFinder(odr_map)
    positions = finder.find_roads_near_position(x, y, max_distance)
    return [rp.road_id for rp in positions]


def get_current_road_id(odr_map, x: float, y: float) -> Optional[str]:
    """
    Quick function to get the closest road ID.
    
    Args:
        odr_map: pyOpenDRIVE map object
        x, y: World coordinates
        
    Returns:
        Road ID or None
    """
    finder = XODRRoadFinder(odr_map)
    pos = finder.find_closest_road(x, y)
    return pos.road_id if pos else None


def find_connected_roads_in_range(odr_map, x: float, y: float,
                                   max_distance: float = 300.0,
                                   ego_road_threshold: float = 20.0) -> List[str]:
    """
    Quick function to find all connected road IDs within range.
    
    This ensures only roads connected to ego's road are returned,
    preventing "dangling" road segments.
    
    Args:
        odr_map: pyOpenDRIVE map object
        x, y: Ego world coordinates
        max_distance: Maximum distance from ego (meters)
        ego_road_threshold: Distance threshold to consider ego "on" a road
        
    Returns:
        List of connected road IDs within range
    """
    finder = XODRRoadFinder(odr_map)
    positions = finder.find_connected_roads_in_range(x, y, max_distance, ego_road_threshold)
    return [rp.road_id for rp in positions]
