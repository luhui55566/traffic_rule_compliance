"""
Map conversion module for LocalMapConstruct.

This module provides functionality for converting MapAPI data structures
to LocalMap data structures.
"""

import logging
from typing import List, Optional, Dict, Any

from common.local_map.local_map_data import (
    Lane, Point3D, Pose, LaneType, LaneDirection,
    TrafficLight, TrafficLightState, TrafficLightColor,
    TrafficLightShape, TrafficLightStatus, TrafficLightType,
    TrafficSign, TrafficSignType, LaneBoundarySegment,
    BoundaryType, BoundaryLineShape, BoundaryColor,
    SpeedLimitSegment, SpeedLimitType
)
from map_node.map_common.base import Position
from map_node.mapapi.types import Lanelet as MapAPILanelet, TrafficSign as MapAPITrafficSign, SignType
from .transformer import CoordinateTransformer
from .config_types import ConversionResult

logger = logging.getLogger(__name__)


class MapConverter:
    """
    Map converter for transforming MapAPI data to LocalMap format.

    This class handles the conversion of various map elements from MapAPI's
    internal format to the standardized LocalMap format used by the
    traffic rule verification system.
    """

    def __init__(self, transformer: CoordinateTransformer):
        """
        Initialize the map converter.

        Args:
            transformer: Coordinate transformer for coordinate conversions
        """
        self.transformer = transformer

    def convert_lanelet_to_lane(
        self,
        lanelet: MapAPILanelet,
        ego_pose: Pose
    ) -> ConversionResult:
        """
        Convert a MapAPI Lanelet to a LocalMap Lane.

        Args:
            lanelet: MapAPI Lanelet object
            ego_pose: Ego vehicle pose for coordinate transformation

        Returns:
            ConversionResult with the converted Lane or error information
        """
        try:
            # Convert lanelet ID
            lane_id = int(lanelet.id) if lanelet.id.isdigit() else hash(lanelet.id)

            # Convert lanelet type
            lane_type = self._convert_lanelet_type(lanelet.lanelet_type)

            # Convert lane direction (assume forward for now)
            lane_direction = LaneDirection.FORWARD

            # Convert centerline points
            centerline_points = self._convert_centerline(lanelet, ego_pose)

            # Convert speed limits
            speed_limits = self._convert_speed_limits(lanelet, ego_pose)

            # Build the Lane object (without boundary segments for now)
            # Boundary segments are now handled by convert_lanelets_to_lanes
            lane = Lane(
                lane_id=lane_id,
                lanelet_id=lane_id,
                lane_type=lane_type,
                lane_direction=lane_direction,
                centerline_points=centerline_points,
                left_boundary_segment_indices=[],
                right_boundary_segment_indices=[],
                speed_limits=speed_limits
            )

            # Return lane only (boundary segments are handled separately)
            return ConversionResult(
                success=True,
                data=lane,
                warnings=[],
                errors=[]
            )

        except Exception as e:
            logger.error(f"Error converting lanelet to lane: {e}")
            return ConversionResult(
                success=False,
                data=None,
                errors=[f"Lanelet conversion failed: {str(e)}"]
            )

    def convert_traffic_signs(
        self,
        traffic_signs: List[MapAPITrafficSign],
        ego_pose: Pose
    ) -> ConversionResult:
        """
        Convert MapAPI TrafficSigns to LocalMap TrafficSigns.

        Args:
            traffic_signs: List of MapAPI TrafficSign objects
            ego_pose: Ego vehicle pose for coordinate transformation

        Returns:
            ConversionResult with the converted TrafficSigns or error information
        """
        try:
            converted_signs = []
            warnings = []

            for sign in traffic_signs:
                try:
                    # Convert position
                    pos_result = self.transformer.global_to_local(sign.position)
                    if not pos_result.success:
                        warnings.append(f"Failed to convert position for sign {sign.id}")
                        continue

                    # Convert sign type
                    sign_type = self._convert_sign_type(sign.sign_type)

                    # Convert value (e.g., speed limit value)
                    value = float(sign.value) if sign.value else 0.0

                    # Build the TrafficSign object
                    converted_sign = TrafficSign(
                        traffic_sign_id=int(sign.id) if sign.id.isdigit() else hash(sign.id),
                        lanelet_id=0,  # Will be set by caller
                        position=pos_result.point,
                        sign_type=sign_type,
                        distance_to_sign=0.0,  # Will be calculated by caller
                        value=value,
                        confidence=1.0
                    )

                    converted_signs.append(converted_sign)

                except Exception as e:
                    warnings.append(f"Failed to convert sign {sign.id}: {str(e)}")

            return ConversionResult(
                success=True,
                data=converted_signs,
                warnings=warnings,
                errors=[]
            )

        except Exception as e:
            logger.error(f"Error converting traffic signs: {e}")
            return ConversionResult(
                success=False,
                data=None,
                errors=[f"Traffic signs conversion failed: {str(e)}"]
            )

    def convert_traffic_lights(
        self,
        position: Position,
        radius: float,
        ego_pose: Pose
    ) -> ConversionResult:
        """
        Convert traffic lights in the vicinity to LocalMap format.

        Note: This is a placeholder implementation. The actual implementation
        would query MapAPI for traffic lights and convert them.

        Args:
            position: Center position for search
            radius: Search radius in meters
            ego_pose: Ego vehicle pose for coordinate transformation

        Returns:
            ConversionResult with the converted TrafficLights or error information
        """
        # Placeholder: Return empty list for now
        # In a full implementation, this would:
        # 1. Query MapAPI for traffic lights near the position
        # 2. Convert each traffic light to LocalMap format
        # 3. Return the converted list

        return ConversionResult(
            success=True,
            data=[],
            warnings=["Traffic light conversion not yet implemented"],
            errors=[]
        )

    def _convert_centerline(
        self,
        lanelet: MapAPILanelet,
        ego_pose: Pose
    ) -> List[Point3D]:
        """
        Convert lanelet centerline to local coordinates.

        Args:
            lanelet: MapAPI Lanelet object
            ego_pose: Ego vehicle pose

        Returns:
            List of centerline points in local coordinates
        """
        centerline = lanelet.centerline()
        converted_points = []

        logger.debug(f"Converting centerline for lanelet {lanelet.id}: {len(centerline)} points")

        for point in centerline:
            # MapAPI centerline uses Position (latitude, longitude)
            # For local coordinates, treat latitude as x, longitude as y
            pos = Position(
                latitude=point.latitude,
                longitude=point.longitude,
                altitude=point.altitude
            )
            result = self.transformer.global_to_local(pos)
            if result.success:
                converted_points.append(result.point)

        logger.debug(f"Converted {len(converted_points)}/{len(centerline)} centerline points for lanelet {lanelet.id}")

        return converted_points

    def _convert_boundaries(
        self,
        lanelet: MapAPILanelet,
        ego_pose: Pose,
        existing_boundary_segments: Optional[List] = None
    ) -> tuple:
        """
        Convert lanelet boundaries to boundary segments.

        Args:
            lanelet: MapAPI Lanelet object
            ego_pose: Ego vehicle pose
            existing_boundary_segments: Optional list of existing boundary segments for global ID assignment

        Returns:
            Tuple of (boundary_segments, left_indices, right_indices)
        """
        # Update transformer with current ego pose before converting boundaries
        self.transformer.update_ego_pose(ego_pose)

        if existing_boundary_segments is None:
            boundary_segments = []
        else:
            boundary_segments = existing_boundary_segments
        left_indices = []
        right_indices = []

        logger.debug(f"Converting boundaries for lanelet {lanelet.id}: left_bound={len(lanelet.left_bound) if lanelet.left_bound else 0}, right_bound={len(lanelet.right_bound) if lanelet.right_bound else 0}")

        # Convert left boundary
        if lanelet.left_bound:
            left_segment = self._convert_boundary_line(
                lanelet.left_bound,
                ego_pose,
                segment_id=len(boundary_segments)
            )
            if left_segment:
                boundary_segments.append(left_segment)
                left_indices.append(left_segment.segment_id)
                logger.debug(f"Added left boundary segment {left_segment.segment_id} for lanelet {lanelet.id}")
            else:
                logger.debug(f"Failed to convert left boundary for lanelet {lanelet.id}")
        else:
            logger.debug(f"No left boundary for lanelet {lanelet.id}")

        # Convert right boundary
        if lanelet.right_bound:
            right_segment = self._convert_boundary_line(
                lanelet.right_bound,
                ego_pose,
                segment_id=len(boundary_segments)
            )
            if right_segment:
                boundary_segments.append(right_segment)
                right_indices.append(right_segment.segment_id)
                logger.debug(f"Added right boundary segment {right_segment.segment_id} for lanelet {lanelet.id}")
            else:
                logger.debug(f"Failed to convert right boundary for lanelet {lanelet.id}")
        else:
            logger.debug(f"No right boundary for lanelet {lanelet.id}")

        return boundary_segments, left_indices, right_indices

    def _convert_boundary_line(
        self,
        boundary_points: List[Point3D],
        ego_pose: Pose,
        segment_id: int
    ) -> Optional[LaneBoundarySegment]:
        """
        Convert a boundary line to a boundary segment.

        Args:
            boundary_points: List of boundary points
            ego_pose: Ego vehicle pose
            segment_id: Segment ID

        Returns:
            LaneBoundarySegment or None if conversion fails
        """
        try:
            converted_points = []
            for point in boundary_points:
                # boundary_points are Position objects (latitude, longitude, altitude)
                # For local map coordinates, treat latitude as x, longitude as y
                logger.debug(f"  Converting boundary point: ({point.latitude:.2f}, {point.longitude:.2f}) with ego pose: ({self.transformer.ego_pose.position.x:.2f}, {self.transformer.ego_pose.position.y:.2f})")
                result = self.transformer.global_to_local(point)
                if result.success:
                    logger.debug(f"    Converted to local: ({result.point.x:.2f}, {result.point.y:.2f})")
                    converted_points.append(result.point)
                else:
                    logger.warning(f"  Failed to convert boundary point: ({point.latitude:.2f}, {point.longitude:.2f}) - {result.error}")

            if not converted_points:
                return None

            # Default boundary type (could be inferred from map data)
            return LaneBoundarySegment(
                segment_id=segment_id,
                boundary_type=BoundaryType.LINE,
                boundary_line_shape=BoundaryLineShape.SOLID,
                boundary_color=BoundaryColor.WHITE,
                boundary_thickness=0.1,
                is_virtual=False,
                boundary_points=converted_points
            )

        except Exception as e:
            logger.error(f"Error converting boundary line: {e}")
            return None

    def _convert_speed_limits(
        self,
        lanelet: MapAPILanelet,
        ego_pose: Pose
    ) -> List[SpeedLimitSegment]:
        """
        Convert lanelet speed limits to speed limit segments.

        Args:
            lanelet: MapAPI Lanelet object
            ego_pose: Ego vehicle pose

        Returns:
            List of SpeedLimitSegment objects
        """
        speed_limits = []

        logger.debug(f"Checking speed limit for lanelet {lanelet.id}: {lanelet.speed_limit}")

        if lanelet.speed_limit is not None:
            # Convert km/h to m/s
            speed_limit_ms = lanelet.speed_limit / 3.6

            # Get centerline for start/end positions
            centerline = lanelet.centerline()
            if centerline:
                start_pos = centerline[0]
                end_pos = centerline[-1]

                # Convert to local coordinates
                start_result = self.transformer.global_to_local(
                    Position(latitude=start_pos.latitude, longitude=start_pos.longitude)
                )
                end_result = self.transformer.global_to_local(
                    Position(latitude=end_pos.latitude, longitude=end_pos.longitude)
                )

                if start_result.success and end_result.success:
                    speed_limits.append(SpeedLimitSegment(
                        segment_id=0,
                        speed_limit=speed_limit_ms,
                        speed_limit_type=SpeedLimitType.REGULAR,
                        start_position=start_result.point,
                        end_position=end_result.point
                    ))
                    logger.debug(f"Added speed limit {speed_limit_ms:.2f} m/s for lanelet {lanelet.id}")

        return speed_limits

    def _convert_lanelet_type(self, lanelet_type: 'LaneletType') -> LaneType:
        """
        Convert MapAPI lanelet type to LocalMap lane type.

        Args:
            lanelet_type: MapAPI LaneletType enum

        Returns:
            LocalMap LaneType enum
        """
        # Map MapAPI lanelet types to LocalMap lane types
        type_mapping = {
            'highway': LaneType.DRIVING,
            'rural': LaneType.DRIVING,
            'urban': LaneType.DRIVING,
            'ramp': LaneType.MERGE,
            'exit': LaneType.EXIT,
            'entry': LaneType.ENTRY,
            'unknown': LaneType.UNKNOWN
        }

        return type_mapping.get(lanelet_type.value, LaneType.UNKNOWN)

    def _convert_sign_type(self, sign_type: SignType) -> TrafficSignType:
        """
        Convert MapAPI sign type to LocalMap sign type.

        Args:
            sign_type: MapAPI SignType enum

        Returns:
            LocalMap TrafficSignType enum
        """
        # Map MapAPI sign types to LocalMap sign types
        type_mapping = {
            SignType.SPEED_LIMIT: TrafficSignType.SPEED_LIMIT,
            SignType.STOP: TrafficSignType.UNKNOWN,  # Could map to specific type
            SignType.YIELD: TrafficSignType.UNKNOWN,
            SignType.NO_ENTRY: TrafficSignType.NO_ENTRY,
            SignType.ONE_WAY: TrafficSignType.UNKNOWN,
            SignType.CONSTRUCTION: TrafficSignType.ROAD_WORKS,
            SignType.FISHBONE: TrafficSignType.UNKNOWN,
            SignType.UNKNOWN: TrafficSignType.UNKNOWN
        }

        return type_mapping.get(sign_type, TrafficSignType.UNKNOWN)

    def convert_lanelets_to_lanes(
        self,
        lanelets: List[MapAPILanelet],
        ego_pose: Pose
    ) -> ConversionResult:
        """
        Convert multiple MapAPI Lanelets to LocalMap Lanes.

        Args:
            lanelets: List of MapAPI Lanelet objects
            ego_pose: Ego vehicle pose for coordinate transformation

        Returns:
            ConversionResult with the converted Lanes and boundary segments or error information
        """
        try:
            converted_lanes = []
            all_boundary_segments = []
            all_warnings = []
            all_errors = []

            for lanelet in lanelets:
                result = self.convert_lanelet_to_lane(lanelet, ego_pose)
                if result.success:
                    converted_lanes.append(result.data)
                    all_warnings.extend(result.warnings)
                else:
                    all_errors.extend(result.errors)

            # Collect boundary segments from all lanes
            for lane in converted_lanes:
                # Convert boundaries for this lanelet with global ID tracking
                boundary_segments, left_indices, right_indices = self._convert_boundaries(
                    lanelet, ego_pose, existing_boundary_segments=all_boundary_segments
                )
                all_boundary_segments = boundary_segments  # Update with new segments
                
                # Update lane with boundary indices
                lane.left_boundary_segment_indices = left_indices
                lane.right_boundary_segment_indices = right_indices

            # Return both lanes and boundary segments
            return ConversionResult(
                success=len(converted_lanes) > 0 or len(all_errors) == 0,
                data={'lanes': converted_lanes, 'boundary_segments': all_boundary_segments},
                warnings=all_warnings,
                errors=all_errors
            )

        except Exception as e:
            logger.error(f"Error converting lanelets to lanes: {e}")
            return ConversionResult(
                success=False,
                data=None,
                errors=[f"Lanelets conversion failed: {str(e)}"]
            )
