"""
LocalMap builder module for LocalMapConstruct.

This module provides functionality for assembling LocalMap data structures
from converted map elements.
"""

import logging
from typing import List, Optional
from datetime import datetime
import time

from common.local_map.local_map_data import (
    LocalMap, Lane, TrafficLight, TrafficSign,
    Header, LocalMapMetadata, LaneBoundarySegment,
    RoadMarking, Crosswalk, StopLine, Intersection
)
from .config_types import BuildResult

logger = logging.getLogger(__name__)


class LocalMapBuilder:
    """
    LocalMap builder for assembling complete LocalMap data structures.

    This class takes converted map elements (lanes, traffic lights, signs, etc.)
    and assembles them into a complete LocalMap object with proper metadata.
    """

    def __init__(self):
        """Initialize the local map builder."""
        self.boundary_segments: List[LaneBoundarySegment] = []
        self.next_segment_id = 0

    def build_local_map(
        self,
        lanes: List[Lane],
        traffic_lights: List[TrafficLight],
        traffic_signs: List[TrafficSign],
        ego_pose: 'Pose',
        map_range: float,
        boundary_segments: Optional[List[LaneBoundarySegment]] = None,
        road_markings: Optional[List[RoadMarking]] = None,
        crosswalks: Optional[List[Crosswalk]] = None,
        stop_lines: Optional[List[StopLine]] = None,
        intersections: Optional[List[Intersection]] = None
    ) -> BuildResult:
        """
        Build a complete LocalMap from converted map elements.

        Args:
            lanes: List of converted Lane objects
            traffic_lights: List of converted TrafficLight objects
            traffic_signs: List of converted TrafficSign objects
            ego_pose: Ego vehicle pose
            map_range: Map range in meters
            boundary_segments: Optional list of boundary segments
            road_markings: Optional list of road markings
            crosswalks: Optional list of crosswalks
            stop_lines: Optional list of stop lines
            intersections: Optional list of intersections

        Returns:
            BuildResult with the built LocalMap or error information
        """
        start_time = time.time()

        try:
            # Create header
            now = datetime.now()
            header = Header(
                timestamp=now,
                frame_id="ego_vehicle_local",
                sequence_number=0
            )

            # Create metadata
            # For local coordinate system, ego vehicle is at origin (0, 0)
            metadata = LocalMapMetadata(
                map_range_x=map_range,
                map_range_y=map_range,
                map_range_z=10.0,
                ego_vehicle_x=0.0,  # Ego vehicle at origin of local coordinate system
                ego_vehicle_y=0.0,
                ego_vehicle_heading=ego_pose.heading,
                ego_vehicle_velocity=0.0,
                timestamp=now
            )

            # Use provided boundary segments or internal ones
            if boundary_segments is not None:
                final_boundary_segments = boundary_segments
            else:
                final_boundary_segments = self.boundary_segments

            # Build the local map
            local_map = LocalMap(
                header=header,
                metadata=metadata,
                lanes=lanes,
                traffic_lights=traffic_lights,
                traffic_signs=traffic_signs,
                road_markings=road_markings or [],
                crosswalks=crosswalks or [],
                stop_lines=stop_lines or [],
                intersections=intersections or [],
                boundary_segments=final_boundary_segments
            )

            # Calculate build time
            build_time_ms = (time.time() - start_time) * 1000.0

            # Build statistics
            stats = {
                'num_lanes': len(lanes),
                'num_traffic_lights': len(traffic_lights),
                'num_traffic_signs': len(traffic_signs),
                'num_boundary_segments': len(final_boundary_segments),
                'num_road_markings': len(road_markings or []),
                'num_crosswalks': len(crosswalks or []),
                'num_stop_lines': len(stop_lines or []),
                'num_intersections': len(intersections or []),
                'build_time_ms': build_time_ms
            }

            logger.info(f"Built local map with {len(lanes)} lanes in {build_time_ms:.2f}ms")

            return BuildResult(
                success=True,
                local_map=local_map,
                build_time_ms=build_time_ms,
                stats=stats
            )

        except Exception as e:
            logger.error(f"Error building local map: {e}")
            build_time_ms = (time.time() - start_time) * 1000.0

            return BuildResult(
                success=False,
                local_map=None,
                build_time_ms=build_time_ms,
                stats={'error': str(e)}
            )

    def update_metadata(
        self,
        local_map: LocalMap,
        ego_pose: 'Pose',
        ego_velocity: float = 0.0
    ) -> None:
        """
        Update the metadata of an existing local map.

        Args:
            local_map: LocalMap to update
            ego_pose: New ego vehicle pose
            ego_velocity: New ego vehicle velocity
        """
        if local_map.metadata is None:
            return

        local_map.metadata.ego_vehicle_x = ego_pose.position.x
        local_map.metadata.ego_vehicle_y = ego_pose.position.y
        local_map.metadata.ego_vehicle_heading = ego_pose.heading
        local_map.metadata.ego_vehicle_velocity = ego_velocity
        local_map.metadata.timestamp = datetime.now()

        # Update header timestamp
        if local_map.header is not None:
            local_map.header.timestamp = datetime.now()
            local_map.header.sequence_number += 1

    def add_boundary_segment(
        self,
        boundary_segment: LaneBoundarySegment
    ) -> int:
        """
        Add a boundary segment to the builder's internal list.

        Args:
            boundary_segment: Boundary segment to add

        Returns:
            The segment ID assigned to the added segment
        """
        if boundary_segment.segment_id is None:
            boundary_segment.segment_id = self.next_segment_id
            self.next_segment_id += 1
        else:
            self.next_segment_id = max(self.next_segment_id, boundary_segment.segment_id + 1)

        self.boundary_segments.append(boundary_segment)
        return boundary_segment.segment_id

    def clear_boundary_segments(self) -> None:
        """Clear all boundary segments from the builder."""
        self.boundary_segments.clear()
        self.next_segment_id = 0

    def get_boundary_segment(
        self,
        segment_id: int
    ) -> Optional[LaneBoundarySegment]:
        """
        Get a boundary segment by ID.

        Args:
            segment_id: Segment ID to retrieve

        Returns:
            Boundary segment if found, None otherwise
        """
        for segment in self.boundary_segments:
            if segment.segment_id == segment_id:
                return segment
        return None

    def merge_boundary_segments(
        self,
        segments: List[LaneBoundarySegment]
    ) -> List[int]:
        """
        Merge boundary segments into the builder's internal list.

        This method adds segments to the internal list while avoiding
        duplicates (segments with the same point data).

        Args:
            segments: List of boundary segments to merge

        Returns:
            List of segment IDs for the merged segments
        """
        merged_ids = []

        for segment in segments:
            # Check for duplicate
            is_duplicate = False
            for existing in self.boundary_segments:
                if self._segments_equal(existing, segment):
                    merged_ids.append(existing.segment_id)
                    is_duplicate = True
                    break

            if not is_duplicate:
                new_id = self.add_boundary_segment(segment)
                merged_ids.append(new_id)

        return merged_ids

    def _segments_equal(
        self,
        seg1: LaneBoundarySegment,
        seg2: LaneBoundarySegment,
        tolerance: float = 0.01
    ) -> bool:
        """
        Check if two boundary segments are equal.

        Args:
            seg1: First boundary segment
            seg2: Second boundary segment
            tolerance: Position tolerance in meters

        Returns:
            True if segments are equal, False otherwise
        """
        # Check properties
        if (seg1.boundary_type != seg2.boundary_type or
            seg1.boundary_line_shape != seg2.boundary_line_shape or
            seg1.boundary_color != seg2.boundary_color or
            abs(seg1.boundary_thickness - seg2.boundary_thickness) > tolerance):
            return False

        # Check point count
        if len(seg1.boundary_points) != len(seg2.boundary_points):
            return False

        # Check points
        for p1, p2 in zip(seg1.boundary_points, seg2.boundary_points):
            if (abs(p1.x - p2.x) > tolerance or
                abs(p1.y - p2.y) > tolerance or
                abs(p1.z - p2.z) > tolerance):
                return False

        return True

    def create_empty_local_map(
        self,
        ego_pose: 'Pose',
        map_range: float = 200.0
    ) -> LocalMap:
        """
        Create an empty local map with only header and metadata.

        Args:
            ego_pose: Ego vehicle pose
            map_range: Map range in meters

        Returns:
            Empty LocalMap object
        """
        now = datetime.now()

        header = Header(
            timestamp=now,
            frame_id="ego_vehicle_local",
            sequence_number=0
        )

        metadata = LocalMapMetadata(
            map_range_x=map_range,
            map_range_y=map_range,
            map_range_z=10.0,
            ego_vehicle_x=ego_pose.position.x,
            ego_vehicle_y=ego_pose.position.y,
            ego_vehicle_heading=ego_pose.heading,
            ego_vehicle_velocity=0.0,
            timestamp=now
        )

        return LocalMap(
            header=header,
            metadata=metadata
        )
