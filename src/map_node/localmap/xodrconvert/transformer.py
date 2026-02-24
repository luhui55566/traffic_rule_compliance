"""
Coordinate transformer for XODR to LocalMap conversion.

This module handles coordinate transformations between XODR's Frenet (s, t, h)
coordinates and LocalMap's Cartesian (x, y, z) coordinates.
"""

import logging
import math
from dataclasses import dataclass
from typing import Optional, List

from common.local_map.local_map_data import Point3D, Pose

logger = logging.getLogger(__name__)


@dataclass
class TransformResult:
    """Result of coordinate transformation."""
    success: bool
    point: Optional[Point3D] = None
    error: Optional[str] = None


class XODRCoordinateTransformer:
    """
    Coordinate transformer for XODR to LocalMap conversion.
    
    Handles transformations between:
    - XODR Frenet coordinates (s, t, h) along road reference line
    - LocalMap Cartesian coordinates (x, y, z) in local ego frame
    """
    
    def __init__(self, ego_pose: Pose = None):
        """
        Initialize coordinate transformer.
        
        Args:
            ego_pose: Ego vehicle pose for local coordinate transformation
        """
        self.ego_pose = ego_pose or Pose(
            position=Point3D(x=0.0, y=0.0, z=0.0),
            heading=0.0
        )
        
        # Cache for transformation matrices
        self._cos_heading = math.cos(self.ego_pose.heading)
        self._sin_heading = math.sin(self.ego_pose.heading)
    
    def update_ego_pose(self, ego_pose: Pose):
        """
        Update ego pose for coordinate transformation.
        
        Args:
            ego_pose: New ego vehicle pose
        """
        self.ego_pose = ego_pose
        self._cos_heading = math.cos(ego_pose.heading)
        self._sin_heading = math.sin(ego_pose.heading)
        logger.debug(f"Updated ego pose: x={ego_pose.position.x:.2f}, "
                    f"y={ego_pose.position.y:.2f}, heading={ego_pose.heading:.2f}")
    
    def global_to_local(self, global_point: Point3D) -> TransformResult:
        """
        Transform global coordinates to local ego coordinates.
        
        Args:
            global_point: Point in global XODR coordinates
            
        Returns:
            TransformResult with local coordinates
        """
        try:
            # Translate to ego position
            dx = global_point.x - self.ego_pose.position.x
            dy = global_point.y - self.ego_pose.position.y
            dz = global_point.z - self.ego_pose.position.z
            
            # Rotate by negative ego heading
            local_x = dx * self._cos_heading + dy * self._sin_heading
            local_y = -dx * self._sin_heading + dy * self._cos_heading
            local_z = dz  # Z is not affected by rotation
            
            return TransformResult(
                success=True,
                point=Point3D(x=local_x, y=local_y, z=local_z)
            )
        except Exception as e:
            logger.error(f"Failed to transform global to local: {e}")
            return TransformResult(
                success=False,
                error=str(e)
            )
    
    def local_to_global(self, local_point: Point3D) -> TransformResult:
        """
        Transform local ego coordinates to global coordinates.
        
        Args:
            local_point: Point in local ego coordinates
            
        Returns:
            TransformResult with global coordinates
        """
        try:
            # Rotate by ego heading
            rotated_x = local_point.x * self._cos_heading - local_point.y * self._sin_heading
            rotated_y = local_point.x * self._sin_heading + local_point.y * self._cos_heading
            
            # Translate to ego position
            global_x = rotated_x + self.ego_pose.position.x
            global_y = rotated_y + self.ego_pose.position.y
            global_z = local_point.z + self.ego_pose.position.z
            
            return TransformResult(
                success=True,
                point=Point3D(x=global_x, y=global_y, z=global_z)
            )
        except Exception as e:
            logger.error(f"Failed to transform local to global: {e}")
            return TransformResult(
                success=False,
                error=str(e)
            )
    
    def transform_points_list(
        self,
        points: List[Point3D],
        to_local: bool = True
    ) -> List[TransformResult]:
        """
        Transform a list of points.
        
        Args:
            points: List of points to transform
            to_local: If True, transform to local; otherwise to global
            
        Returns:
            List of TransformResults
        """
        results = []
        for point in points:
            if to_local:
                result = self.global_to_local(point)
            else:
                result = self.local_to_global(point)
            results.append(result)
        return results
    
    def is_point_in_range(
        self,
        point: Point3D,
        range_x: float = 200.0,
        range_y: float = 200.0
    ) -> bool:
        """
        Check if a point is within the specified range from ego.
        
        Args:
            point: Point to check
            range_x: X-axis range in meters
            range_y: Y-axis range in meters
            
        Returns:
            True if point is within range
        """
        # Transform to local coordinates
        result = self.global_to_local(point)
        if not result.success:
            return False
        
        local_point = result.point
        return (abs(local_point.x) <= range_x and 
                abs(local_point.y) <= range_y)
    
    def filter_points_in_range(
        self,
        points: List[Point3D],
        range_x: float = 200.0,
        range_y: float = 200.0
    ) -> List[Point3D]:
        """
        Filter points to keep only those within range.
        
        Args:
            points: List of points to filter
            range_x: X-axis range in meters
            range_y: Y-axis range in meters
            
        Returns:
            List of points within range
        """
        filtered = []
        for point in points:
            if self.is_point_in_range(point, range_x, range_y):
                filtered.append(point)
        return filtered
    
    @staticmethod
    def calculate_heading(p1: Point3D, p2: Point3D) -> float:
        """
        Calculate heading from point p1 to point p2.
        
        Args:
            p1: Start point
            p2: End point
            
        Returns:
            Heading angle in radians
        """
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return math.atan2(dy, dx)
    
    @staticmethod
    def calculate_distance(p1: Point3D, p2: Point3D) -> float:
        """
        Calculate Euclidean distance between two points.
        
        Args:
            p1: First point
            p2: Second point
            
        Returns:
            Distance in meters
        """
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        dz = p2.z - p1.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
