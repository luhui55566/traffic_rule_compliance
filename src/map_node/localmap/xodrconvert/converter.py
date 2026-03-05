"""
Map converter for XODR to LocalMap conversion.

This module handles conversion of XODR data structures (from pyOpenDRIVE)
to LocalMap data structures.
"""

import logging
import math
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from common.local_map.local_map_data import (
    Point3D, Lane, LaneType, LaneDirection,
    LaneBoundarySegment, BoundaryType, BoundaryLineShape, BoundaryColor,
    SpeedLimitSegment, SpeedLimitType,
    TrafficSign, TrafficSignType,
    TrafficLight, TrafficLightColor, TrafficLightShape, TrafficLightStatus, TrafficLightType,
    RoadMarking, RoadMarkingType, RoadMarkingColor,
    Crosswalk,
    StopLine, StopLineType,
    Road, Junction
)
from .transformer import XODRCoordinateTransformer
from .config_types import ConversionResult, ConversionConfig

logger = logging.getLogger(__name__)


class XODRMapConverter:
    """
    Converter for XODR map data to LocalMap format.
    
    This class handles the conversion of XODR elements (roads, lanes, junctions,
    signals, objects) to LocalMap data structures.
    """
    
    def __init__(self, transformer: XODRCoordinateTransformer, config: ConversionConfig = None):
        """
        Initialize XODR map converter.
        
        Args:
            transformer: Coordinate transformer for coordinate conversions
            config: Conversion configuration
        """
        self.transformer = transformer
        self.config = config or ConversionConfig()
        
        # Cache for boundary segment sharing
        self._boundary_cache: Dict[str, int] = {}
        self._boundary_segments: List[LaneBoundarySegment] = []
        self._next_boundary_id = 0  # 边界段ID计数器
        
        # Cache for lane ID generation
        self._lane_id_cache: Dict[str, int] = {}
        self._next_lane_id = 1
        
        # Cache for road and junction objects
        self._roads: Dict[int, Road] = {}
        self._junctions: Dict[int, Junction] = {}
    
    def generate_lane_id(self, road_id: int, lanesection_s0: float, lane_id: int) -> int:
        """
        Generate globally unique lane ID.
        
        Args:
            road_id: Road ID
            lanesection_s0: Lane section start s coordinate
            lane_id: Lane ID (positive for right, negative for left)
            
        Returns:
            Globally unique lane ID
        """
        key = f"{road_id}_{lanesection_s0}_{lane_id}"
        if key not in self._lane_id_cache:
            self._lane_id_cache[key] = self._next_lane_id
            self._next_lane_id += 1
        return self._lane_id_cache[key]
    
    def generate_boundary_id(self, road_id: int, lanesection_s0: float, lane_id: int, s_start: float, boundary_suffix: str = '') -> int:
        """
        Generate globally unique boundary segment ID.
        
        Args:
            road_id: Road ID
            lanesection_s0: Lane section start s coordinate
            lane_id: Lane ID
            s_start: Start s coordinate for this segment
            boundary_suffix: Suffix to distinguish inner/outer boundaries (optional)
            
        Returns:
            Globally unique boundary segment ID
        """
        key = f"{road_id}_{lanesection_s0}_{lane_id}_{s_start}_{boundary_suffix}"
        if key not in self._boundary_cache:
            self._boundary_cache[key] = self._next_boundary_id
            self._next_boundary_id += 1
        return self._boundary_cache[key]
    
    def _clip_centerline_at_range(
        self,
        centerline_points: List[Point3D],
        s_values: List[float],
        map_range: float
    ) -> Tuple[List[Point3D], List[float]]:
        """
        Clip centerline points at the map_range boundary using rectangular bounds.
        
        This method ensures that centerlines extending beyond the map range
        are properly clipped at the boundary, with interpolated points added
        where the centerline crosses the range limit.
        
        Uses rectangular bounds (|x| <= range and |y| <= range) to match
        the visualization's axis limits.
        
        Args:
            centerline_points: List of centerline points in local coordinates
            s_values: List of s values corresponding to each point
            map_range: Maximum range from ego (origin in local coords)
            
        Returns:
            Tuple of (clipped_points, clipped_s_values)
        """
        if not centerline_points or len(centerline_points) < 2:
            return centerline_points, s_values
        
        clipped_points = []
        clipped_s_values = []
        
        # Helper function to check if point is in rectangular range
        def is_in_range(pt: Point3D) -> bool:
            return abs(pt.x) <= map_range and abs(pt.y) <= map_range
        
        # Helper function to find intersection with boundary edge
        def interpolate_at_boundary(p1: Point3D, p2: Point3D, s1: float, s2: float,
                                    boundary: str) -> Tuple[Point3D, float]:
            """
            Interpolate to find the point where line crosses a boundary edge.
            
            Args:
                p1, p2: Endpoints of the line segment
                s1, s2: S values at endpoints
                boundary: One of 'x+', 'x-', 'y+', 'y-' indicating which boundary
            """
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            
            if boundary == 'x+':
                # Crossing x = +map_range
                if abs(dx) < 1e-9:
                    t = 0.5
                else:
                    t = (map_range - p1.x) / dx
            elif boundary == 'x-':
                # Crossing x = -map_range
                if abs(dx) < 1e-9:
                    t = 0.5
                else:
                    t = (-map_range - p1.x) / dx
            elif boundary == 'y+':
                # Crossing y = +map_range
                if abs(dy) < 1e-9:
                    t = 0.5
                else:
                    t = (map_range - p1.y) / dy
            else:  # y-
                # Crossing y = -map_range
                if abs(dy) < 1e-9:
                    t = 0.5
                else:
                    t = (-map_range - p1.y) / dy
            
            t = max(0.0, min(1.0, t))  # Clamp to [0, 1]
            
            interp_x = p1.x + t * dx
            interp_y = p1.y + t * dy
            interp_z = p1.z + t * (p2.z - p1.z)
            interp_s = s1 + t * (s2 - s1)
            
            return Point3D(x=interp_x, y=interp_y, z=interp_z), interp_s
        
        # Helper function to find all boundary crossings for a segment
        def find_boundary_crossings(p1: Point3D, p2: Point3D, s1: float, s2: float):
            """Find all points where segment crosses rectangular boundary."""
            crossings = []
            
            # Check each boundary edge
            boundaries = []
            if (p1.x > map_range) != (p2.x > map_range):
                boundaries.append('x+')
            if (p1.x < -map_range) != (p2.x < -map_range):
                boundaries.append('x-')
            if (p1.y > map_range) != (p2.y > map_range):
                boundaries.append('y+')
            if (p1.y < -map_range) != (p2.y < -map_range):
                boundaries.append('y-')
            
            for boundary in boundaries:
                pt, s_val = interpolate_at_boundary(p1, p2, s1, s2, boundary)
                # Verify the interpolated point is actually on the boundary
                if abs(pt.x) <= map_range + 0.01 and abs(pt.y) <= map_range + 0.01:
                    crossings.append((pt, s_val, t_for_boundary(p1, p2, boundary)))
            
            # Sort by parameter t to maintain order along segment
            crossings.sort(key=lambda x: x[2])
            return [(pt, s) for pt, s, _ in crossings]
        
        def t_for_boundary(p1: Point3D, p2: Point3D, boundary: str) -> float:
            """Calculate t parameter for boundary crossing."""
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            
            if boundary in ('x+', 'x-'):
                if abs(dx) < 1e-9:
                    return 0.5
                target = map_range if boundary == 'x+' else -map_range
                return (target - p1.x) / dx
            else:
                if abs(dy) < 1e-9:
                    return 0.5
                target = map_range if boundary == 'y+' else -map_range
                return (target - p1.y) / dy
        
        # Process each segment
        prev_point = centerline_points[0]
        prev_s = s_values[0]
        prev_in_range = is_in_range(prev_point)
        
        # Start with first point if in range
        if prev_in_range:
            clipped_points.append(prev_point)
            clipped_s_values.append(prev_s)
        
        for i in range(1, len(centerline_points)):
            curr_point = centerline_points[i]
            curr_s = s_values[i]
            curr_in_range = is_in_range(curr_point)
            
            if prev_in_range and curr_in_range:
                # Both in range - add current point
                clipped_points.append(curr_point)
                clipped_s_values.append(curr_s)
            elif prev_in_range and not curr_in_range:
                # Exiting range - add boundary crossing point(s)
                crossings = find_boundary_crossings(prev_point, curr_point, prev_s, curr_s)
                for pt, s_val in crossings:
                    clipped_points.append(pt)
                    clipped_s_values.append(s_val)
            elif not prev_in_range and curr_in_range:
                # Entering range - add boundary crossing point(s) then current point
                crossings = find_boundary_crossings(prev_point, curr_point, prev_s, curr_s)
                for pt, s_val in crossings:
                    clipped_points.append(pt)
                    clipped_s_values.append(s_val)
                clipped_points.append(curr_point)
                clipped_s_values.append(curr_s)
            # else: both out of range - check if segment passes through range
            elif not prev_in_range and not curr_in_range:
                # Check if segment crosses through the rectangular region
                crossings = find_boundary_crossings(prev_point, curr_point, prev_s, curr_s)
                if len(crossings) >= 2:
                    # Segment passes through - add entry and exit points
                    for pt, s_val in crossings[:2]:  # Take first two (entry and exit)
                        clipped_points.append(pt)
                        clipped_s_values.append(s_val)
            
            prev_point = curr_point
            prev_s = curr_s
            prev_in_range = curr_in_range
        
        # If we only have 0 or 1 points after clipping, return empty to avoid drawing issues
        if len(clipped_points) < 2:
            logger.debug(f"Centerline clipped to {len(clipped_points)} points (insufficient for drawing)")
            return [], []
        
        return clipped_points, clipped_s_values
    
    def _resample_centerline_uniform(
        self,
        centerline_points: List[Point3D],
        s_values: List[float],
        target_spacing: float
    ) -> Tuple[List[Point3D], List[float]]:
        """
        Resample centerline points to ensure uniform spacing.
        
        This fixes the issue where pyOpenDRIVE's sampling produces uneven gaps
        on curved roads by interpolating points at regular intervals.
        
        Args:
            centerline_points: List of centerline points
            s_values: List of s values corresponding to each point
            target_spacing: Target distance between consecutive points (meters)
            
        Returns:
            Tuple of (resampled_points, resampled_s_values)
        """
        if len(centerline_points) < 2:
            return centerline_points, s_values
        
        # Calculate total path length
        total_length = 0.0
        segment_lengths = []
        for i in range(len(centerline_points) - 1):
            p1 = centerline_points[i]
            p2 = centerline_points[i + 1]
            length = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2 + (p2.z - p1.z)**2)
            segment_lengths.append(length)
            total_length += length
        
        if total_length < 0.01:  # Nearly zero length
            return centerline_points, s_values
        
        # Calculate number of segments needed
        num_segments = max(2, int(math.ceil(total_length / target_spacing)))
        
        # Generate uniformly spaced points
        resampled_points = []
        resampled_s_values = []
        
        # Always include first point
        resampled_points.append(centerline_points[0])
        resampled_s_values.append(s_values[0])
        
        # Interpolate points at uniform intervals
        target_dist = total_length / num_segments
        current_target = target_dist
        
        accumulated_dist = 0.0
        for i in range(len(segment_lengths)):
            seg_length = segment_lengths[i]
            p1 = centerline_points[i]
            p2 = centerline_points[i + 1]
            s1 = s_values[i]
            s2 = s_values[i + 1]
            
            # Process this segment
            seg_start_dist = accumulated_dist
            seg_end_dist = accumulated_dist + seg_length
            
            # Add interpolated points within this segment
            while current_target < seg_end_dist - 0.001:  # Small tolerance to avoid duplicates
                # Calculate interpolation parameter
                if seg_length < 0.001:
                    t = 0.0
                else:
                    t = (current_target - seg_start_dist) / seg_length
                t = max(0.0, min(1.0, t))
                
                # Interpolate point
                interp_x = p1.x + t * (p2.x - p1.x)
                interp_y = p1.y + t * (p2.y - p1.y)
                interp_z = p1.z + t * (p2.z - p1.z)
                interp_s = s1 + t * (s2 - s1)
                
                resampled_points.append(Point3D(x=interp_x, y=interp_y, z=interp_z))
                resampled_s_values.append(interp_s)
                
                current_target += target_dist
            
            accumulated_dist = seg_end_dist
        
        # Always include last point if not already included
        if len(resampled_points) > 0:
            last_point = resampled_points[-1]
            end_point = centerline_points[-1]
            dist_to_end = math.sqrt(
                (end_point.x - last_point.x)**2 +
                (end_point.y - last_point.y)**2 +
                (end_point.z - last_point.z)**2
            )
            if dist_to_end > 0.001:  # Only add if not essentially the same point
                resampled_points.append(centerline_points[-1])
                resampled_s_values.append(s_values[-1])
        
        return resampled_points, resampled_s_values
    
    def _clip_boundary_at_range(
        self,
        boundary_points: List[Point3D],
        map_range: float
    ) -> List[Point3D]:
        """
        Clip boundary points at the map_range boundary using rectangular bounds.
        
        This is similar to _clip_centerline_at_range but for boundary segments
        that don't have s values.
        
        Args:
            boundary_points: List of boundary points in local coordinates
            map_range: Maximum range from ego (origin in local coords)
            
        Returns:
            List of clipped boundary points
        """
        if not boundary_points or len(boundary_points) < 2:
            return boundary_points
        
        clipped_points = []
        
        # Helper function to check if point is in rectangular range
        def is_in_range(pt: Point3D) -> bool:
            return abs(pt.x) <= map_range and abs(pt.y) <= map_range
        
        # Helper function to find intersection with boundary edge
        def interpolate_at_boundary(p1: Point3D, p2: Point3D, boundary: str) -> Point3D:
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            
            if boundary == 'x+':
                t = (map_range - p1.x) / dx if abs(dx) > 1e-9 else 0.5
            elif boundary == 'x-':
                t = (-map_range - p1.x) / dx if abs(dx) > 1e-9 else 0.5
            elif boundary == 'y+':
                t = (map_range - p1.y) / dy if abs(dy) > 1e-9 else 0.5
            else:  # y-
                t = (-map_range - p1.y) / dy if abs(dy) > 1e-9 else 0.5
            
            t = max(0.0, min(1.0, t))
            
            return Point3D(
                x=p1.x + t * dx,
                y=p1.y + t * dy,
                z=p1.z + t * (p2.z - p1.z)
            )
        
        # Helper function to find all boundary crossings for a segment
        def find_boundary_crossings(p1: Point3D, p2: Point3D):
            crossings = []
            
            # Check each boundary edge
            boundaries = []
            if (p1.x > map_range) != (p2.x > map_range):
                boundaries.append('x+')
            if (p1.x < -map_range) != (p2.x < -map_range):
                boundaries.append('x-')
            if (p1.y > map_range) != (p2.y > map_range):
                boundaries.append('y+')
            if (p1.y < -map_range) != (p2.y < -map_range):
                boundaries.append('y-')
            
            for boundary in boundaries:
                pt = interpolate_at_boundary(p1, p2, boundary)
                # Verify the interpolated point is actually on the boundary
                if abs(pt.x) <= map_range + 0.01 and abs(pt.y) <= map_range + 0.01:
                    crossings.append((pt, t_for_boundary(p1, p2, boundary)))
            
            # Sort by parameter t to maintain order along segment
            crossings.sort(key=lambda x: x[1])
            return [pt for pt, _ in crossings]
        
        def t_for_boundary(p1: Point3D, p2: Point3D, boundary: str) -> float:
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            
            if boundary in ('x+', 'x-'):
                if abs(dx) < 1e-9:
                    return 0.5
                target = map_range if boundary == 'x+' else -map_range
                return (target - p1.x) / dx
            else:
                if abs(dy) < 1e-9:
                    return 0.5
                target = map_range if boundary == 'y+' else -map_range
                return (target - p1.y) / dy
        
        # Process each segment
        prev_point = boundary_points[0]
        prev_in_range = is_in_range(prev_point)
        
        # Start with first point if in range
        if prev_in_range:
            clipped_points.append(prev_point)
        
        for i in range(1, len(boundary_points)):
            curr_point = boundary_points[i]
            curr_in_range = is_in_range(curr_point)
            
            if prev_in_range and curr_in_range:
                # Both in range - add current point
                clipped_points.append(curr_point)
            elif prev_in_range and not curr_in_range:
                # Exiting range - add boundary crossing point(s)
                crossings = find_boundary_crossings(prev_point, curr_point)
                clipped_points.extend(crossings)
            elif not prev_in_range and curr_in_range:
                # Entering range - add boundary crossing point(s) then current point
                crossings = find_boundary_crossings(prev_point, curr_point)
                clipped_points.extend(crossings)
                clipped_points.append(curr_point)
            # else: both out of range - check if segment passes through range
            elif not prev_in_range and not curr_in_range:
                # Check if segment crosses through the rectangular region
                crossings = find_boundary_crossings(prev_point, curr_point)
                if len(crossings) >= 2:
                    # Segment passes through - add entry and exit points
                    clipped_points.extend(crossings[:2])
            
            prev_point = curr_point
            prev_in_range = curr_in_range
        
        # If we only have 0 or 1 points after clipping, return empty
        if len(clipped_points) < 2:
            return []
        
        return clipped_points
    
    def convert_lane_type(self, xodr_lane_type: str) -> LaneType:
        """
        Convert XODR lane type to LocalMap LaneType.
        
        Args:
            xodr_lane_type: XODR lane type string
            
        Returns:
            LocalMap LaneType enum
        """
        # Use different variable name to avoid conflict with local variable
        xodr_lane_type_lower = xodr_lane_type.lower()
        type_mapping = {
            'driving': LaneType.DRIVING,
            'shoulder': LaneType.SHOULDER,
            'sidewalk': LaneType.SIDEWALK,
            'parking': LaneType.PARKING,
            'biking': LaneType.BIKING,
            'border': LaneType.UNKNOWN,
            'restricted': LaneType.UNKNOWN,
            'none': LaneType.UNKNOWN,
            'median': LaneType.UNKNOWN,
        }
        return type_mapping.get(xodr_lane_type_lower, LaneType.UNKNOWN)
    
    def convert_lane_direction(self, xodr_lane_id: int) -> LaneDirection:
        """
        Convert XODR lane ID to LocalMap LaneDirection.
        
        Args:
            xodr_lane_id: XODR lane ID (positive for right, negative for left)
            
        Returns:
            LocalMap LaneDirection enum
        """
        if xodr_lane_id < 0:
            return LaneDirection.FORWARD  # Left lanes (negative ID)
        elif xodr_lane_id > 0:
            return LaneDirection.BACKWARD  # Right lanes (positive ID)
        else:
            return LaneDirection.UNKNOWN  # Center reference line
    
    def convert_boundary_type(self, xodr_roadmark_type: str) -> BoundaryType:
        """
        Convert XODR roadmark type to LocalMap BoundaryType.
        
        Args:
            xodr_roadmark_type: XODR roadmark type string
            
        Returns:
            LocalMap BoundaryType enum
        """
        type_mapping = {
            'curb': BoundaryType.CURB,
            'solid': BoundaryType.LINE,
            'broken': BoundaryType.LINE,
            'none': BoundaryType.VIRTUAL,
            'botts_dots': BoundaryType.LINE,
        }
        if isinstance(xodr_roadmark_type, bytes):
            xodr_roadmark_type = xodr_roadmark_type.decode('utf-8')
        elif not isinstance(xodr_roadmark_type, str):
            # 防御性编程：转成字符串
            xodr_roadmark_type = str(xodr_roadmark_type)
        return type_mapping.get(xodr_roadmark_type.lower(), BoundaryType.UNKNOWN)
    
    def convert_boundary_line_shape(self, xodr_roadmark_type: str) -> BoundaryLineShape:
        """
        Convert XODR roadmark type to LocalMap BoundaryLineShape.
        
        XODR RoadMark Type 定义:
        - solid: 单实线
        - broken: 单虚线
        - solid solid: 双实线
        - solid broken: 左实右虚 (从道路中心向外看)
        - broken solid: 左虚右实
        - broken broken: 双虚线
        - botts_dots: 圆点标线
        
        Args:
            xodr_roadmark_type: XODR roadmark type string
            
        Returns:
            LocalMap BoundaryLineShape enum
        """
        type_mapping = {
            'solid': BoundaryLineShape.SOLID,
            'broken': BoundaryLineShape.DASHED,
            'solid solid': BoundaryLineShape.DOUBLE_SOLID,
            'solid broken': BoundaryLineShape.LEFT_SOLID_RIGHT_DASHED,  # 左实右虚
            'broken solid': BoundaryLineShape.LEFT_DASHED_RIGHT_SOLID,  # 左虚右实
            'broken broken': BoundaryLineShape.DOUBLE_DASHED,           # 双虚线
            'botts_dots': BoundaryLineShape.DOTTED,                     # 圆点标线
        }
        if isinstance(xodr_roadmark_type, bytes):
            xodr_roadmark_type = xodr_roadmark_type.decode('utf-8')
        elif not isinstance(xodr_roadmark_type, str):
            # 防御性编程：转成字符串
            xodr_roadmark_type = str(xodr_roadmark_type)
        return type_mapping.get(xodr_roadmark_type.lower(), BoundaryLineShape.UNKNOWN)
    
    def convert_boundary_color(self, xodr_color: str) -> BoundaryColor:
        """
        Convert XODR roadmark color to LocalMap BoundaryColor.
        
        OpenDRIVE 标准颜色定义:
        - standard: 标准颜色（通常为白色，是最常用的默认颜色）
        - white: 白色
        - yellow: 黄色（通常用于分隔对向交通）
        - blue: 蓝色（特殊用途）
        - red: 红色（特殊用途）
        
        Args:
            xodr_color: XODR roadmark color string (may be bytes)
            
        Returns:
            LocalMap BoundaryColor enum
        """
        color_mapping = {
            'standard': BoundaryColor.WHITE,  # standard = 白色（OpenDRIVE默认）
            'white': BoundaryColor.WHITE,
            'yellow': BoundaryColor.YELLOW,
            'blue': BoundaryColor.BLUE,
            'red': BoundaryColor.RED,
        }
        if isinstance(xodr_color, bytes):
            xodr_color = xodr_color.decode('utf-8')
        elif not isinstance(xodr_color, str):
            # 防御性编程：转成字符串
            xodr_color = str(xodr_color)
        return color_mapping.get(xodr_color.lower(), BoundaryColor.UNKNOWN)
    
    def convert_speed_limit(self, speed_value: float, speed_unit: str) -> float:
        """
        Convert XODR speed limit to m/s.
        
        Args:
            speed_value: Speed limit value
            speed_unit: Speed unit (mph, km/h, m/s)
            
        Returns:
            Speed limit in m/s
        """
        if speed_unit.lower() == 'mph':
            return speed_value * 0.44704  # mph to m/s
        elif speed_unit.lower() == 'km/h':
            return speed_value / 3.6  # km/h to m/s
        else:  # m/s
            return speed_value
    
    def convert_traffic_sign_type(self, xodr_signal_type: int) -> TrafficSignType:
        """
        Convert XODR signal type to LocalMap TrafficSignType.
        
        Args:
            xodr_signal_type: XODR signal type code
            
        Returns:
            LocalMap TrafficSignType enum
        """
        type_mapping = {
            274: TrafficSignType.SPEED_LIMIT,
            275: TrafficSignType.SPEED_LIMIT_END,
            205: TrafficSignType.NO_ENTRY,
            206: TrafficSignType.NO_OVERTAKING,
            209: TrafficSignType.NO_LEFT_TURN,
            211: TrafficSignType.NO_RIGHT_TURN,
            222: TrafficSignType.STRAIGHT_ONLY,
            223: TrafficSignType.LEFT_TURN_ONLY,
            224: TrafficSignType.RIGHT_TURN_ONLY,
            235: TrafficSignType.ROUNDABOUT,
        }
        return type_mapping.get(xodr_signal_type, TrafficSignType.UNKNOWN)
    
    def convert_road_to_road_object(
        self,
        odr_road: Any,
        reference_line_points: List[Point3D] = None
    ) -> Road:
        """
        Convert XODR Road to LocalMap Road object.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            reference_line_points: Reference line points (optional)
            
        Returns:
            LocalMap Road object
        """
        road_id = int(odr_road.id.decode() if isinstance(odr_road.id, bytes) else odr_road.id)
        
        # Extract road type from first type element
        road_type = ""
        if hasattr(odr_road, 'get_s_to_type'):
            type_at_0 = odr_road.get_s_to_type(0.0)
            if type_at_0:
                road_type = type_at_0.decode() if isinstance(type_at_0, bytes) else type_at_0
        
        # Extract speed limit
        speed_limit = 0.0
        # pyOpenDRIVE exposes s_to_speed as a property (dict), not a method
        if hasattr(odr_road, 's_to_speed') and odr_road.s_to_speed:
            # Get the first speed record (at s=0 or lowest s value)
            s_to_speed_dict = odr_road.s_to_speed
            if s_to_speed_dict:
                first_s = min(s_to_speed_dict.keys())
                speed_record = s_to_speed_dict[first_s]
                speed_limit = self.convert_speed_limit(speed_record.max, speed_record.unit)
        
        # Extract predecessor/successor information
        predecessor_road_id = None
        successor_road_id = None
        predecessor_junction_id = None
        successor_junction_id = None
        
        if hasattr(odr_road, 'predecessor'):
            pred = odr_road.predecessor
            if pred:
                # pyOpenDRIVE uses 'type' (integer enum) not 'elementType' (string)
                # Type_Road = 1, Type_Junction = 2
                if hasattr(pred, 'type'):
                    elem_type = pred.type
                    if elem_type == 1:  # Type_Road
                        predecessor_road_id = int(pred.id)
                    elif elem_type == 2:  # Type_Junction
                        predecessor_junction_id = int(pred.id)
        
        if hasattr(odr_road, 'successor'):
            succ = odr_road.successor
            if succ:
                # pyOpenDRIVE uses 'type' (integer enum) not 'elementType' (string)
                # Type_Road = 1, Type_Junction = 2
                if hasattr(succ, 'type'):
                    elem_type = succ.type
                    if elem_type == 1:  # Type_Road
                        successor_road_id = int(succ.id)
                    elif elem_type == 2:  # Type_Junction
                        successor_junction_id = int(succ.id)
        
        return Road(
            road_id=road_id,
            road_name=odr_road.name.decode() if isinstance(odr_road.name, bytes) else odr_road.name,
            road_length=odr_road.length,
            road_type=road_type,
            predecessor_road_id=predecessor_road_id,
            successor_road_id=successor_road_id,
            predecessor_junction_id=predecessor_junction_id,
            successor_junction_id=successor_junction_id,
            lane_ids=[],  # Will be populated during lane conversion
            reference_line=reference_line_points or [],
            speed_limit=speed_limit
        )
    
    def convert_junction_to_junction_object(
        self,
        odr_junction: Any,
        connected_road_ids: List[int]
    ) -> Junction:
        """
        Convert XODR Junction to LocalMap Junction object.
        
        Args:
            odr_junction: pyOpenDRIVE Junction object
            connected_road_ids: List of road IDs connected to this junction
            
        Returns:
            LocalMap Junction object
        """
        junction_id = int(odr_junction.id.decode() if isinstance(odr_junction.id, bytes) else odr_junction.id)
        
        # Extract junction type
        junction_type = ""
        if hasattr(odr_junction, 'junctionType'):
            j_type = odr_junction.junctionType
            junction_type = j_type.decode() if isinstance(j_type, bytes) else j_type
        
        # Check for traffic light controllers
        has_traffic_light = False
        controller_ids = []
        if hasattr(odr_junction, 'id_to_controller'):
            controllers = odr_junction.id_to_controller
            if controllers:
                has_traffic_light = True
                controller_ids = list(controllers.keys())
        
        # Calculate connection count
        connection_count = 0
        if hasattr(odr_junction, 'id_to_connection'):
            connection_count = len(odr_junction.id_to_connection)
        
        return Junction(
            junction_id=junction_id,
            junction_name=odr_junction.name.decode() if isinstance(odr_junction.name, bytes) else odr_junction.name,
            junction_type=junction_type,
            road_ids=connected_road_ids,
            connection_count=connection_count,
            has_traffic_light=has_traffic_light,
            controller_ids=controller_ids,
            polygon_points=[],  # Will be calculated later
            center_point=Point3D(x=0.0, y=0.0, z=0.0)  # Will be calculated later
        )
    
    def convert_lane_to_lane(
        self,
        odr_road: Any,
        odr_lane: Any,
        lanesection_s0: float,
        lanesection_send: float,
        lanes: List[Any] = None
    ) -> ConversionResult:
        """
        Convert XODR Lane to LocalMap Lane object.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            odr_lane: pyOpenDRIVE Lane object
            lanesection_s0: Lane section start s coordinate
            lanesection_send: Lane section end s coordinate
            lanes: List of all lanes in this lane section (unused, kept for compatibility)
            
        Returns:
            ConversionResult with converted Lane
        """
        try:
            road_id = int(odr_road.id.decode() if isinstance(odr_road.id, bytes) else odr_road.id)
            lane_id = int(odr_lane.id.decode() if isinstance(odr_lane.id, bytes) else odr_lane.id)
            
            # Skip center lane (lane_id=0) - it represents the boundary between innermost lanes
            # but should not be converted to a Lane object in the final localmap
            if lane_id == 0:
                return ConversionResult(
                    success=True,
                    data=None,
                    warnings=["Center lane (lane_id=0) skipped - boundary lines will be added to boundary pool"],
                    errors=[]
                )
            
            # Generate unique lane ID
            local_lane_id = self.generate_lane_id(road_id, lanesection_s0, lane_id)
            
            # Convert lane type
            lane_type_str = odr_lane.type.decode() if isinstance(odr_lane.type, bytes) else odr_lane.type
            lane_type = self.convert_lane_type(lane_type_str)
            
            # Convert lane direction
            lane_direction = self.convert_lane_direction(lane_id)
            
            # Determine if this is a junction lane
            junction_value = int(odr_road.junction.decode()) if isinstance(odr_road.junction, bytes) else int(odr_road.junction)
            is_junction_lane = (junction_value != -1)
            junction_id = junction_value if is_junction_lane else None
            
            # Extract centerline points by taking midpoints of left and right boundary lines
            centerline_points = []
            centerline_s_values = []  # Track s values for sorting
            
            if hasattr(odr_road, 'get_lane_border_line'):
                try:
                    # Get left boundary (outer for left lanes, inner for right lanes)
                    # For lane_id > 0 (left lanes): left side is further from reference line (outer)
                    # For lane_id < 0 (right lanes): left side is closer to reference line (inner)
                    left_boundary = odr_road.get_lane_border_line(
                        lane=odr_lane,
                        s_start=lanesection_s0,
                        s_end=lanesection_send,
                        eps=self.config.eps,
                        outer=(lane_id > 0)  # Left lanes: left boundary is outer
                    )
                    
                    # Get right boundary (inner for left lanes, outer for right lanes)
                    # For lane_id > 0 (left lanes): right side is closer to reference line (inner)
                    # For lane_id < 0 (right lanes): right side is further from reference line (outer)
                    right_boundary = odr_road.get_lane_border_line(
                        lane=odr_lane,
                        s_start=lanesection_s0,
                        s_end=lanesection_send,
                        eps=self.config.eps,
                        outer=(lane_id < 0)  # Right lanes: right boundary is outer
                    )
                    
                    # Calculate midpoints between corresponding boundary points
                    if left_boundary and right_boundary and hasattr(left_boundary, 'array') and hasattr(right_boundary, 'array'):
                        left_points = left_boundary.array
                        right_points = right_boundary.array
                        
                        # Use the minimum length to avoid index errors
                        num_points = min(len(left_points), len(right_points))
                        
                        for i in range(num_points):
                            left_pos = left_points[i].array
                            right_pos = right_points[i].array
                            
                            # Calculate midpoint
                            mid_x = (left_pos[0] + right_pos[0]) / 2.0
                            mid_y = (left_pos[1] + right_pos[1]) / 2.0
                            mid_z = (left_pos[2] + right_pos[2]) / 2.0
                            
                            centerline_points.append(Point3D(x=mid_x, y=mid_y, z=mid_z))
                        
                        # Estimate s values for sampled points (linear interpolation)
                        if num_points > 1:
                            for i in range(num_points):
                                s_val = lanesection_s0 + (lanesection_send - lanesection_s0) * i / (num_points - 1)
                                centerline_s_values.append(s_val)
                        elif num_points == 1:
                            centerline_s_values.append(lanesection_s0)
                            
                except Exception as e:
                    logger.warning(f"Failed to extract centerline for lane {local_lane_id}: {e}")
            
            # Add exact endpoints to ensure continuity at road connections
            # Calculate the centerline position at s_start and s_end using lane border lines
            if hasattr(odr_road, 'get_lane_border_line'):
                try:
                    # Get left and right boundaries at s_start (single point)
                    # Use a very small eps to get just the start point
                    tiny_eps = 0.01
                    
                    left_start = odr_road.get_lane_border_line(
                        lane=odr_lane,
                        s_start=lanesection_s0,
                        s_end=lanesection_s0 + tiny_eps,
                        eps=tiny_eps,
                        outer=(lane_id > 0)
                    )
                    
                    right_start = odr_road.get_lane_border_line(
                        lane=odr_lane,
                        s_start=lanesection_s0,
                        s_end=lanesection_s0 + tiny_eps,
                        eps=tiny_eps,
                        outer=(lane_id < 0)
                    )
                    
                    # Calculate start point as midpoint
                    if (left_start and right_start and
                        hasattr(left_start, 'array') and hasattr(right_start, 'array') and
                        len(left_start.array) > 0 and len(right_start.array) > 0):
                        left_pos = left_start.array[0].array
                        right_pos = right_start.array[0].array
                        start_point = Point3D(
                            x=(left_pos[0] + right_pos[0]) / 2.0,
                            y=(left_pos[1] + right_pos[1]) / 2.0,
                            z=(left_pos[2] + right_pos[2]) / 2.0
                        )
                        
                        # Add start point if not already present
                        endpoint_tolerance = 0.5  # meters
                        start_exists = False
                        for pt in centerline_points:
                            dist = ((pt.x - start_point.x)**2 + (pt.y - start_point.y)**2)**0.5
                            if dist < endpoint_tolerance:
                                start_exists = True
                                break
                        
                        if not start_exists and centerline_points:
                            centerline_points.insert(0, start_point)
                            centerline_s_values.insert(0, lanesection_s0)
                    
                    # Get left and right boundaries at s_end (single point)
                    left_end = odr_road.get_lane_border_line(
                        lane=odr_lane,
                        s_start=lanesection_send - tiny_eps,
                        s_end=lanesection_send,
                        eps=tiny_eps,
                        outer=(lane_id > 0)
                    )
                    
                    right_end = odr_road.get_lane_border_line(
                        lane=odr_lane,
                        s_start=lanesection_send - tiny_eps,
                        s_end=lanesection_send,
                        eps=tiny_eps,
                        outer=(lane_id < 0)
                    )
                    
                    # Calculate end point as midpoint
                    if (left_end and right_end and
                        hasattr(left_end, 'array') and hasattr(right_end, 'array') and
                        len(left_end.array) > 0 and len(right_end.array) > 0):
                        left_pos = left_end.array[-1].array
                        right_pos = right_end.array[-1].array
                        end_point = Point3D(
                            x=(left_pos[0] + right_pos[0]) / 2.0,
                            y=(left_pos[1] + right_pos[1]) / 2.0,
                            z=(left_pos[2] + right_pos[2]) / 2.0
                        )
                        
                        # Add end point if not already present
                        endpoint_tolerance = 0.5  # meters
                        end_exists = False
                        for pt in centerline_points:
                            dist = ((pt.x - end_point.x)**2 + (pt.y - end_point.y)**2)**0.5
                            if dist < endpoint_tolerance:
                                end_exists = True
                                break
                        
                        if not end_exists and centerline_points:
                            centerline_points.append(end_point)
                            centerline_s_values.append(lanesection_send)
                        
                except Exception as e:
                    logger.debug(f"Could not add exact endpoints for lane {local_lane_id}: {e}")
            
            # Sort centerline points by s value to ensure proper ordering
            if len(centerline_points) == len(centerline_s_values) and len(centerline_s_values) > 1:
                sorted_pairs = sorted(zip(centerline_s_values, centerline_points), key=lambda x: x[0])
                centerline_points = [pt for _, pt in sorted_pairs]
            
            # Convert to local coordinates
            # Note: We clip centerline points at map_range boundary to ensure:
            # 1. Partially-visible roads show their visible portion properly
            # 2. Centerlines don't extend beyond the requested map range
            # 3. Visualization shows correct data within the range
            if self.transformer:
                local_centerline = []
                filtered_s_values = []
                for point, s_val in zip(centerline_points, centerline_s_values):
                    result = self.transformer.global_to_local(point)
                    if result.success:
                        local_centerline.append(result.point)
                        filtered_s_values.append(s_val)
                centerline_points = local_centerline
                centerline_s_values = filtered_s_values
                
                # If all points failed to convert, skip this lane
                if not centerline_points:
                    return ConversionResult(
                        success=False,
                        data=None,
                        errors=["All centerline points failed coordinate transformation"]
                    )
                
                # Clip centerline at map_range boundary
                # This ensures that roads partially within range show only their visible portion
                if self.config and hasattr(self.config, 'map_range') and len(centerline_points) > 1:
                    clipped_centerline, clipped_s_values = self._clip_centerline_at_range(
                        centerline_points, centerline_s_values, self.config.map_range
                    )
                    if clipped_centerline:
                        centerline_points = clipped_centerline
                        centerline_s_values = clipped_s_values
            
            # Resample centerline to ensure uniform point spacing
            # This fixes the issue where pyOpenDRIVE's sampling produces uneven gaps
            if len(centerline_points) > 2:
                resampled_points, resampled_s_values = self._resample_centerline_uniform(
                    centerline_points, centerline_s_values, self.config.eps
                )
                if len(resampled_points) >= 2:
                    centerline_points = resampled_points
                    centerline_s_values = resampled_s_values
            
            # Calculate per-point speed limits based on s values
            max_speed_limits = []
            min_speed_limits = []
            speed_limit_types = []
            
            # Get speed records from road (road-level speed limits)
            # pyOpenDRIVE exposes s_to_speed as a property (not a method)
            s_to_speed = None
            if hasattr(odr_road, 's_to_speed'):
                s_to_speed = odr_road.s_to_speed
            elif hasattr(odr_road, 'get_s_to_speed'):
                # Fallback for older API
                s_to_speed = odr_road.get_s_to_speed()
            
            # Get lane-level speed records (priority over road-level)
            # Lane speed is defined inside <lane><speed sOffset="..." max="..."/></lane>
            # pyOpenDRIVE exposes this as speed_records (list of PyLaneSpeedRecord)
            lane_speed_records = None
            if hasattr(odr_lane, 'speed_records'):
                lane_speed_data = odr_lane.speed_records
                if lane_speed_data is not None and len(lane_speed_data) > 0:
                    # Convert list to dict indexed by s_offset for easier lookup
                    lane_speed_records = {}
                    for speed_entry in lane_speed_data:
                        s_offset = float(speed_entry.s_offset) if hasattr(speed_entry, 's_offset') else 0.0
                        lane_speed_records[s_offset] = speed_entry
            
            # For each centerline point, look up the speed limit at its s value
            for s_val in centerline_s_values:
                max_speed = 0.0  # Default: no speed limit
                min_speed = 0.0  # Default: no minimum speed
                speed_type = SpeedLimitType.REGULAR
                
                # Priority 1: Check lane-level speed limits (relative to lane section start)
                # sOffset is relative to the lane section start (lanesection_s0)
                applicable_lane_speed = None
                if lane_speed_records:
                    # s_val is absolute s coordinate on the road
                    # Convert to relative s within the lane section
                    s_relative = s_val - lanesection_s0
                    for s_offset, speed_entry in lane_speed_records.items():
                        # Find the speed entry that applies at this relative s position
                        # Each entry applies from its sOffset until the next entry or end of lane section
                        entry_s_offset = float(s_offset)
                        # Check if this entry applies (s_relative >= sOffset)
                        if s_relative >= entry_s_offset:
                            if applicable_lane_speed is None or entry_s_offset > applicable_lane_speed[0]:
                                applicable_lane_speed = (entry_s_offset, speed_entry)
                
                if applicable_lane_speed:
                    speed_entry = applicable_lane_speed[1]
                    # max and unit are bytes from pyOpenDRIVE, need to decode
                    max_val = speed_entry.max
                    if isinstance(max_val, bytes):
                        max_val = max_val.decode('utf-8')
                    max_speed = float(max_val) if max_val else 0.0
                    # Handle unit - default is m/s if not specified
                    unit = speed_entry.unit if hasattr(speed_entry, 'unit') else b'm/s'
                    if isinstance(unit, bytes):
                        unit = unit.decode('utf-8')
                    max_speed = self.convert_speed_limit(max_speed, unit)
                elif s_to_speed:
                    # Priority 2: Fall back to road-level speed limits
                    # Find the applicable speed record for this s value
                    # Speed records are indexed by their start s value
                    applicable_speed = None
                    for record_s, speed_record in s_to_speed.items():
                        # Check if this record applies at s_val
                        record_s_val = float(record_s) if not isinstance(record_s, float) else record_s
                        record_s_end = float(speed_record.s_end) if hasattr(speed_record, 's_end') else lanesection_send
                        
                        if record_s_val <= s_val <= record_s_end:
                            if applicable_speed is None or record_s_val > float(applicable_speed[0]):
                                applicable_speed = (record_s, speed_record)
                    
                    if applicable_speed:
                        speed_record = applicable_speed[1]
                        # Handle bytes from pyOpenDRIVE
                        max_val = speed_record.max
                        if isinstance(max_val, bytes):
                            max_val = max_val.decode('utf-8')
                        max_speed = float(max_val) if max_val else 0.0
                        
                        unit = speed_record.unit if hasattr(speed_record, 'unit') else 'm/s'
                        if isinstance(unit, bytes):
                            unit = unit.decode('utf-8')
                        max_speed = self.convert_speed_limit(max_speed, unit)
                        
                        # Some roads may have min speed limit
                        if hasattr(speed_record, 'min') and speed_record.min is not None:
                            min_val = speed_record.min
                            if isinstance(min_val, bytes):
                                min_val = min_val.decode('utf-8')
                            min_speed = self.convert_speed_limit(float(min_val), unit)
                
                max_speed_limits.append(max_speed)
                min_speed_limits.append(min_speed)
                speed_limit_types.append(speed_type)
            
            # Safety check: ensure speed limit lists match centerline points length
            if len(max_speed_limits) != len(centerline_points):
                logger.warning(f"Speed limit list length ({len(max_speed_limits)}) != centerline points length ({len(centerline_points)}), adjusting...")
                # If we have fewer speed limits than points, fill with default values
                while len(max_speed_limits) < len(centerline_points):
                    max_speed_limits.append(0.0)
                    min_speed_limits.append(0.0)
                    speed_limit_types.append(SpeedLimitType.REGULAR)
                # If we have more speed limits than points, truncate
                if len(max_speed_limits) > len(centerline_points):
                    max_speed_limits = max_speed_limits[:len(centerline_points)]
                    min_speed_limits = min_speed_limits[:len(centerline_points)]
                    speed_limit_types = speed_limit_types[:len(centerline_points)]
            
            # Create Lane object
            lane = Lane(
                lane_id=local_lane_id,
                lane_type=lane_type,
                lane_direction=lane_direction,
                centerline_points=centerline_points,
                left_boundary_segment_indices=[],
                right_boundary_segment_indices=[],
                max_speed_limits=max_speed_limits,
                min_speed_limits=min_speed_limits,
                speed_limit_types=speed_limit_types,
                # XODR-specific fields
                original_lane_id=lane_id,
                original_road_id=road_id,
                original_junction_id=junction_id,
                map_source_type="XODR",
                map_source_id=self.config.map_source_id,
                road_id=road_id,
                junction_id=junction_id
            )
            
            return ConversionResult(
                success=True,
                data=lane,
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Error converting lane to lane: {e}")
            return ConversionResult(
                success=False,
                data=None,
                errors=[f"Lane conversion failed: {str(e)}"]
            )
    
    def convert_boundary_segment(
        self,
        odr_road: Any,
        odr_lane: Any,
        is_outer: bool,
        road_id: int,
        lanesection_s0: float,
        lanesection_end: float,
        lane_id: int
    ) -> Optional[LaneBoundarySegment]:
        """
        Convert XODR boundary to LocalMap LaneBoundarySegment.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            odr_lane: pyOpenDRIVE Lane object
            is_outer: Whether this is the outer boundary
            road_id: Road ID
            lanesection_s0: Lane section start s coordinate
            lanesection_end: Lane section end s coordinate
            lane_id: Lane ID
            
        Returns:
            LaneBoundarySegment or None if conversion fails
        """
        try:
            # Extract boundary points
            boundary_points = []
            roadid = odr_road.id
            if hasattr(odr_road, 'get_lane_border_line'):
                try:
                    border_line = odr_road.get_lane_border_line(
                        lane=odr_lane,
                        eps=self.config.eps,
                        outer=is_outer
                    )
                    if border_line and hasattr(border_line, 'array'):
                        # border_line.array contains a list of PyVec3D objects
                        # Each PyVec3D has an 'array' property that returns [x, y, z]
                        for v in border_line.array:
                            boundary_points.append(Point3D(x=v.array[0], y=v.array[1], z=v.array[2]))
                except Exception as e:
                    logger.warning(f"Failed to extract boundary line: {e}")
            
            if not boundary_points:
                return None
            
            # Convert to local coordinates
            if self.transformer:
                local_boundary = []
                for point in boundary_points:
                    result = self.transformer.global_to_local(point)
                    if result.success:
                        local_boundary.append(result.point)
                boundary_points = local_boundary
                
                # If all points failed to convert, return None
                if not boundary_points:
                    return None
                
                # Clip boundary points at rectangular map_range boundary
                # This ensures boundaries match the visualization's axis limits
                if self.config and hasattr(self.config, 'map_range') and len(boundary_points) > 1:
                    clipped_boundary = self._clip_boundary_at_range(boundary_points, self.config.map_range)
                    if clipped_boundary:
                        boundary_points = clipped_boundary
                    else:
                        return None  # All points were outside range
            
            # Extract roadmark properties using get_roadmarks() and roadmark_groups
            # RoadMark has type, s_start, s_end, width, group_s0
            # RoadMarkGroup has type, color, weight, material, etc.
            # We match RoadMark.group_s0 to RoadMarkGroup.s_offset
            
            # Get roadmark groups for color information
            roadmark_group_map = {}
            if hasattr(odr_lane, 'roadmark_groups'):
                for group in odr_lane.roadmark_groups:
                    if hasattr(group, 's_offset'):
                        roadmark_group_map[group.s_offset] = group
            
            # Build list of roadmark segments: [(s_start, s_end, type, color, width), ...]
            roadmark_segments = []
            
            if hasattr(odr_lane, 'get_roadmarks'):
                roadmarks = odr_lane.get_roadmarks(lanesection_s0, lanesection_end)
                
                if roadmarks:
                    for roadmark in roadmarks:
                        rm_type = roadmark.type
                        rm_width = roadmark.width if hasattr(roadmark, 'width') else 0.1
                        rm_s_start = roadmark.s_start if hasattr(roadmark, 's_start') else lanesection_s0
                        rm_s_end = roadmark.s_end if hasattr(roadmark, 's_end') else lanesection_end
                        
                        # Try to find matching roadmark group for color
                        rm_color = 'white'
                        if hasattr(roadmark, 'group_s0'):
                            group = roadmark_group_map.get(roadmark.group_s0)
                            if group and hasattr(group, 'color'):
                                rm_color = group.color
                        
                        roadmark_segments.append((rm_s_start, rm_s_end, rm_type, rm_color, rm_width))
            
            # Build per-point attribute lists that correspond 1:1 with boundary_points
            # Each boundary point gets attributes based on which roadmark segment it falls into
            boundary_types = []
            boundary_line_shapes = []
            boundary_colors = []
            boundary_thicknesses = []
            is_virtuals = []
            
            # Get s values for each boundary point by sampling the road geometry
            boundary_s_values = []
            if boundary_points and hasattr(odr_road, 'get_lane_border_line'):
                for _ in boundary_points:
                    # We'll compute s values by interpolating along the lane
                    # For now, use uniform distribution as approximation
                    pass
            
            # If we have roadmark segments, we need to map each point to its segment
            # Since boundary_points are sampled uniformly along s, we can estimate s for each point
            if roadmark_segments and boundary_points:
                # Sort roadmark segments by s_start
                roadmark_segments.sort(key=lambda x: x[0])
                
                # Estimate s value for each boundary point based on its index
                # Assume points are uniformly distributed from lanesection_s0 to lanesection_end
                total_s_length = lanesection_end - lanesection_s0
                num_points = len(boundary_points)
                
                for point_idx in range(num_points):
                    # Estimate s value for this point
                    estimated_s = lanesection_s0 + (point_idx / max(1, num_points - 1)) * total_s_length
                    
                    # Find the roadmark segment this point falls into
                    matched_segment = None
                    for rm_s_start, rm_s_end, rm_type, rm_color, rm_width in roadmark_segments:
                        if rm_s_start <= estimated_s <= rm_s_end:
                            matched_segment = (rm_type, rm_color, rm_width)
                            break
                    
                    if matched_segment is None:
                        # Point doesn't fall into any segment, use first segment's properties
                        if roadmark_segments:
                            _, _, rm_type, rm_color, rm_width = roadmark_segments[0]
                            matched_segment = (rm_type, rm_color, rm_width)
                        else:
                            matched_segment = ('none', 'white', 0.1)
                    
                    rm_type, rm_color, rm_width = matched_segment
                    boundary_types.append(self.convert_boundary_type(rm_type))
                    boundary_line_shapes.append(self.convert_boundary_line_shape(rm_type))
                    boundary_colors.append(self.convert_boundary_color(rm_color))
                    boundary_thicknesses.append(rm_width)
                    is_virtuals.append(rm_type.lower() == 'none')
            
            elif boundary_points:
                # No roadmark segments found - use default VIRTUAL values for all points
                default_type = BoundaryType.VIRTUAL
                default_shape = BoundaryLineShape.UNKNOWN
                default_color = BoundaryColor.UNKNOWN
                default_thickness = 0.1
                default_is_virtual = True
                
                for _ in boundary_points:
                    boundary_types.append(default_type)
                    boundary_line_shapes.append(default_shape)
                    boundary_colors.append(default_color)
                    boundary_thicknesses.append(default_thickness)
                    is_virtuals.append(default_is_virtual)
                
                logger.debug(f"No roadmarks found for boundary segment (road={road_id}, lane={lane_id}), "
                           f"using VIRTUAL type for {len(boundary_points)} points")
            
            # Generate boundary segment ID
            boundary_suffix = 'outer' if is_outer else 'inner'
            segment_id = self.generate_boundary_id(road_id, lanesection_s0, lane_id, lanesection_s0, boundary_suffix)
            
            return LaneBoundarySegment(
                segment_id=segment_id,
                boundary_points=boundary_points,
                boundary_types=boundary_types,
                boundary_line_shapes=boundary_line_shapes,
                boundary_colors=boundary_colors,
                boundary_thicknesses=boundary_thicknesses,
                is_virtuals=is_virtuals
            )
            
        except Exception as e:
            logger.error(f"Error converting boundary segment: {e}")
            return None

    
    def convert_speed_limit_segment(
        self,
        odr_road: Any,
        speed_record: Any,
        road_id: int
    ) -> Optional[SpeedLimitSegment]:
        """
        Convert XODR SpeedRecord to LocalMap SpeedLimitSegment.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            speed_record: pyOpenDRIVE SpeedRecord object
            road_id: Road ID
            
        Returns:
            SpeedLimitSegment or None if conversion fails
        """
        try:
            # Convert speed limit to m/s
            speed_limit = self.convert_speed_limit(speed_record.max, speed_record.unit)
            
            # Get start and end positions from road geometry
            start_point = Point3D(x=0.0, y=0.0, z=0.0)
            end_point = Point3D(x=0.0, y=0.0, z=0.0)
            
            if hasattr(odr_road, 'get_xyz'):
                try:
                    xyz_start = odr_road.get_xyz(speed_record.s, 0.0, 0.0)
                    xyz_end = odr_road.get_xyz(speed_record.s_end, 0.0, 0.0)
                    
                    start_point = Point3D(x=xyz_start.array[0], y=xyz_start.array[1], z=xyz_start.array[2])
                    end_point = Point3D(x=xyz_end.array[0], y=xyz_end.array[1], z=xyz_end.array[2])
                except Exception as e:
                    logger.warning(f"Failed to get xyz for speed limit: {e}")
            
            # Convert to local coordinates
            if self.transformer:
                start_result = self.transformer.global_to_local(start_point)
                end_result = self.transformer.global_to_local(end_point)
                if start_result.success:
                    start_point = start_result.point
                if end_result.success:
                    end_point = end_result.point
            
            return SpeedLimitSegment(
                segment_id=0,  # Will be assigned by builder
                speed_limit=speed_limit,
                speed_limit_type=SpeedLimitType.REGULAR,
                start_position=start_point,
                end_position=end_point
            )
            
        except Exception as e:
            logger.error(f"Error converting speed limit segment: {e}")
            return None
    
    def convert_traffic_sign(
        self,
        odr_road: Any,
        odr_signal: Any,
        road_id: int
    ) -> Optional[TrafficSign]:
        """
        Convert XODR RoadSignal to LocalMap TrafficSign.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            odr_signal: pyOpenDRIVE RoadSignal object
            road_id: Road ID
            
        Returns:
            TrafficSign or None if conversion fails
        """
        try:
            # Get signal position
            position = Point3D(x=0.0, y=0.0, z=0.0)
            if hasattr(odr_road, 'get_xyz'):
                try:
                    xyz = odr_road.get_xyz(odr_signal.s0, odr_signal.t0, odr_signal.zOffset)
                    position = Point3D(x=xyz.array[0], y=xyz.array[1], z=xyz.array[2])
                except Exception as e:
                    logger.warning(f"Failed to get xyz for signal: {e}")
            
            # Convert to local coordinates
            if self.transformer:
                result = self.transformer.global_to_local(position)
                if result.success:
                    position = result.point
            
            # Get signal type
            signal_type = int(odr_signal.type) if hasattr(odr_signal, 'type') else 0
            sign_type = self.convert_traffic_sign_type(signal_type)
            
            # Get signal value
            value = 0.0
            if hasattr(odr_signal, 'value'):
                value = float(odr_signal.value)
            
            # Get signal text
            text_content = ""
            if hasattr(odr_signal, 'text'):
                text_content = odr_signal.text.decode() if isinstance(odr_signal.text, bytes) else odr_signal.text
            
            return TrafficSign(
                traffic_sign_id=int(odr_signal.id),
                position=position,
                sign_type=sign_type,
                associated_lane_id=0,  # Will be assigned by builder
                distance_to_sign=0.0,  # Will be calculated by builder
                value=value,
                text_content=text_content,
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error converting traffic sign: {e}")
            return None
    
    def convert_crosswalk(
        self,
        odr_road: Any,
        odr_object: Any,
        road_id: int
    ) -> Optional[Crosswalk]:
        """
        Convert XODR RoadObject (crosswalk) to LocalMap Crosswalk.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            odr_object: pyOpenDRIVE RoadObject object
            road_id: Road ID
            
        Returns:
            Crosswalk or None if conversion fails
        """
        try:
            # Get object position
            position = Point3D(x=0.0, y=0.0, z=0.0)
            if hasattr(odr_road, 'get_xyz'):
                try:
                    xyz = odr_road.get_xyz(odr_object.s0, odr_object.t0, odr_object.z0)
                    position = Point3D(x=xyz.array[0], y=xyz.array[1], z=xyz.array[2])
                except Exception as e:
                    logger.warning(f"Failed to get xyz for object: {e}")
            
            # Convert to local coordinates
            if self.transformer:
                result = self.transformer.global_to_local(position)
                if result.success:
                    position = result.point
            
            # Extract polygon points from mesh
            polygon_points = []
            if hasattr(odr_road, 'get_road_object_mesh'):
                try:
                    mesh = odr_road.get_road_object_mesh(odr_object, eps=self.config.eps)
                    if mesh and hasattr(mesh, 'vertices'):
                        for v in mesh.vertices:
                            polygon_points.append(Point3D(x=v.array[0], y=v.array[1], z=v.array[2]))
                except Exception as e:
                    logger.warning(f"Failed to extract crosswalk mesh: {e}")
            
            # Convert to local coordinates
            if self.transformer:
                local_polygon = []
                for point in polygon_points:
                    result = self.transformer.global_to_local(point)
                    if result.success:
                        local_polygon.append(result.point)
                polygon_points = local_polygon
            
            return Crosswalk(
                crosswalk_id=int(odr_object.id),
                polygon_points=polygon_points,
                crosswalk_width=odr_object.width if hasattr(odr_object, 'width') else 3.0,
                crosswalk_length=odr_object.length if hasattr(odr_object, 'length') else 3.0,
                has_traffic_light=False,  # Will be determined from associated signals
                associated_traffic_light_id=0,
                associated_lane_id=0,
                has_pedestrian_island=False,
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error converting crosswalk: {e}")
            return None
    
    def convert_road_marking(
        self,
        odr_road: Any,
        odr_object: Any,
        road_id: int
    ) -> Optional[RoadMarking]:
        """
        Convert XODR RoadObject to LocalMap RoadMarking.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            odr_object: pyOpenDRIVE RoadObject object
            road_id: Road ID
            
        Returns:
            RoadMarking or None if conversion fails
        """
        try:
            # Get object position
            position = Point3D(x=0.0, y=0.0, z=0.0)
            if hasattr(odr_road, 'get_xyz'):
                try:
                    xyz = odr_road.get_xyz(odr_object.s0, odr_object.t0, odr_object.z0)
                    position = Point3D(x=xyz.array[0], y=xyz.array[1], z=xyz.array[2])
                except Exception as e:
                    logger.warning(f"Failed to get xyz for object: {e}")
            
            # Convert to local coordinates
            if self.transformer:
                result = self.transformer.global_to_local(position)
                if result.success:
                    position = result.point
            
            # Determine marking type from object name/type
            marking_type = RoadMarkingType.UNKNOWN
            object_name = odr_object.name.decode() if isinstance(odr_object.name, bytes) else odr_object.name
            
            if 'arrow' in object_name.lower():
                if 'left' in object_name.lower():
                    marking_type = RoadMarkingType.ARROW_LEFT
                elif 'right' in object_name.lower():
                    marking_type = RoadMarkingType.ARROW_RIGHT
                elif 'straight' in object_name.lower():
                    marking_type = RoadMarkingType.ARROW_STRAIGHT
            elif 'stop' in object_name.lower():
                marking_type = RoadMarkingType.STOP_LINE
            
            return RoadMarking(
                road_marking_id=int(odr_object.id),
                marking_type=marking_type,
                marking_points=[position],  # Single point for now
                marking_width=odr_object.width if hasattr(odr_object, 'width') else 0.2,
                marking_color=RoadMarkingColor.WHITE,
                associated_lane_id=0,
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Error converting road marking: {e}")
            return None
    
    def get_boundary_segments(self) -> List[LaneBoundarySegment]:
        """
        Get all boundary segments created during conversion.
        
        Returns:
            List of LaneBoundarySegment objects
        """
        return self._boundary_segments
    
    def get_roads(self) -> Dict[int, Road]:
        """
        Get all Road objects created during conversion.
        
        Returns:
            Dictionary mapping road IDs to Road objects
        """
        return self._roads
    
    def get_junctions(self) -> Dict[int, Junction]:
        """
        Get all Junction objects created during conversion.
        
        Returns:
            Dictionary mapping junction IDs to Junction objects
        """
        return self._junctions
    
    def clear_cache(self):
        """Clear all conversion caches."""
        self._boundary_cache.clear()
        self._boundary_segments.clear()
        self._lane_id_cache.clear()
        self._next_lane_id = 1
        self._roads.clear()
        self._junctions.clear()
