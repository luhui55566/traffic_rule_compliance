"""
Coordinate transformation module for LocalMapConstruct.

This module provides coordinate transformation utilities for converting between
global (WGS84/local map) coordinates and local (ego-centered) coordinates.
"""

import math
import logging
from typing import Optional

from common.local_map.local_map_data import Point3D, Pose
from map_node.map_common.base import Position
from .config_types import TransformResult

logger = logging.getLogger(__name__)


class CoordinateTransformer:
    """
    Coordinate transformer for converting between global and local coordinates.

    This class handles transformations between global coordinates (WGS84 or local
    map coordinates) and ego-centered local coordinates. The ego-centered
    coordinate system has its origin at the ego vehicle's position, with the
    x-axis pointing in the direction of the ego vehicle's heading.
    """

    def __init__(self, ego_pose: Pose, precision_threshold: float = 0.01):
        """
        Initialize the coordinate transformer.

        Args:
            ego_pose: The ego vehicle's pose (origin of local coordinate system)
            precision_threshold: Precision threshold in meters for coordinate comparisons
        """
        self.ego_pose = ego_pose
        self.precision_threshold = precision_threshold

    def update_ego_pose(self, ego_pose: Pose) -> None:
        """
        Update the ego vehicle pose.

        Args:
            ego_pose: New ego vehicle pose
        """
        self.ego_pose = ego_pose

    def global_to_local(self, global_position: Position) -> TransformResult:
        """
        Convert global coordinates to local (ego-centered) coordinates.

        The transformation involves:
        1. Translating the global position relative to ego position
        2. Rotating the translated position by negative ego heading

        Args:
            global_position: Global position (latitude, longitude, altitude)
                             Note: For local map coordinates, use latitude as x,
                                   longitude as y

        Returns:
            TransformResult with the local point or error information
        """
        try:
            # Calculate relative position
            # For local map coordinates: latitude is x, longitude is y
            dx = global_position.latitude - self.ego_pose.position.x
            dy = global_position.longitude - self.ego_pose.position.y
            dz = (global_position.altitude - self.ego_pose.position.z
                  if global_position.altitude is not None else 0.0)

            # Apply rotation transformation
            # Rotate by negative ego heading to align with ego coordinate system
            cos_heading = math.cos(-self.ego_pose.heading)
            sin_heading = math.sin(-self.ego_pose.heading)

            local_x = dx * cos_heading - dy * sin_heading
            local_y = dx * sin_heading + dy * cos_heading
            local_z = dz

            local_point = Point3D(x=local_x, y=local_y, z=local_z)

            return TransformResult(success=True, point=local_point)

        except Exception as e:
            logger.error(f"Error converting global to local coordinates: {e}")
            return TransformResult(
                success=False,
                error=f"Coordinate transformation failed: {str(e)}"
            )

    def local_to_global(self, local_point: Point3D) -> TransformResult:
        """
        Convert local (ego-centered) coordinates to global coordinates.

        The transformation involves:
        1. Rotating the local position by ego heading
        2. Translating the rotated position by ego position

        Args:
            local_point: Local point (x, y, z) in ego-centered coordinates

        Returns:
            TransformResult with the global position or error information
        """
        try:
            # Apply rotation transformation
            # Rotate by ego heading to align with global coordinate system
            cos_heading = math.cos(self.ego_pose.heading)
            sin_heading = math.sin(self.ego_pose.heading)

            rotated_x = local_point.x * cos_heading - local_point.y * sin_heading
            rotated_y = local_point.x * sin_heading + local_point.y * cos_heading
            rotated_z = local_point.z

            # Translate by ego position
            global_latitude = rotated_x + self.ego_pose.position.x
            global_longitude = rotated_y + self.ego_pose.position.y
            global_altitude = rotated_z + self.ego_pose.position.z

            global_position = Position(
                latitude=global_latitude,
                longitude=global_longitude,
                altitude=global_altitude
            )

            return TransformResult(success=True, point=global_position)

        except Exception as e:
            logger.error(f"Error converting local to global coordinates: {e}")
            return TransformResult(
                success=False,
                error=f"Coordinate transformation failed: {str(e)}"
            )

    def transform_point_list(
        self,
        points: list,
        to_local: bool = True
    ) -> list:
        """
        Transform a list of points.

        Args:
            points: List of Point3D or Position objects
            to_local: If True, transform to local; otherwise transform to global

        Returns:
            List of transformed points
        """
        transformed = []
        for point in points:
            if to_local:
                result = self.global_to_local(point)
                if result.success:
                    transformed.append(result.point)
            else:
                result = self.local_to_global(point)
                if result.success:
                    transformed.append(result.point)
        return transformed

    def calculate_distance(self, pos1: Point3D, pos2: Point3D) -> float:
        """
        Calculate Euclidean distance between two points.

        Args:
            pos1: First point
            pos2: Second point

        Returns:
            Distance in meters
        """
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        dz = pos1.z - pos2.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def is_within_range(
        self,
        position: Point3D,
        range_meters: float
    ) -> bool:
        """
        Check if a position is within range of ego vehicle.

        Args:
            position: Position to check (in local coordinates)
            range_meters: Range in meters

        Returns:
            True if position is within range
        """
        distance = self.calculate_distance(
            Point3D(x=0.0, y=0.0, z=0.0),  # Ego position at origin
            position
        )
        return distance <= range_meters

    def generate_cache_key(
        self,
        ego_pose: Pose,
        position_tolerance: float = 5.0
    ) -> str:
        """
        Generate a cache key based on ego pose.

        The cache key is generated by quantizing the ego position and heading
        to the specified tolerance.

        Args:
            ego_pose: Ego vehicle pose
            position_tolerance: Position tolerance in meters for quantization

        Returns:
            Cache key string
        """
        # Quantize position
        x_key = int(ego_pose.position.x / position_tolerance)
        y_key = int(ego_pose.position.y / position_tolerance)

        # Quantize heading (5 degrees)
        heading_deg = math.degrees(ego_pose.heading) % 360
        heading_key = int(heading_deg / 5)

        return f"pos_{x_key}_{y_key}_head_{heading_key}"
