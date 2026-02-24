"""
LocalMap builder for XODR to LocalMap conversion.

This module assembles LocalMap objects from converted XODR data structures.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from common.local_map.local_map_data import (
    LocalMap, Header, LocalMapMetadata, Point3D, Pose,
    Lane, LaneBoundarySegment, SpeedLimitSegment,
    TrafficSign, TrafficLight,
    RoadMarking, RoadMarkingType, RoadMarkingColor,
    Crosswalk, StopLine, StopLineType,
    Road, Junction, Intersection, IntersectionType
)
from .converter import XODRMapConverter
from .config_types import ConversionConfig

logger = logging.getLogger(__name__)


class LocalMapBuilder:
    """
    Builder for constructing LocalMap from converted XODR data.
    
    This class assembles the complete LocalMap structure including:
    - Lanes with boundary segments
    - Road and Junction objects (XODR extensions)
    - Traffic elements (signs, lights, markings, crosswalks)
    - Intersections
    """
    
    def __init__(self, converter: XODRMapConverter, config: ConversionConfig = None):
        """
        Initialize LocalMap builder.
        
        Args:
            converter: XODR map converter
            config: Conversion configuration
        """
        self.converter = converter
        self.config = config or ConversionConfig()
        
        # Storage for LocalMap components
        self._lanes: List[Lane] = []
        self._boundary_segments: List[LaneBoundarySegment] = []
        self._traffic_signs: List[TrafficSign] = []
        self._traffic_lights: List[TrafficLight] = []
        self._road_markings: List[RoadMarking] = []
        self._crosswalks: List[Crosswalk] = []
        self._stop_lines: List[StopLine] = []
        self._intersections: List[Intersection] = []
        
        # Lane ID to lane object mapping
        self._lane_map: Dict[int, Lane] = {}
        
        # Boundary segment ID to segment mapping
        self._boundary_map: Dict[int, LaneBoundarySegment] = {}
    
    def create_header(self) -> Header:
        """
        Create LocalMap header.
        
        Returns:
            Header object with timestamp and frame info
        """
        return Header(
            timestamp=datetime.now(),
            frame_id="ego_vehicle_local",
            sequence_number=0
        )
    
    def create_metadata(self) -> LocalMapMetadata:
        """
        Create LocalMap metadata.
        
        Returns:
            LocalMapMetadata object with ego pose and map range
        """
        return LocalMapMetadata(
            map_range_x=self.config.map_range,
            map_range_y=self.config.map_range,
            map_range_z=10.0,  # Default Z range
            ego_vehicle_x=self.config.ego_x,
            ego_vehicle_y=self.config.ego_y,
            ego_vehicle_heading=self.config.ego_heading,
            ego_vehicle_velocity=0.0,  # Static map, no velocity
            timestamp=datetime.now()
        )
    
    def add_lane(self, lane: Lane) -> bool:
        """
        Add a lane to the LocalMap.
        
        Args:
            lane: Lane object to add
            
        Returns:
            True if added successfully
        """
        if lane.lane_id in self._lane_map:
            logger.warning(f"Lane {lane.lane_id} already exists, skipping")
            return False
        
        self._lanes.append(lane)
        self._lane_map[lane.lane_id] = lane
        return True
    
    def add_boundary_segment(self, segment: LaneBoundarySegment) -> bool:
        """
        Add a boundary segment to the LocalMap.
        
        Args:
            segment: LaneBoundarySegment to add
            
        Returns:
            True if added successfully
        """
        if segment.segment_id in self._boundary_map:
            logger.warning(f"Boundary segment {segment.segment_id} already exists, skipping")
            return False
        
        self._boundary_segments.append(segment)
        self._boundary_map[segment.segment_id] = segment
        return True
    
    def add_traffic_sign(self, sign: TrafficSign) -> None:
        """
        Add a traffic sign to the LocalMap.
        
        Args:
            sign: TrafficSign object to add
        """
        self._traffic_signs.append(sign)
    
    def add_traffic_light(self, light: TrafficLight) -> None:
        """
        Add a traffic light to the LocalMap.
        
        Args:
            light: TrafficLight object to add
        """
        self._traffic_lights.append(light)
    
    def add_road_marking(self, marking: RoadMarking) -> None:
        """
        Add a road marking to the LocalMap.
        
        Args:
            marking: RoadMarking object to add
        """
        self._road_markings.append(marking)
    
    def add_crosswalk(self, crosswalk: Crosswalk) -> None:
        """
        Add a crosswalk to the LocalMap.
        
        Args:
            crosswalk: Crosswalk object to add
        """
        self._crosswalks.append(crosswalk)
    
    def add_stop_line(self, stop_line: StopLine) -> None:
        """
        Add a stop line to the LocalMap.
        
        Args:
            stop_line: StopLine object to add
        """
        self._stop_lines.append(stop_line)
    
    def add_intersection(self, intersection: Intersection) -> None:
        """
        Add an intersection to the LocalMap.
        
        Args:
            intersection: Intersection object to add
        """
        self._intersections.append(intersection)
    
    def get_lane_by_id(self, lane_id: int) -> Optional[Lane]:
        """
        Get a lane by ID.
        
        Args:
            lane_id: Lane ID
            
        Returns:
            Lane object or None if not found
        """
        return self._lane_map.get(lane_id)
    
    def get_boundary_segment_by_id(self, segment_id: int) -> Optional[LaneBoundarySegment]:
        """
        Get a boundary segment by ID.
        
        Args:
            segment_id: Boundary segment ID
            
        Returns:
            LaneBoundarySegment object or None if not found
        """
        return self._boundary_map.get(segment_id)
    
    def associate_lane_with_boundaries(
        self,
        lane: Lane,
        left_boundary_indices: List[int],
        right_boundary_indices: List[int]
    ) -> None:
        """
        Associate a lane with its boundary segments.
        
        Args:
            lane: Lane object to update
            left_boundary_indices: List of left boundary segment indices
            right_boundary_indices: List of right boundary segment indices
        """
        lane.left_boundary_segment_indices = left_boundary_indices
        lane.right_boundary_segment_indices = right_boundary_indices
    
    def associate_lane_with_speed_limits(
        self,
        lane: Lane,
        speed_limits: List[SpeedLimitSegment]
    ) -> None:
        """
        Associate speed limits with a lane.
        
        Args:
            lane: Lane object to update
            speed_limits: List of SpeedLimitSegment objects
        """
        lane.speed_limits = speed_limits
    
    def associate_traffic_elements_with_lanes(self) -> None:
        """
        Associate traffic elements (signs, lights, markings) with lanes.
        
        This method finds the nearest lane to each traffic element
        and associates them.
        """
        for sign in self._traffic_signs:
            nearest_lane = self._find_nearest_lane(sign.position)
            if nearest_lane:
                sign.associated_lane_id = nearest_lane.lane_id
                nearest_lane.associated_traffic_sign_ids.append(sign.traffic_sign_id)
        
        for light in self._traffic_lights:
            nearest_lane = self._find_nearest_lane(light.position)
            if nearest_lane:
                light.associated_lane_id = nearest_lane.lane_id
                nearest_lane.associated_traffic_light_ids.append(light.traffic_light_id)
        
        for marking in self._road_markings:
            nearest_lane = self._find_nearest_lane(marking.marking_points[0] if marking.marking_points else Point3D(x=0, y=0, z=0))
            if nearest_lane:
                marking.associated_lane_id = nearest_lane.lane_id
                nearest_lane.associated_road_marking_ids.append(marking.road_marking_id)
        
        for crosswalk in self._crosswalks:
            nearest_lane = self._find_nearest_lane(crosswalk.polygon_points[0] if crosswalk.polygon_points else Point3D(x=0, y=0, z=0))
            if nearest_lane:
                crosswalk.associated_lane_id = nearest_lane.lane_id
                nearest_lane.associated_crosswalk_ids.append(crosswalk.crosswalk_id)
        
        for stop_line in self._stop_lines:
            nearest_lane = self._find_nearest_lane(stop_line.line_points[0] if stop_line.line_points else Point3D(x=0, y=0, z=0))
            if nearest_lane:
                stop_line.associated_lane_id = nearest_lane.lane_id
                nearest_lane.associated_stop_line_ids.append(stop_line.stop_line_id)
    
    def _find_nearest_lane(self, point: Point3D) -> Optional[Lane]:
        """
        Find the nearest lane to a given point.
        
        Args:
            point: Point to find nearest lane for
            
        Returns:
            Nearest Lane object or None if no lanes
        """
        if not self._lanes:
            return None
        
        min_distance = float('inf')
        nearest_lane = None
        
        for lane in self._lanes:
            if not lane.centerline_points:
                continue
            
            # Find minimum distance to any centerline point
            for centerline_point in lane.centerline_points:
                dx = centerline_point.x - point.x
                dy = centerline_point.y - point.y
                dz = centerline_point.z - point.z
                distance = (dx*dx + dy*dy + dz*dz) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_lane = lane
        
        return nearest_lane
    
    def create_intersection_from_junction(
        self,
        junction: Junction
    ) -> Optional[Intersection]:
        """
        Create an Intersection from a Junction object.
        
        Args:
            junction: Junction object
            
        Returns:
            Intersection object or None if creation fails
        """
        if not junction.road_ids:
            return None
        
        # Determine intersection type based on connection count
        if junction.connection_count == 4:
            intersection_type = IntersectionType.FOUR_WAY
        elif junction.connection_count == 3:
            intersection_type = IntersectionType.THREE_WAY
        elif junction.connection_count > 4:
            intersection_type = IntersectionType.MULTI_LEG
        else:
            intersection_type = IntersectionType.UNKNOWN
        
        # Find all lanes connected to this junction
        incoming_lane_ids = []
        outgoing_lane_ids = []
        
        for road_id in junction.road_ids:
            road = self.converter.get_roads().get(road_id)
            if road and road.lane_ids:
                # For simplicity, add all lanes from roads connected to junction
                incoming_lane_ids.extend(road.lane_ids)
                outgoing_lane_ids.extend(road.lane_ids)
        
        # Remove duplicates
        incoming_lane_ids = list(set(incoming_lane_ids))
        outgoing_lane_ids = list(set(outgoing_lane_ids))
        
        # Find associated traffic lights
        traffic_light_ids = []
        for light in self._traffic_lights:
            if light.associated_lane_id in incoming_lane_ids or light.associated_lane_id in outgoing_lane_ids:
                traffic_light_ids.append(light.traffic_light_id)
        
        return Intersection(
            intersection_id=junction.junction_id,
            intersection_type=intersection_type,
            polygon_points=junction.polygon_points,
            incoming_lane_ids=incoming_lane_ids,
            outgoing_lane_ids=outgoing_lane_ids,
            traffic_light_ids=traffic_light_ids,
            stop_line_ids=[],  # Will be populated separately
            crosswalk_ids=[],
            has_traffic_light=junction.has_traffic_light,
            has_stop_sign=False,
            is_roundabout='roundabout' in junction.junction_type.lower(),
            associated_lane_id=0,
            confidence=1.0
        )
    
    def build_local_map(self) -> LocalMap:
        """
        Build the complete LocalMap from all components.
        
        Returns:
            Complete LocalMap object
        """
        logger.info(f"Building LocalMap with {len(self._lanes)} lanes, "
                   f"{len(self._boundary_segments)} boundary segments, "
                   f"{len(self._traffic_signs)} traffic signs, "
                   f"{len(self._traffic_lights)} traffic lights")
        
        # Get roads and junctions from converter
        roads = list(self.converter.get_roads().values())
        junctions = list(self.converter.get_junctions().values())
        
        # Create intersections from junctions
        for junction in junctions:
            intersection = self.create_intersection_from_junction(junction)
            if intersection:
                self.add_intersection(intersection)
        
        # Associate traffic elements with lanes
        self.associate_traffic_elements_with_lanes()
        
        # Create LocalMap
        return LocalMap(
            header=self.create_header(),
            metadata=self.create_metadata(),
            lanes=self._lanes,
            traffic_lights=self._traffic_lights,
            traffic_signs=self._traffic_signs,
            road_markings=self._road_markings,
            crosswalks=self._crosswalks,
            stop_lines=self._stop_lines,
            intersections=self._intersections,
            boundary_segments=self._boundary_segments,
            roads=roads,
            junctions=junctions,
            custom_data=[],
            reserved_bytes=b'',
            reserved_string=''
        )
    
    def clear(self) -> None:
        """Clear all stored components."""
        self._lanes.clear()
        self._boundary_segments.clear()
        self._traffic_signs.clear()
        self._traffic_lights.clear()
        self._road_markings.clear()
        self._crosswalks.clear()
        self._stop_lines.clear()
        self._intersections.clear()
        self._lane_map.clear()
        self._boundary_map.clear()
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the built LocalMap.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'lanes': len(self._lanes),
            'boundary_segments': len(self._boundary_segments),
            'traffic_signs': len(self._traffic_signs),
            'traffic_lights': len(self._traffic_lights),
            'road_markings': len(self._road_markings),
            'crosswalks': len(self._crosswalks),
            'stop_lines': len(self._stop_lines),
            'intersections': len(self._intersections),
            'roads': len(self.converter.get_roads()),
            'junctions': len(self.converter.get_junctions()),
        }
