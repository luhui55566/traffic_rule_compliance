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
        
        Args:
            xodr_roadmark_type: XODR roadmark type string
            
        Returns:
            LocalMap BoundaryLineShape enum
        """
        type_mapping = {
            'solid': BoundaryLineShape.SOLID,
            'broken': BoundaryLineShape.DASHED,
            'solid solid': BoundaryLineShape.DOUBLE_SOLID,
            'solid broken': BoundaryLineShape.SOLID_DASHED,
            'broken solid': BoundaryLineShape.LEFT_DASHED_RIGHT_SOLID,
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
        
        Args:
            xodr_color: XODR roadmark color string
            
        Returns:
            LocalMap BoundaryColor enum
        """
        color_mapping = {
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
        if hasattr(odr_road, 'get_s_to_speed'):
            speed_at_0 = odr_road.get_s_to_speed(0.0)
            if speed_at_0:
                speed_limit = self.convert_speed_limit(speed_at_0.max, speed_at_0.unit)
        
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
                except Exception as e:
                    logger.warning(f"Failed to extract centerline for lane {local_lane_id}: {e}")
            
            # Convert to local coordinates
            if self.transformer:
                local_centerline = []
                for point in centerline_points:
                    result = self.transformer.global_to_local(point)
                    if result.success:
                        local_centerline.append(result.point)
                centerline_points = local_centerline
            
            # Create Lane object
            lane = Lane(
                lane_id=local_lane_id,
                lane_type=lane_type,
                lane_direction=lane_direction,
                centerline_points=centerline_points,
                left_boundary_segment_indices=[],
                right_boundary_segment_indices=[],
                speed_limits=[],
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
            
            # Extract roadmark properties using get_roadmarks() and roadmark_groups
            # RoadMark has type, s_start, s_end, width, group_s0
            # RoadMarkGroup has type, color, weight, material, etc.
            # We match RoadMark.group_s0 to RoadMarkGroup.s_offset
            roadmark_type = 'none'
            roadmark_color = 'white'
            roadmark_width = 0.1
            s_start = lanesection_s0
            
            # Get roadmark groups for color information
            roadmark_group_map = {}
            if hasattr(odr_lane, 'roadmark_groups'):
                for group in odr_lane.roadmark_groups:
                    if hasattr(group, 's_offset'):
                        roadmark_group_map[group.s_offset] = group
            
            # Get roadmarks for type and width information
            # Build segmented boundary arrays with Point3D coordinates
            boundary_type_segments = []
            boundary_line_shape_segments = []
            boundary_color_segments = []
            boundary_thickness_segments = []
            is_virtual_segments = []
            
            if hasattr(odr_lane, 'get_roadmarks'):
                roadmarks = odr_lane.get_roadmarks(lanesection_s0, lanesection_end)
                
                if roadmarks:
                    # Process each roadmark and create a boundary segment for it
                    for roadmark in roadmarks:
                        roadmark_type = roadmark.type
                        roadmark_width = roadmark.width if hasattr(roadmark, 'width') else 0.1
                        s_start = roadmark.s_start if hasattr(roadmark, 's_start') else lanesection_s0
                        
                        # Try to find matching roadmark group for color
                        if hasattr(roadmark, 'group_s0'):
                            group = roadmark_group_map.get(roadmark.group_s0)
                            if group and hasattr(group, 'color'):
                                roadmark_color = group.color
                            else:
                                roadmark_color = 'white'
                        
                        # Calculate the boundary point at this s coordinate
                        # Get the t offset for the boundary at s_start
                        try:
                            global_point=None
                            border_line = odr_road.get_lane_border_line(
                                lane=odr_lane,
                                s_start = s_start, 
                                s_end = s_start+0.001,
                                eps=self.config.eps,
                                outer=is_outer
                                )
                            if border_line and hasattr(border_line, 'array'):
                            # border_line.array contains a list of PyVec3D objects
                            # Each PyVec3D has an 'array' property that returns [x, y, z]
                                v = border_line.array[0]
                                global_point = Point3D(x=v.array[0], y=v.array[1], z=v.array[2])
                            
                            # Calculate global xyz coordinates at (s_start, t_offset, 0)
                            if global_point:
                                # Convert to local coordinates
                                if self.transformer:
                                    result = self.transformer.global_to_local(global_point)
                                    if result.success:
                                        start_point = result.point
                                    else:
                                        start_point = global_point
                                else:
                                    start_point = global_point
                            else:
                                start_point = Point3D(x=0, y=0, z=0)
                        except Exception as e:
                            logger.warning(f"Failed to calculate boundary point at s={s_start}: {e}")
                            start_point = Point3D(x=0, y=0, z=0)
                        
                        # Add to segment arrays with Point3D coordinates
                        boundary_type_segments.append((start_point, self.convert_boundary_type(roadmark_type)))
                        boundary_line_shape_segments.append((start_point, self.convert_boundary_line_shape(roadmark_type)))
                        boundary_color_segments.append((start_point, self.convert_boundary_color(roadmark_color)))
                        boundary_thickness_segments.append((start_point, roadmark_width))
                        is_virtual_segments.append((start_point, roadmark_type.lower() == 'none'))
            
            # Generate boundary segment ID
            boundary_suffix = 'outer' if is_outer else 'inner'
            segment_id = self.generate_boundary_id(road_id, lanesection_s0, lane_id, lanesection_s0, boundary_suffix)
            
            return LaneBoundarySegment(
                segment_id=segment_id,
                boundary_points=boundary_points,
                boundary_type_segments=boundary_type_segments,
                boundary_line_shape_segments=boundary_line_shape_segments,
                boundary_color_segments=boundary_color_segments,
                boundary_thickness_segments=boundary_thickness_segments,
                is_virtual_segments=is_virtual_segments
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
