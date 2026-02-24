"""
Visualization utilities for LocalMap data.

This module provides visualization functionality for LocalMap data structures.
"""

import logging
from typing import Optional, List, Tuple
from pathlib import Path

# Set matplotlib to use non-interactive backend before importing
import matplotlib
matplotlib.use('Agg')

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.collections import LineCollection
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    patches = None
    LineCollection = None

from common.local_map.local_map_data import (
    LocalMap, Lane, LaneBoundarySegment,
    TrafficLight, TrafficSign, Point3D
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalMapVisualizer:
    """Visualizer for LocalMap data."""

    def __init__(self, figsize: Tuple[float, float] = (12, 10)):
        """
        Initialize local map visualizer.

        Args:
            figsize: Figure size (width, height) in inches
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "Matplotlib is not installed. Please install it first:\n"
                "  pip install matplotlib"
            )

        self.figsize = figsize
        self.fig = None
        self.ax = None

    def visualize_local_map(
        self,
        local_map: LocalMap,
        title: str = "Local Map Visualization",
        show_lanes: bool = True,
        show_centerlines: bool = True,
        show_traffic_elements: bool = True,
        show_ego_position: bool = True,
        ego_points: Optional[List[Point3D]] = None,
        save_path: Optional[str] = None,
        dpi: int = 100
    ) -> None:
        """
        Visualize a LocalMap.

        Args:
            local_map: LocalMap object to visualize
            title: Plot title
            show_lanes: Whether to show lane boundaries
            show_centerlines: Whether to show lane centerlines
            show_traffic_elements: Whether to show traffic lights and signs
            show_ego_position: Whether to show ego vehicle position
            ego_points: List of ego test points to mark
            save_path: Path to save figure (optional)
            dpi: DPI for saved figure
        """
        logger.info(f"Visualizing local map with {len(local_map.lanes)} lanes")

        # Create figure and axis with black background
        self.fig, self.ax = plt.subplots(figsize=self.figsize, facecolor='black')
        self.ax.set_facecolor('black')

        # Plot lanes (includes left/right boundaries)
        if show_lanes:
            self._plot_lanes(local_map)

        # Plot centerlines
        if show_centerlines:
            self._plot_centerlines(local_map)

        # Plot traffic elements
        if show_traffic_elements:
            self._plot_traffic_elements(local_map)

        # Plot ego position
        if show_ego_position and local_map.metadata:
            self._plot_ego_position(local_map)

        # Plot ego test points
        if ego_points:
            self._plot_ego_points(ego_points)

        # Set plot properties with white text for black background
        self.ax.set_title(title, fontsize=14, fontweight='bold', color='white')
        self.ax.set_xlabel('X (meters)', fontsize=12, color='white')
        self.ax.set_ylabel('Y (meters)', fontsize=12, color='white')
        self.ax.grid(True, alpha=0.3, color='gray')
        self.ax.set_aspect('equal')
        # Set tick colors to white
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')

        # Auto-scale axis to show all content
        self.auto_scale_axis(local_map)

        # Add legend
        self._add_legend(show_lanes, show_centerlines,
                        show_traffic_elements, show_ego_position, ego_points)

        # Adjust layout
        plt.tight_layout()

        # Save or show
        if save_path:
            self.fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
            logger.info(f"Figure saved to: {save_path}")

        # plt.show()  # Disabled for WSL/headless environments

    def _plot_lanes(self, local_map: LocalMap) -> None:
        """Plot lane boundaries from local map with actual colors and line types."""
        logger.debug(f"Processing {len(local_map.lanes)} lanes for boundary plotting")
        logger.debug(f"Total boundary segments in local_map: {len(local_map.boundary_segments)}")

        # Color mapping for BoundaryColor enum
        color_map = {
            0: 'gray',      # UNKNOWN
            1: 'white',     # WHITE
            2: 'yellow',    # YELLOW
            3: 'blue',      # BLUE
            4: 'red',       # RED
        }

        # Line style mapping for BoundaryLineShape enum
        linestyle_map = {
            0: '-',         # UNKNOWN
            1: '-',         # SOLID
            2: '--',        # DASHED
            3: '-',         # DOUBLE_SOLID (draw as solid for now)
            4: '--',        # DOUBLE_DASHED (draw as dashed for now)
            5: '-.',        # SOLID_DASHED
            6: ':',         # DOTTED
            7: '-.',        # LEFT_SOLID_RIGHT_DASHED
            8: '-.',        # LEFT_DASHED_RIGHT_SOLID
        }

        # Collect all boundary sub-segments with their properties
        all_sub_segments = []
        all_colors = []
        all_linestyles = []
        all_widths = []

        # Process all boundary segments
        for i, segment in enumerate(local_map.boundary_segments):
            segment.segment_id
            points = [(p.x, p.y) for p in segment.boundary_points]
            if len(points) <= 1:
                logger.debug(f"Boundary segment {i}: skipped (only {len(points)} points)")
                continue

            # Check if this segment has segmented boundary data
            has_segmented_data = (
                segment.boundary_color_segments and
                segment.boundary_line_shape_segments and
                segment.boundary_thickness_segments
            )

            if has_segmented_data:
                # Use segmented boundary data
                # Each segment array contains (Point3D, property_value) tuples
                # We need to split the boundary_points into sub-segments based on these
                
                # Get the segment start points and their properties
                color_segments = segment.boundary_color_segments
                line_shape_segments = segment.boundary_line_shape_segments
                thickness_segments = segment.boundary_thickness_segments
                
                # Sort segments by their start point (approximate by index in boundary_points)
                # Since we don't have exact s-to-point mapping, we'll use a simplified approach
                
                # Find the index in boundary_points for each segment's start point
                # color_segments contains (Point3D, property_value) tuples
                # where Point3D is the starting coordinate of each segment
                
                # Helper function to find index in boundary_points that matches a Point3D
                def find_point_index(target_point: Point3D, tolerance: float = 0.001) -> int:
                    """Find the index in boundary_points that matches target_point within tolerance."""
                    for idx, p in enumerate(segment.boundary_points):
                        if (abs(p.x - target_point.x) < tolerance and
                            abs(p.y - target_point.y) < tolerance):
                            return idx
                    return -1
                
                # Build list of (segment_idx, start_index) pairs
                segment_start_indices = []  # [(original_seg_idx, start_index), ...]
                for seg_idx, (start_point, _) in enumerate(color_segments):
                    start_idx = find_point_index(start_point)
                    if start_idx >= 0:
                        segment_start_indices.append((seg_idx, start_idx))
                
                # Sort by start_index
                segment_start_indices.sort(key=lambda x: x[1])
                
                # Build point to segment mapping
                # Each point belongs to the segment whose start_index is <= point_index
                # and is the largest such start_index
                point_to_segment = {}  # {point_idx: segment_idx}
                current_seg_idx = None
                current_seg_start_idx = -1
                
                for point_idx in range(len(points)):
                    # Check if this point matches any segment start
                    for seg_idx, start_idx in segment_start_indices:
                        if point_idx == start_idx:
                            current_seg_idx = seg_idx
                            current_seg_start_idx = start_idx
                            break
                    
                    # Assign segment to this point
                    if current_seg_idx is not None:
                        point_to_segment[point_idx] = current_seg_idx
                
                # Group points by segment
                segment_points = {}  # {seg_idx: [points]}
                for point_idx, point in enumerate(points):
                    seg_idx = point_to_segment.get(point_idx)
                    if seg_idx is not None:
                        if seg_idx not in segment_points:
                            segment_points[seg_idx] = []
                        segment_points[seg_idx].append(point)
                
                # Process each segment
                if segment_points:
                    for seg_idx, seg_points in segment_points.items():
                        if len(seg_points) < 2:
                            continue  # Need at least 2 points to draw a line
                        
                        sub_segment_points = seg_points
                        
                        # Get properties for this sub-segment
                        color_value = color_segments[seg_idx][1] if seg_idx < len(color_segments) else color_segments[0][1]
                        line_shape_value = line_shape_segments[seg_idx][1] if seg_idx < len(line_shape_segments) else line_shape_segments[0][1]
                        thickness_value = thickness_segments[seg_idx][1] if seg_idx < len(thickness_segments) else thickness_segments[0][1]
                        
                        # Map enum values to matplotlib values
                        color = color_map.get(color_value.value if hasattr(color_value, 'value') else 0, 'gray')
                        linestyle = linestyle_map.get(line_shape_value.value if hasattr(line_shape_value, 'value') else 0, '-')
                        width = max(0.5, thickness_value * 3)
                        
                        all_sub_segments.append(sub_segment_points)
                        all_colors.append(color)
                        all_linestyles.append(linestyle)
                        all_widths.append(width)
                        
                        logger.debug(f"Boundary segment {i}, sub-segment {seg_idx}: "
                                   f"color={color}, style={linestyle}, width={width:.1f}, "
                                   f"points={len(sub_segment_points)}")
                else:
                    # No segments found, use default values
                    all_sub_segments.append(points)
                    all_colors.append('gray')
                    all_linestyles.append('-')
                    all_widths.append(1.0)
                    logger.debug(f"Boundary segment {i}: using default values (no segments)")
            else:
                # No segmented data, skip this segment or use default values
                logger.debug(f"Boundary segment {i}: no segmented data, skipping")
                continue

        logger.debug(f"Total boundary sub-segments to plot: {len(all_sub_segments)}")

        # Plot boundary sub-segments with their actual colors and line styles
        if all_sub_segments:
            # Create LineCollection with individual colors and linestyles
            lc = LineCollection(all_sub_segments,
                              colors=all_colors,
                              linewidths=all_widths,
                              linestyles=all_linestyles,
                              alpha=0.9,
                              label='Lane Boundary')
            self.ax.add_collection(lc)
            logger.debug(f"Plotted {len(all_sub_segments)} boundary sub-segments")
        else:
            logger.debug("No boundary sub-segments to plot")

    def _plot_boundary_segments(self, local_map: LocalMap) -> None:
        """Plot boundary segments from local map."""
        segments = []
        colors = []

        logger.debug(f"Processing {len(local_map.boundary_segments)} boundary segments")

        for i, segment in enumerate(local_map.boundary_segments):
            points = [(p.x, p.y) for p in segment.boundary_points]
            if len(points) > 1:
                segments.append(points)
                # Color based on boundary type
                color_map = {
                    1: 'black',   # LINE
                    2: 'gray',    # CURB
                    3: 'orange',  # GUARDRAIL
                    4: 'purple',  # WALL
                    5: 'cyan',    # VIRTUAL
                }
                colors.append(color_map.get(segment.boundary_type.value, 'black'))
                logger.debug(f"Boundary segment {i}: {len(points)} points, type={segment.boundary_type.name}")
            else:
                logger.debug(f"Boundary segment {i}: skipped (only {len(points)} points)")

        logger.debug(f"Total boundary segments to plot: {len(segments)}")

        if segments:
            lc = LineCollection(segments, colors=colors, linewidths=1.0, alpha=0.5, label='Boundary Segments')
            self.ax.add_collection(lc)
            logger.debug(f"Plotted {len(segments)} boundary segments")
        else:
            logger.debug("No boundary segments to plot")

    def _plot_centerlines(self, local_map: LocalMap) -> None:
        """Plot lane centerlines from local map."""
        centerlines = []

        for lane in local_map.lanes:
            if lane.centerline_points:
                points = [(p.x, p.y) for p in lane.centerline_points]
                if len(points) > 1:
                    centerlines.append(points)

        logger.debug(f"Found {len(centerlines)} lanes with centerlines (out of {len(local_map.lanes)} total lanes)")

        # Plot centerlines (lime dashed, thinner)
        if centerlines:
            lc_center = LineCollection(centerlines, colors='lime',
                                      linewidths=1.0, alpha=0.8,
                                      linestyles='--', label='Centerline')
            self.ax.add_collection(lc_center)
            logger.debug(f"Plotted {len(centerlines)} centerlines")
        else:
            logger.debug("No centerlines to plot")

    def _plot_traffic_elements(self, local_map: LocalMap) -> None:
        """Plot traffic lights and signs from local map."""
        # Plot traffic lights
        for light in local_map.traffic_lights:
            self.ax.scatter(light.position.x, light.position.y,
                          c='yellow', s=100, marker='o',
                          edgecolors='black', linewidths=1.5,
                          label='Traffic Light' if light == local_map.traffic_lights[0] else None)

        # Plot traffic signs
        for sign in local_map.traffic_signs:
            self.ax.scatter(sign.position.x, sign.position.y,
                          c='orange', s=80, marker='s',
                          edgecolors='black', linewidths=1.5,
                          label='Traffic Sign' if sign == local_map.traffic_signs[0] else None)

            # Add sign type as text
            self.ax.text(sign.position.x + 2, sign.position.y + 2,
                       f"{sign.sign_type.name}",
                       fontsize=8, alpha=0.7, color='white')

    def _plot_ego_position(self, local_map: LocalMap) -> None:
        """Plot ego vehicle position."""
        if local_map.metadata:
            # In local ego coordinate system, ego vehicle is always at (0, 0)
            ego_x = 0.0
            ego_y = 0.0

            # Plot ego position (green star)
            self.ax.scatter(ego_x, ego_y, c='lime', s=200,
                          marker='*', edgecolors='black', linewidths=2,
                          label='Ego Vehicle', zorder=10)

            # Plot ego heading arrow
            heading = local_map.metadata.ego_vehicle_heading
            arrow_length = 10.0
            import math
            dx = arrow_length * math.cos(heading)
            dy = arrow_length * math.sin(heading)

            self.ax.arrow(ego_x, ego_y, dx, dy,
                        head_width=3, head_length=3,
                        fc='lime', ec='black', alpha=0.7, zorder=9)

    def _plot_ego_points(self, ego_points: List[Point3D]) -> None:
        """Plot ego test points."""
        if not ego_points:
            return

        for i, point in enumerate(ego_points):
            self.ax.scatter(point.x, point.y, c='magenta', s=50,
                          marker='x', edgecolors='white', linewidths=1,
                          label='Test Point' if i == 0 else None)

            # Add point number
            self.ax.text(point.x + 1, point.y + 1,
                       f"P{i+1}", fontsize=8, alpha=0.7, color='white')

    def _add_legend(
        self,
        show_lanes: bool,
        show_centerlines: bool,
        show_traffic_elements: bool,
        show_ego_position: bool,
        ego_points: Optional[List[Point3D]]
    ) -> None:
        """Add legend to plot."""
        from matplotlib.lines import Line2D
        handles = []
        labels = []

        if show_lanes:
            # Add legend entries for different boundary colors and line types
            handles.append(Line2D([0], [0], color='white', linestyle='-', linewidth=1, label='Solid White'))
            handles.append(Line2D([0], [0], color='yellow', linestyle='-', linewidth=1, label='Solid Yellow'))
            handles.append(Line2D([0], [0], color='white', linestyle='--', linewidth=1, label='Dashed White'))
            handles.append(Line2D([0], [0], color='gray', linestyle='-', linewidth=1, label='Unknown Boundary'))
        if show_centerlines:
            handles.append(Line2D([0], [0], color='lime', linestyle='--', linewidth=1, label='Centerline'))
        if show_traffic_elements:
            handles.append(Line2D([0], [0], marker='o', color='yellow', linestyle='None',
                               markersize=8, label='Traffic Light'))
            handles.append(Line2D([0], [0], marker='s', color='orange', linestyle='None',
                               markersize=8, label='Traffic Sign'))
        if show_ego_position:
            handles.append(Line2D([0], [0], marker='*', color='lime', linestyle='None',
                               markersize=12, label='Ego Vehicle'))
        if ego_points:
            handles.append(Line2D([0], [0], marker='x', color='magenta', linestyle='None',
                               markersize=8, label='Test Point'))

        if handles:
            self.ax.legend(handles=handles, loc='upper right', fontsize=9, labelcolor='white')

    def auto_scale_axis(self, local_map: LocalMap) -> None:
        """Auto-scale axis based on local map content."""
        all_points = []

        # Collect all points from lanes
        for lane in local_map.lanes:
            for point in lane.centerline_points:
                all_points.append((point.x, point.y))

        # Collect all points from boundary segments
        for segment in local_map.boundary_segments:
            for point in segment.boundary_points:
                all_points.append((point.x, point.y))

        # Collect traffic element positions
        for light in local_map.traffic_lights:
            all_points.append((light.position.x, light.position.y))
        for sign in local_map.traffic_signs:
            all_points.append((sign.position.x, sign.position.y))

        # Add ego position
        if local_map.metadata:
            all_points.append((local_map.metadata.ego_vehicle_x,
                           local_map.metadata.ego_vehicle_y))

        if all_points:
            xs, ys = zip(*all_points)
            self.ax.set_xlim(min(xs) - 10, max(xs) + 10)
            self.ax.set_ylim(min(ys) - 10, max(ys) + 10)

