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

    def __init__(self, figsize: Tuple[float, float] = (20, 20)):
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
        show_road_ids: bool = True,
        show_lane_ids: bool = True,
        ego_points: Optional[List[Point3D]] = None,
        trajectory_points: Optional[List[Point3D]] = None,
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
            show_road_ids: Whether to show Road ID labels on each lane
            show_lane_ids: Whether to show Lane ID labels on each lane (smaller font)
            ego_points: List of ego test points to mark
            trajectory_points: List of trajectory points to plot as a connected path
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

        # Plot trajectory
        if trajectory_points:
            self._plot_trajectory(trajectory_points)

        # Plot Road ID labels
        if show_road_ids:
            self._plot_road_ids(local_map)
        
        # Plot Lane ID labels
        if show_lane_ids:
            self._plot_lane_ids(local_map)

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
                        show_traffic_elements, show_ego_position, ego_points, trajectory_points)

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
        
        # Log boundary segment info for road266
        road266_lane_ids = set()
        for lane in local_map.lanes:
            if lane.road_id == 266:
                road266_lane_ids.add(lane.lane_id)
                # Get boundary segment indices
                all_indices = list(lane.left_boundary_segment_indices) + list(lane.right_boundary_segment_indices)
                for idx in all_indices:
                    if idx < len(local_map.boundary_segments):
                        seg = local_map.boundary_segments[idx]
                        if seg.boundary_points:
                            max_y = max(p.y for p in seg.boundary_points)
                            min_y = min(p.y for p in seg.boundary_points)
                            logger.info(f"Road266 boundary seg {idx}: {len(seg.boundary_points)} pts, Y=[{min_y:.2f}, {max_y:.2f}]")

        # Color mapping for BoundaryColor enum
        # XODR standard colors: white, yellow, blue, red
        color_map = {
            0: 'cyan',      # UNKNOWN - 青色（用于虚拟边界，在黑色背景上明显）
            1: 'white',     # WHITE - 标准白色车道线
            2: 'yellow',    # YELLOW - 标准黄色车道线（通常用于分隔对向交通）
            3: 'blue',      # BLUE - 特殊用途（如残疾人停车位）
            4: 'red',       # RED - 特殊用途（如消防通道）
        }

        # Line style mapping for BoundaryLineShape enum
        # Matplotlib linestyles: '-', '--', '-.', ':', 'None', ' ', ''
        linestyle_map = {
            0: (0, (2, 2, 2, 2)),  # UNKNOWN - 点划线（用于虚拟边界，独特线型）
            1: '-',         # SOLID - 单实线━━━━━━━
            2: '--',        # DASHED - 单虚线 ┅┅┅┅┅┅┅
            3: '-',         # DOUBLE_SOLID - 双实线 ━═━═━═ (用粗实线表示)
            4: '--',        # DOUBLE_DASHED - 双虚线 ┅═┅═┅═ (用粗虚线表示)
            5: '-.',        # SOLID_DASHED - 实虚组合 ━┅┅┅┅
            6: ':',         # DOTTED - 点线 ●●●●●● (botts_dots)
            7: (0, (5, 1, 1, 1)),  # LEFT_SOLID_RIGHT_DASHED - 左实右虚 (dash-dot pattern)
            8: (0, (1, 1, 5, 1)),  # LEFT_DASHED_RIGHT_SOLID - 左虚右实 (dot-dash pattern)
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

            # Check if this segment has per-point boundary data
            # Each attribute list corresponds 1:1 with boundary_points
            has_per_point_data = (
                segment.boundary_colors and
                segment.boundary_line_shapes and
                segment.boundary_thicknesses and
                len(segment.boundary_colors) == len(segment.boundary_points)
            )

            if has_per_point_data:
                # Use per-point boundary data - group consecutive points with same properties
                # into sub-segments for efficient rendering
                
                # Build sub-segments by grouping consecutive points with same properties
                sub_segments = []  # [(start_idx, end_idx, color, linestyle, width), ...]
                
                if len(points) >= 2:
                    current_start = 0
                    current_color = segment.boundary_colors[0] if segment.boundary_colors else None
                    current_shape = segment.boundary_line_shapes[0] if segment.boundary_line_shapes else None
                    current_thickness = segment.boundary_thicknesses[0] if segment.boundary_thicknesses else 0.1
                    
                    for idx in range(1, len(points)):
                        # Check if properties changed at this point
                        color_changed = (idx >= len(segment.boundary_colors) or
                                        segment.boundary_colors[idx] != current_color)
                        shape_changed = (idx >= len(segment.boundary_line_shapes) or
                                        segment.boundary_line_shapes[idx] != current_shape)
                        thickness_changed = (idx >= len(segment.boundary_thicknesses) or
                                            abs(segment.boundary_thicknesses[idx] - current_thickness) > 0.01)
                        
                        if color_changed or shape_changed or thickness_changed or idx == len(points) - 1:
                            # End current sub-segment
                            end_idx = idx if idx == len(points) - 1 else idx
                            if end_idx > current_start:
                                # Map enum values to matplotlib values
                                color = color_map.get(
                                    current_color.value if current_color and hasattr(current_color, 'value') else 0,
                                    'gray'
                                )
                                linestyle = linestyle_map.get(
                                    current_shape.value if current_shape and hasattr(current_shape, 'value') else 0,
                                    '-'
                                )
                                width = max(0.5, current_thickness * 3)
                                
                                sub_segments.append((current_start, end_idx, color, linestyle, width))
                            
                            # Start new sub-segment
                            if idx < len(points) - 1:
                                current_start = idx
                                current_color = segment.boundary_colors[idx] if idx < len(segment.boundary_colors) else current_color
                                current_shape = segment.boundary_line_shapes[idx] if idx < len(segment.boundary_line_shapes) else current_shape
                                current_thickness = segment.boundary_thicknesses[idx] if idx < len(segment.boundary_thicknesses) else current_thickness
                    
                    # If no sub-segments were created (all points have same properties), create one
                    if not sub_segments and len(points) >= 2:
                        color = color_map.get(
                            current_color.value if current_color and hasattr(current_color, 'value') else 0,
                            'gray'
                        )
                        linestyle = linestyle_map.get(
                            current_shape.value if current_shape and hasattr(current_shape, 'value') else 0,
                            '-'
                        )
                        width = max(0.5, current_thickness * 3)
                        sub_segments.append((0, len(points) - 1, color, linestyle, width))
                
                # Add sub-segments to collection
                for start_idx, end_idx, color, linestyle, width in sub_segments:
                    sub_points = points[start_idx:end_idx + 1]
                    if len(sub_points) >= 2:
                        all_sub_segments.append(sub_points)
                        all_colors.append(color)
                        all_linestyles.append(linestyle)
                        all_widths.append(width)
                        logger.debug(f"Boundary segment {i}: sub-segment [{start_idx}:{end_idx}] "
                                   f"color={color}, style={linestyle}, width={width:.1f}")
            else:
                # No per-point data, use default virtual boundary style
                if len(points) >= 2:
                    all_sub_segments.append(points)
                    all_colors.append('cyan')  # Cyan for virtual boundaries
                    all_linestyles.append((0, (2, 2, 2, 2)))  # Dash-dot pattern for virtual
                    all_widths.append(1.0)
                    logger.debug(f"Boundary segment {i}: using virtual boundary defaults (cyan, dash-dot)")
                else:
                    logger.debug(f"Boundary segment {i}: skipped (only {len(points)} points)")
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
        short_centerlines = []  # Centerlines with few points (likely short roads)

        for lane in local_map.lanes:
            if lane.centerline_points:
                points = [(p.x, p.y) for p in lane.centerline_points]
                if len(points) > 1:
                    # Log road266 centerlines for debugging
                    if lane.road_id == 266:
                        max_y = max(p[1] for p in points)
                        min_y = min(p[1] for p in points)
                        logger.info(f"Road266 lane {lane.lane_id}: {len(points)} points, Y range=[{min_y:.2f}, {max_y:.2f}]")
                        logger.info(f"  First point: {points[0]}, Last point: {points[-1]}")
                    
                    # Separate short centerlines (<=5 points or short length)
                    if len(points) <= 5:
                        # Calculate approximate length
                        total_length = 0
                        for i in range(len(points) - 1):
                            dx = points[i+1][0] - points[i][0]
                            dy = points[i+1][1] - points[i][1]
                            total_length += (dx*dx + dy*dy) ** 0.5
                        if total_length <= 10:  # Short road (<=10m)
                            short_centerlines.append(points)
                        else:
                            centerlines.append(points)
                    else:
                        centerlines.append(points)

        logger.debug(f"Found {len(centerlines)} regular centerlines and {len(short_centerlines)} short centerlines (out of {len(local_map.lanes)} total lanes)")

        # Plot regular centerlines (lime dashed, thinner)
        if centerlines:
            lc_center = LineCollection(centerlines, colors='lime',
                                      linewidths=1.0, alpha=0.8,
                                      linestyles='--', label='Centerline')
            self.ax.add_collection(lc_center)
            logger.debug(f"Plotted {len(centerlines)} regular centerlines")
        
        # Plot short centerlines with more visible style (thicker, solid, cyan)
        if short_centerlines:
            lc_short = LineCollection(short_centerlines, colors='cyan',
                                      linewidths=2.0, alpha=1.0,
                                      linestyles='-', label='Short Centerline')
            self.ax.add_collection(lc_short)
            logger.debug(f"Plotted {len(short_centerlines)} short centerlines with enhanced visibility")
        
        if not centerlines and not short_centerlines:
            logger.debug("No centerlines to plot")

    def _plot_road_ids(self, local_map: LocalMap) -> None:
        """Plot Road ID labels at the center of each lane.
        
        This method adds Road ID text labels to help identify which road
        each lane belongs to. The label is placed at the midpoint of each
        lane's centerline, but only if the midpoint is within the visible range.
        For lanes belonging to the same road, only one label is shown.
        """
        import math
        
        # Get visible range from metadata (in local coordinates, ego is at origin)
        # Use map_range from metadata instead of axis limits, since axis limits
        # may not be set yet when this method is called
        if local_map.metadata:
            map_range_x = local_map.metadata.map_range_x
            map_range_y = local_map.metadata.map_range_y
        else:
            # Fallback: calculate from actual data bounds
            all_x = []
            all_y = []
            for lane in local_map.lanes:
                for pt in lane.centerline_points:
                    all_x.append(pt.x)
                    all_y.append(pt.y)
            if all_x and all_y:
                map_range_x = max(abs(min(all_x)), abs(max(all_x))) + 10
                map_range_y = max(abs(min(all_y)), abs(max(all_y))) + 10
            else:
                map_range_x = 100.0
                map_range_y = 100.0
        
        def is_in_visible_range(x, y, margin=10):
            """Check if point is within visible range with small margin."""
            return (abs(x) <= map_range_x + margin and abs(y) <= map_range_y + margin)
        
        # Group lanes by road_id and find the best lane for labeling each road
        road_lanes = {}  # {road_id: best_lane_info}
        
        for lane in local_map.lanes:
            if not lane.centerline_points or len(lane.centerline_points) < 2:
                continue
            
            # Get road_id - use the new road_id directly
            road_id = lane.road_id
            
            if road_id is None:
                continue
            
            # Filter centerline_points to only include points within the visible range
            # This handles cases where clipping didn't fully work
            visible_points = [(i, pt) for i, pt in enumerate(lane.centerline_points)
                             if is_in_visible_range(pt.x, pt.y)]
            
            # Skip this lane if no points are in visible range
            if not visible_points:
                continue
            
            # Find the best point for labeling - prefer a point near the "visual center"
            # of the visible portion of the lane
            label_x, label_y = None, None
            
            if len(visible_points) == 1:
                # Only one visible point, use it
                label_x, label_y = visible_points[0][1].x, visible_points[0][1].y
            else:
                # Use the midpoint of the visible points
                mid_visible_idx = len(visible_points) // 2
                label_x, label_y = visible_points[mid_visible_idx][1].x, visible_points[mid_visible_idx][1].y
            
            # Final sanity check: ensure label position is within range
            if not is_in_visible_range(label_x, label_y):
                continue
            
            # Calculate lane "weight" - prefer lanes with more visible points
            lane_weight = len(visible_points)
            
            if road_id not in road_lanes or lane_weight > road_lanes[road_id]['weight']:
                road_lanes[road_id] = {
                    'weight': lane_weight,
                    'x': label_x,
                    'y': label_y,
                    'lane': lane
                }
        
        # Plot Road ID labels
        plotted_count = 0
        for road_id, info in road_lanes.items():
            # Determine label text - show original road ID
            label_text = f"R{road_id}"
            
            # Check if this is a junction lane (has junction_id)
            lane = info['lane']
            junction_id = lane.original_junction_id if lane.original_junction_id is not None else lane.junction_id
            if junction_id is not None:
                label_text = f"R{road_id}\n(J{junction_id})"
            
            # Add text label with cyan color for visibility on black background
            self.ax.text(
                info['x'], info['y'],
                label_text,
                fontsize=9,
                fontweight='bold',
                color='cyan',
                alpha=0.9,
                ha='center',
                va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6, edgecolor='cyan'),
                zorder=15
            )
            plotted_count += 1
        
        logger.debug(f"Plotted {plotted_count} Road ID labels")

    def _plot_lane_ids(self, local_map: LocalMap) -> None:
        """Plot Lane ID labels at the center of each lane.
        
        This method adds Lane ID text labels to help identify each lane.
        The label is placed at the midpoint of each lane's centerline.
        Uses a smaller font size than road ID labels.
        """
        import math
        
        # Get visible range from metadata (in local coordinates, ego is at origin)
        # Use map_range from metadata instead of axis limits, since axis limits
        # may not be set yet when this method is called
        if local_map.metadata:
            map_range_x = local_map.metadata.map_range_x
            map_range_y = local_map.metadata.map_range_y
        else:
            # Fallback: calculate from actual data bounds
            all_x = []
            all_y = []
            for lane in local_map.lanes:
                for pt in lane.centerline_points:
                    all_x.append(pt.x)
                    all_y.append(pt.y)
            if all_x and all_y:
                map_range_x = max(abs(min(all_x)), abs(max(all_x))) + 10
                map_range_y = max(abs(min(all_y)), abs(max(all_y))) + 10
            else:
                map_range_x = 100.0
                map_range_y = 100.0
        
        def is_in_visible_range(x, y, margin=10):
            """Check if point is within visible range with small margin."""
            return (abs(x) <= map_range_x + margin and abs(y) <= map_range_y + margin)
        
        plotted_count = 0
        for lane in local_map.lanes:
            if not lane.centerline_points or len(lane.centerline_points) < 2:
                continue
            
            # Get lane_id - use the new lane_id directly
            lane_id = lane.lane_id
            
            if lane_id is None:
                continue
            
            # Filter centerline_points to only include points within the visible range
            # This handles cases where clipping didn't fully work
            visible_points = [(i, pt) for i, pt in enumerate(lane.centerline_points)
                             if is_in_visible_range(pt.x, pt.y)]
            
            # Skip this lane if no points are in visible range
            if not visible_points:
                continue
            
            # Find the best point for labeling - prefer a point near the "visual center"
            # of the visible portion of the lane
            label_x, label_y = None, None
            
            if len(visible_points) == 1:
                # Only one visible point, use it
                label_x, label_y = visible_points[0][1].x, visible_points[0][1].y
            else:
                # Use the midpoint of the visible points
                mid_visible_idx = len(visible_points) // 2
                label_x, label_y = visible_points[mid_visible_idx][1].x, visible_points[mid_visible_idx][1].y
            
            # Final sanity check: ensure label position is within range
            if not is_in_visible_range(label_x, label_y):
                continue
            
            # Add text label with smaller font (7pt vs 9pt for road IDs)
            self.ax.text(
                label_x, label_y,
                f"L{lane_id}",
                fontsize=7,  # Smaller font than road IDs (9pt)
                fontweight='normal',
                color='lightgreen',
                alpha=0.8,
                ha='center',
                va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.5, edgecolor='lightgreen', linewidth=0.5),
                zorder=14
            )
            plotted_count += 1
        
        logger.debug(f"Plotted {plotted_count} Lane ID labels")

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
                          marker='x', linewidths=1,
                          label='Test Point' if i == 0 else None)

            # Add point number
            self.ax.text(point.x + 1, point.y + 1,
                       f"P{i+1}", fontsize=8, alpha=0.7, color='white')

    def _plot_trajectory(self, trajectory_points: List[Point3D]) -> None:
        """Plot trajectory as a connected path with gradient color."""
        if not trajectory_points or len(trajectory_points) < 2:
            return

        import numpy as np
        
        # Extract x, y coordinates
        x_coords = [p.x for p in trajectory_points]
        y_coords = [p.y for p in trajectory_points]
        
        # Create line segments for colored trajectory
        points = np.array([x_coords, y_coords]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        # Create color array (gradient from cyan to red based on position in trajectory)
        colors = plt.cm.coolwarm(np.linspace(0, 1, len(segments)))
        
        # Plot trajectory segments with gradient color
        for i, (seg, color) in enumerate(zip(segments, colors)):
            self.ax.plot(seg[:, 0], seg[:, 1], color=color, linewidth=2, alpha=0.8,
                        label='Trajectory' if i == 0 else None)
        
        # Mark start point (green)
        self.ax.scatter(x_coords[0], y_coords[0], c='lime', s=80, marker='o',
                       edgecolors='white', linewidths=2, zorder=5, label='Start')
        
        # Mark end point (red)
        self.ax.scatter(x_coords[-1], y_coords[-1], c='red', s=80, marker='s',
                       edgecolors='white', linewidths=2, zorder=5, label='End')

    def _add_legend(
        self,
        show_lanes: bool,
        show_centerlines: bool,
        show_traffic_elements: bool,
        show_ego_position: bool,
        ego_points: Optional[List[Point3D]],
        trajectory_points: Optional[List[Point3D]] = None
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
            handles.append(Line2D([0], [0], color='#00BFFF', linestyle='-', linewidth=1, label='Unknown Boundary (Virtual)'))
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
        if trajectory_points and len(trajectory_points) >= 2:
            handles.append(Line2D([0], [0], color='cyan', linewidth=2, label='Trajectory'))
            handles.append(Line2D([0], [0], marker='o', color='lime', linestyle='None',
                               markersize=8, markeredgecolor='white', label='Start'))
            handles.append(Line2D([0], [0], marker='s', color='red', linestyle='None',
                               markersize=8, markeredgecolor='white', label='End'))

        if handles:
            self.ax.legend(handles=handles, loc='upper right', fontsize=9, labelcolor='white')

    def auto_scale_axis(self, local_map: LocalMap) -> None:
        """Auto-scale axis based on local map content.
        
        For local maps, data is in local coordinates (ego at origin).
        Use map_range from metadata to set axis limits.
        """
        # Use metadata map_range to set axis limits
        # In local coordinates, ego is at (0, 0)
        if local_map.metadata:
            map_range_x = local_map.metadata.map_range_x
            map_range_y = local_map.metadata.map_range_y
            
            # Set axis limits based on map_range (ego at origin in local coords)
            self.ax.set_xlim(-map_range_x, map_range_x)
            self.ax.set_ylim(-map_range_y, map_range_y)
        else:
            # Fallback: calculate bounds from all points
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

            if all_points:
                xs, ys = zip(*all_points)
                self.ax.set_xlim(min(xs) - 10, max(xs) + 10)
                self.ax.set_ylim(min(ys) - 10, max(ys) + 10)

