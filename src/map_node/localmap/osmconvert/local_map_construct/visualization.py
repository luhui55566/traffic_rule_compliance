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

        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

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

        # Set plot properties
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel('X (meters)', fontsize=12)
        self.ax.set_ylabel('Y (meters)', fontsize=12)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')

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
        """Plot lane boundaries from local map."""
        left_boundaries = []
        right_boundaries = []

        logger.debug(f"Processing {len(local_map.lanes)} lanes for boundary plotting")
        logger.debug(f"Total boundary segments in local_map: {len(local_map.boundary_segments)}")

        for lane in local_map.lanes:
            # Get boundary segments
            logger.debug(f"Lane {lane.lane_id}: left_indices={lane.left_boundary_segment_indices}, right_indices={lane.right_boundary_segment_indices}")
            for idx in lane.left_boundary_segment_indices:
                if idx < len(local_map.boundary_segments):
                    segment = local_map.boundary_segments[idx]
                    points = [(p.x, p.y) for p in segment.boundary_points]
                    if len(points) > 1:
                        left_boundaries.append(points)
                else:
                    logger.debug(f"  Left boundary index {idx} out of range (max={len(local_map.boundary_segments)-1})")

            for idx in lane.right_boundary_segment_indices:
                if idx < len(local_map.boundary_segments):
                    segment = local_map.boundary_segments[idx]
                    points = [(p.x, p.y) for p in segment.boundary_points]
                    if len(points) > 1:
                        right_boundaries.append(points)
                else:
                    logger.debug(f"  Right boundary index {idx} out of range (max={len(local_map.boundary_segments)-1})")

        logger.debug(f"Plotting lanes: {len(left_boundaries)} left boundaries, {len(right_boundaries)} right boundaries")

        # Log boundary point ranges for debugging
        if left_boundaries:
            left_x = [p[0] for boundary in left_boundaries for p in boundary]
            left_y = [p[1] for boundary in left_boundaries for p in boundary]
            logger.debug(f"Left boundary range: x=[{min(left_x):.1f}, {max(left_x):.1f}], y=[{min(left_y):.1f}, {max(left_y):.1f}]")
        if right_boundaries:
            right_x = [p[0] for boundary in right_boundaries for p in boundary]
            right_y = [p[1] for boundary in right_boundaries for p in boundary]
            logger.debug(f"Right boundary range: x=[{min(right_x):.1f}, {max(right_x):.1f}], y=[{min(right_y):.1f}, {max(right_y):.1f}]")

        # Plot left boundaries (blue)
        if left_boundaries:
            lc_left = LineCollection(left_boundaries, colors='blue',
                                      linewidths=2.5, alpha=0.9, label='Left Boundary')
            self.ax.add_collection(lc_left)
            logger.debug(f"Plotted {len(left_boundaries)} left boundaries")
        else:
            logger.debug("No left boundaries to plot")

        # Plot right boundaries (red)
        if right_boundaries:
            lc_right = LineCollection(right_boundaries, colors='red',
                                       linewidths=2.5, alpha=0.9, label='Right Boundary')
            self.ax.add_collection(lc_right)
            logger.debug(f"Plotted {len(right_boundaries)} right boundaries")
        else:
            logger.debug("No right boundaries to plot")

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

        # Plot centerlines (green dashed)
        if centerlines:
            lc_center = LineCollection(centerlines, colors='green',
                                      linewidths=2.0, alpha=0.8,
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
                       fontsize=8, alpha=0.7)

    def _plot_ego_position(self, local_map: LocalMap) -> None:
        """Plot ego vehicle position."""
        if local_map.metadata:
            ego_x = local_map.metadata.ego_vehicle_x
            ego_y = local_map.metadata.ego_vehicle_y

            # Plot ego position (green star)
            self.ax.scatter(ego_x, ego_y, c='lime', s=200,
                          marker='*', edgecolors='black', linewidths=2,
                          label='Ego Vehicle', zorder=10)

            # Plot ego heading arrow
            heading = local_map.metadata.ego_vehicle_heading
            arrow_length = 10.0
            dx = arrow_length * (heading ** 0)
            dy = arrow_length * (heading ** 0)
            # Actually use proper trigonometry
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
                       f"P{i+1}", fontsize=8, alpha=0.7)

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
            handles.append(patches.Patch(color='blue', label='Left Boundary'))
            handles.append(patches.Patch(color='red', label='Right Boundary'))
        if show_centerlines:
            handles.append(Line2D([0], [0], color='green', linestyle='--', label='Centerline'))
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
            self.ax.legend(handles=handles, loc='upper right', fontsize=9)

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
