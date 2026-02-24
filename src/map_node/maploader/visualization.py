"""
Visualization utilities for map data.
"""

import logging
from typing import Optional, List, Tuple
from pathlib import Path

try:
    from lanelet2.core import LaneletMap, BasicPoint2d
    LANELET2_AVAILABLE = True
except ImportError:
    LANELET2_AVAILABLE = False
    LaneletMap = None
    BasicPoint2d = None

# Try to import lanelet2.visualization first (built-in)
try:
    from lanelet2 import visualization as lanelet2_viz
    LANELET2_VIZ_AVAILABLE = True
except ImportError:
    LANELET2_VIZ_AVAILABLE = False
    lanelet2_viz = None

# Fallback to matplotlib
try:
    # Set matplotlib to use non-interactive backend before importing
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.collections import LineCollection
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    patches = None
    LineCollection = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapVisualizer:
    """Visualizer for Lanelet2 map data."""
    
    def __init__(self, figsize: Tuple[float, float] = (12, 10)):
        """
        Initialize map visualizer.
        
        Args:
            figsize: Figure size (width, height) in inches
        """
        if not LANELET2_AVAILABLE:
            raise ImportError(
                "Lanelet2 is not installed. Please install it first:\n"
                "  sudo apt-get install liblanelet2-dev python3-lanelet2"
            )
        
        self.figsize = figsize
        self.fig = None
        self.ax = None
        self.use_lanelet2_viz = LANELET2_VIZ_AVAILABLE
    
    def visualize_map(
        self,
        lanelet_map: LaneletMap,
        title: str = "Lanelet2 Map Visualization",
        show_lanelets: bool = True,
        show_areas: bool = True,
        show_points: bool = False,
        save_path: Optional[str] = None,
        dpi: int = 100,
        use_builtin: bool = True
    ) -> None:
        """
        Visualize a Lanelet2 map.
        
        Args:
            lanelet_map: LaneletMap object to visualize
            title: Plot title
            show_lanelets: Whether to show lanelets
            show_areas: Whether to show areas
            show_points: Whether to show points
            save_path: Path to save the figure (optional)
            dpi: DPI for saved figure
            use_builtin: Whether to use lanelet2's built-in visualization (if available)
        """
        # Use lanelet2's built-in visualization if available and requested
        if use_builtin and self.use_lanelet2_viz:
            self._visualize_with_builtin(lanelet_map, title, save_path, dpi)
        else:
            # Fall back to matplotlib
            if not MATPLOTLIB_AVAILABLE:
                raise ImportError(
                    "Matplotlib is not installed. Please install it first:\n"
                    "  pip install matplotlib"
                )
            self._visualize_with_matplotlib(
                lanelet_map, title, show_lanelets, show_areas, show_points, save_path, dpi
            )
    
    def _visualize_with_builtin(
        self,
        lanelet_map: LaneletMap,
        title: str,
        save_path: Optional[str],
        dpi: int
    ) -> None:
        """
        Visualize using lanelet2's built-in visualization.
        
        Args:
            lanelet_map: LaneletMap object to visualize
            title: Plot title
            save_path: Path to save the figure (optional)
            dpi: DPI for saved figure
        """
        logger.info("Using lanelet2's built-in visualization")
        
        # Create figure using lanelet2's visualization
        self.fig, self.ax = lanelet2_viz.drawMap(lanelet_map)
        
        # Set title
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel('X (meters)', fontsize=12)
        self.ax.set_ylabel('Y (meters)', fontsize=12)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or show
        if save_path:
            self.fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
            logger.info(f"Figure saved to: {save_path}")
        
        plt.show()
    
    def _visualize_with_matplotlib(
        self,
        lanelet_map: LaneletMap,
        title: str,
        show_lanelets: bool,
        show_areas: bool,
        show_points: bool,
        save_path: Optional[str],
        dpi: int
    ) -> None:
        """
        Visualize using matplotlib.
        
        Args:
            lanelet_map: LaneletMap object to visualize
            title: Plot title
            show_lanelets: Whether to show lanelets
            show_areas: Whether to show areas
            show_points: Whether to show points
            save_path: Path to save the figure (optional)
            dpi: DPI for saved figure
        """
        logger.info("Using matplotlib for visualization")
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        
        # Plot lanelets
        if show_lanelets:
            self._plot_lanelets(lanelet_map)
        
        # Plot areas
        if show_areas:
            self._plot_areas(lanelet_map)
        
        # Plot points
        if show_points:
            self._plot_points(lanelet_map)
        
        # Set plot properties
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel('X (meters)', fontsize=12)
        self.ax.set_ylabel('Y (meters)', fontsize=12)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')
        
        # Add legend
        self._add_legend(show_lanelets, show_areas, show_points)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or show
        if save_path:
            self.fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
            logger.info(f"Figure saved to: {save_path}")
        
        # plt.show()  # Disabled for WSL/headless environments
    
    def _plot_lanelets(self, lanelet_map: LaneletMap) -> None:
        """Plot lanelets from the map."""
        left_boundaries = []
        right_boundaries = []
        centerlines = []
        
        for lanelet in lanelet_map.laneletLayer:
            # Extract left boundary points
            left_points = []
            for point in lanelet.leftBound:
                left_points.append((point.x, point.y))
            if len(left_points) > 1:
                left_boundaries.append(left_points)
            
            # Extract right boundary points
            right_points = []
            for point in lanelet.rightBound:
                right_points.append((point.x, point.y))
            if len(right_points) > 1:
                right_boundaries.append(right_points)
            
            # Extract centerline points
            center_points = []
            for point in lanelet.centerline:
                center_points.append((point.x, point.y))
            if len(center_points) > 1:
                centerlines.append(center_points)
        
        # Plot left boundaries (blue)
        if left_boundaries:
            lc_left = LineCollection(left_boundaries, colors='blue', linewidths=1.5, alpha=0.7, label='Left Boundary')
            self.ax.add_collection(lc_left)
        
        # Plot right boundaries (red)
        if right_boundaries:
            lc_right = LineCollection(right_boundaries, colors='red', linewidths=1.5, alpha=0.7, label='Right Boundary')
            self.ax.add_collection(lc_right)
        
        # Plot centerlines (green dashed)
        if centerlines:
            lc_center = LineCollection(centerlines, colors='green', linewidths=1.0, alpha=0.5, linestyles='--', label='Centerline')
            self.ax.add_collection(lc_center)
        
        # Auto-scale axis
        all_points = []
        for boundary in left_boundaries + right_boundaries + centerlines:
            all_points.extend(boundary)
        
        if all_points:
            xs, ys = zip(*all_points)
            self.ax.set_xlim(min(xs) - 10, max(xs) + 10)
            self.ax.set_ylim(min(ys) - 10, max(ys) + 10)
    
    def _plot_areas(self, lanelet_map: LaneletMap) -> None:
        """Plot areas from the map."""
        for area in lanelet_map.areaLayer:
            # Extract outer boundary points
            outer_points = []
            for point in area.outerBound:
                outer_points.append((point.x, point.y))
            
            if len(outer_points) > 2:
                # Create polygon patch
                polygon = patches.Polygon(
                    outer_points,
                    closed=True,
                    facecolor='yellow',
                    edgecolor='orange',
                    alpha=0.3,
                    linewidth=1,
                    label='Area' if area == lanelet_map.areaLayer[0] else None
                )
                self.ax.add_patch(polygon)
    
    def _plot_points(self, lanelet_map: LaneletMap) -> None:
        """Plot points from the map."""
        xs = []
        ys = []
        
        for point in lanelet_map.pointLayer:
            xs.append(point.x)
            ys.append(point.y)
        
        if xs:
            self.ax.scatter(xs, ys, c='black', s=10, alpha=0.5, label='Points')
    
    def _add_legend(self, show_lanelets: bool, show_areas: bool, show_points: bool) -> None:
        """Add legend to the plot."""
        handles = []
        labels = []
        
        if show_lanelets:
            from matplotlib.lines import Line2D
            handles.append(Line2D([0], [0], color='blue', lw=1.5, label='Left Boundary'))
            handles.append(Line2D([0], [0], color='red', lw=1.5, label='Right Boundary'))
            handles.append(Line2D([0], [0], color='green', lw=1, linestyle='--', label='Centerline'))
        
        if show_areas:
            handles.append(patches.Patch(facecolor='yellow', edgecolor='orange', alpha=0.3, label='Area'))
        
        if show_points:
            handles.append(patches.Patch(facecolor='black', alpha=0.5, label='Points'))
        
        if handles:
            self.ax.legend(handles=handles, loc='upper right', fontsize=10)
    
    def close(self) -> None:
        """Close the figure."""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None


def visualize_map_simple(
    lanelet_map: LaneletMap,
    title: str = "Lanelet2 Map",
    save_path: Optional[str] = None
) -> None:
    """
    Simple function to visualize a Lanelet2 map.
    
    Args:
        lanelet_map: LaneletMap object to visualize
        title: Plot title
        save_path: Path to save the figure (optional)
    """
    visualizer = MapVisualizer()
    try:
        visualizer.visualize_map(lanelet_map, title=title, save_path=save_path)
    finally:
        visualizer.close()
