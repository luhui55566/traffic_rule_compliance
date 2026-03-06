"""
Main constructor for XODR to LocalMap conversion.

This module provides the main interface for converting XODR maps
loaded by maploader to LocalMap format.
"""

import logging
from typing import Optional, Set
from datetime import datetime

from common.local_map.local_map_data import LocalMap, Pose, Point3D, Lane, TrafficLight
from map_node.maploader.loader_xodr import XODRLoader, XODRMapData
from .config_types import ConversionConfig, ConversionResult, ConversionStatistics
from .transformer import XODRCoordinateTransformer
from .converter import XODRMapConverter
from .builder import LocalMapBuilder
from .road_finder import XODRRoadFinder

logger = logging.getLogger(__name__)


class LocalMapConstructor:
    """
    Constructor for converting XODR maps to LocalMap.
    
    This class orchestrates the complete conversion process:
    1. Load XODR map using XODRLoader
    2. Initialize coordinate transformer
    3. Convert XODR elements to LocalMap structures
    4. Build complete LocalMap
    """
    
    def __init__(self, config: ConversionConfig = None):
        """
        Initialize LocalMap constructor.
        
        Args:
            config: Conversion configuration
        """
        self.config = config or ConversionConfig()
        self.loader = XODRLoader()
        self.transformer: Optional[XODRCoordinateTransformer] = None
        self.converter: Optional[XODRMapConverter] = None
        self.builder: Optional[LocalMapBuilder] = None
        self.statistics: Optional[ConversionStatistics] = None
    
    def load_xodr_map(self, file_path: str) -> bool:
        """
        Load XODR map file.
        
        Args:
            file_path: Path to XODR file
            
        Returns:
            True if loading succeeded
        """
        logger.info(f"Loading XODR map from: {file_path}")
        success = self.loader.load_map(file_path)
        
        if success:
            self._initialize_components()
            logger.info(f"XODR map loaded successfully with {len(self.loader.get_map_data().get_roads())} roads")
        else:
            logger.error("Failed to load XODR map")
        
        return success
    
    def _initialize_components(self):
        """Initialize transformer, converter, and builder with current config."""
        # Initialize transformer with ego pose from config
        ego_pose = Pose(
            position=Point3D(
                x=self.config.ego_x,
                y=self.config.ego_y,
                z=0.0
            ),
            heading=self.config.ego_heading
        )
        self.transformer = XODRCoordinateTransformer(ego_pose)
        
        # Initialize converter
        self.converter = XODRMapConverter(self.transformer, self.config)
        
        # Initialize builder
        self.builder = LocalMapBuilder(self.converter, self.config)
    
    def set_map_data(self, map_data: 'XODRMapData') -> bool:
        """
        Set pre-loaded XODR map data to avoid reloading.
        
        Args:
            map_data: Pre-loaded XODRMapData object
            
        Returns:
            True if map data was set successfully
        """
        if map_data is None:
            logger.error("Cannot set None map data")
            return False
        
        # XODRLoader使用map_data（没有下划线）
        self.loader.map_data = map_data
        # 同时设置odr_map，因为is_loaded()检查的是odr_map
        self.loader.odr_map = map_data.odr_map
        self._initialize_components()
        
        logger.info(f"Pre-loaded XODR map set with {len(map_data.get_roads())} roads")
        return True
    
    def update_config(self, config: ConversionConfig) -> None:
        """
        Update configuration and reinitialize components.
        
        This method allows changing the ego position without reloading the map.
        
        Args:
            config: New conversion configuration
        """
        self.config = config
        if self.loader.is_loaded():
            self._initialize_components()
            logger.debug(f"Config updated: ego=({config.ego_x:.2f}, {config.ego_y:.2f})")
    
    def _is_road_in_range(self, odr_road) -> bool:
        """
        Check if any part of road is within map_range of ego position.
        
        Args:
            odr_road: PyRoad object
            
        Returns:
            True if road is within range, False otherwise
        """
        ego_x = self.config.ego_x
        ego_y = self.config.ego_y
        map_range = self.config.map_range
        map_range_sq = map_range * map_range  # Use squared distance for efficiency
        
        # Sample points along the road at 100m intervals
        sample_step = 100.0  # Sample every 100 meters
        road_length = odr_road.length
        
        # Check start, middle, and end points
        for s in [0.0, road_length / 2.0, road_length]:
            pos = odr_road.get_xyz(s, 0.0, 0.0)
            dx = pos.array[0] - ego_x
            dy = pos.array[1] - ego_y
            dist_sq = dx * dx + dy * dy
            if dist_sq <= map_range_sq:
                return True
        
        # Sample intermediate points
        num_samples = int(road_length / sample_step) + 1
        for i in range(1, num_samples):
            s = i * sample_step
            if s >= road_length:
                break
            pos = odr_road.get_xyz(s, 0.0, 0.0)
            dx = pos.array[0] - ego_x
            dy = pos.array[1] - ego_y
            dist_sq = dx * dx + dy * dy
            if dist_sq <= map_range_sq:
                return True
        
        return False
    
    def process_roads_and_junctions(self) -> None:
        """Process all roads and junctions from the loaded XODR map."""
        if not self.loader.is_loaded():
            logger.error("No map loaded, cannot process roads and junctions")
            return
        
        map_data = self.loader.get_map_data()
        odr_map = self.loader.odr_map
        
        # Log map_range configuration
        logger.info(f"Configured map_range: {self.config.map_range} meters")
        logger.info(f"Ego position: ({self.config.ego_x:.2f}, {self.config.ego_y:.2f})")
        
        # Use XODRRoadFinder to find connected roads within range
        # This prevents "dangling" road segments that are within range but not connected
        logger.info("Finding connected roads using road network topology...")
        road_finder = XODRRoadFinder(odr_map)
        connected_positions = road_finder.find_connected_roads_in_range(
            x=self.config.ego_x,
            y=self.config.ego_y,
            z=self.config.ego_z,
            max_distance=self.config.map_range,
            ego_road_threshold=20.0  # Consider ego on roads within 20m
        )
        
        # Build set of connected road IDs for fast lookup
        connected_road_ids: Set[str] = {rp.road_id for rp in connected_positions}
        logger.info(f"Found {len(connected_road_ids)} connected roads within range")
        
        logger.info("Processing roads...")
        
        # Count total and filtered roads
        total_roads = len(map_data.get_roads())
        roads_in_range = 0
        roads_filtered_by_distance = 0
        roads_filtered_by_connectivity = 0
        
        # Process all roads with distance AND connectivity filtering
        for odr_road in map_data.get_roads():
            road_id = odr_road.id.decode() if isinstance(odr_road.id, bytes) else str(odr_road.id)
            
            # Check if road is within map_range (distance filter)
            if not self._is_road_in_range(odr_road):
                roads_filtered_by_distance += 1
                continue
            
            # Check if road is connected to ego's road network (connectivity filter)
            if road_id not in connected_road_ids:
                roads_filtered_by_connectivity += 1
                continue
            
            roads_in_range += 1
            try:
                # Convert Road object
                road = self.converter.convert_road_to_road_object(odr_road)
                self.converter._roads[road.road_id] = road
                
                # Process lane sections
                for lanesection in map_data.get_lanesections(odr_road):
                    lanesection_s0 = lanesection.s0 if hasattr(lanesection, 's0') else 0.0
                    lanesection_end = odr_road.get_lanesection_end(lanesection)
                    
                    # Get all lanes in this section for offset calculation
                    lanes = map_data.get_lanes(lanesection)
                    
                    # Process lanes in this section
                    for odr_lane in lanes:
                        # Convert Lane to LocalMap Lane
                        result = self.converter.convert_lane_to_lane(odr_road, odr_lane, lanesection_s0,lanesection_end, lanes)
                        
                        if result.success:
                            lane = result.data
                            # Skip center lane (lane_id=0) - boundaries will be handled by adjacent lanes
                            if lane is None:
                                continue
                            
                            self.builder.add_lane(lane)
                            road.lane_ids.append(lane.lane_id)
                            
                            # Process boundary segments
                            self._process_lane_boundaries(odr_road, odr_lane, lanesection_s0,lanesection_end,lane)
                        else:
                            logger.warning(f"Failed to convert lane: {result.errors}")
                
            except Exception as e:
                logger.error(f"Error processing road {odr_road.id}: {e}")
        
        # Log road filtering statistics
        roads_filtered = total_roads - roads_in_range
        logger.info(f"Road filtering: {roads_in_range}/{total_roads} roads in range")
        logger.info(f"  Filtered by distance: {roads_filtered_by_distance}")
        logger.info(f"  Filtered by connectivity (dangling roads): {roads_filtered_by_connectivity}")
        
        logger.info("Processing junctions...")
        
        # Get set of processed road IDs for junction filtering
        processed_road_ids = set(self.converter._roads.keys())
        junctions_in_range = 0
        junctions_filtered = 0
        
        # Process only junctions that are related to processed roads
        if hasattr(odr_map, 'get_junctions'):
            for odr_junction in odr_map.get_junctions():
                try:
                    # Collect connected road IDs
                    junction_connected_road_ids = []
                    if hasattr(odr_junction, 'id_to_connection'):
                        for conn in odr_junction.id_to_connection.values():
                            junction_connected_road_ids.append(int(conn.incoming_road))
                            junction_connected_road_ids.append(int(conn.connecting_road))
                    
                    # Filter: Only include junction if at least one of its roads is in processed_roads
                    # This ensures we only include junctions that are actually relevant to the local area
                    has_connected_road = any(
                        road_id in processed_road_ids for road_id in junction_connected_road_ids
                    )
                    
                    if not has_connected_road:
                        junctions_filtered += 1
                        continue
                    
                    junctions_in_range += 1
                    
                    # Convert Junction object
                    junction = self.converter.convert_junction_to_junction_object(
                        odr_junction, junction_connected_road_ids
                    )
                    if junction:
                        self.converter._junctions[junction.junction_id] = junction
                except Exception as e:
                    logger.error(f"Error processing junction {odr_junction.id}: {e}")
        
        logger.info(f"Junction filtering: {junctions_in_range} in range, {junctions_filtered} filtered out")
        logger.info(f"Processed {len(self.converter._roads)} roads and "
                   f"{len(self.converter._junctions)} junctions")
        
        # Post-process: Merge lanes with same original_lane_id within same road
        #self._merge_lanes_across_sections()
        # 后处理：填充车道邻接关系
        self._validate_adjacent_lane_relations()

    
    def _merge_lanes_across_sections(self) -> None:
        """
        Merge lanes with same original_lane_id within same road across lane sections.
        
        This merges multiple lane objects (one per lane section) into a single Lane object:
        - Centerlines are merged into the first lane
        - Boundary indices are merged
        - Speed limits are merged
        - Predecessor is the first lane's predecessor
        - Successor is the last lane's successor
        - Other lanes are removed from the builder
        """
        logger.info("Merging lanes across lane sections...")
        
        # Group lanes by (original_road_id, original_lane_id)
        lane_groups = {}
        for lane_id in self.builder._lanes:
            lane = self.builder.get_lane_by_id(lane_id)
            if not lane:
                continue
            # Use string key (Lane objects are not hashable)
            key = f"{lane.original_road_id}_{lane.original_lane_id}"
            if key not in lane_groups:
                lane_groups[key] = []
            lane_groups[key].append(lane_id)
        
        # For each group, merge lanes into the first lane
        lanes_to_remove = []
        for (road_id, original_lane_id), lane_ids in lane_groups.items():
            if len(lane_ids) > 1:
                # Sort by lane_id (which includes lanesection_s0 in the hash)
                lane_ids_sorted = sorted(lane_ids)
                
                # First lane is the merged lane
                first_lane_id = lane_ids_sorted[0]
                first_lane = self.builder.get_lane_by_id(first_lane_id)
                if not first_lane:
                    continue
                
                # Merge centerlines from all lanes
                merged_centerline = []
                for lane_id in lane_ids_sorted:
                    lane = self.builder.get_lane_by_id(lane_id)
                    if lane and lane.centerline_points:
                        merged_centerline.extend(lane.centerline_points)
                first_lane.centerline_points = merged_centerline
                
                # Merge boundary indices (remove duplicates)
                merged_left_boundaries = []
                merged_right_boundaries = []
                for lane_id in lane_ids_sorted:
                    lane = self.builder.get_lane_by_id(lane_id)
                    if not lane:
                        continue
                    for idx in lane.left_boundary_segment_indices:
                        if idx not in merged_left_boundaries:
                            merged_left_boundaries.append(idx)
                    for idx in lane.right_boundary_segment_indices:
                        if idx not in merged_right_boundaries:
                            merged_right_boundaries.append(idx)
                first_lane.left_boundary_segment_indices = merged_left_boundaries
                first_lane.right_boundary_segment_indices = merged_right_boundaries
                
                # Merge per-point speed limits
                merged_max_speed_limits = []
                merged_min_speed_limits = []
                merged_speed_limit_types = []
                for lane_id in lane_ids_sorted:
                    lane = self.builder.get_lane_by_id(lane_id)
                    if not lane:
                        continue
                    merged_max_speed_limits.extend(lane.max_speed_limits)
                    merged_min_speed_limits.extend(lane.min_speed_limits)
                    merged_speed_limit_types.extend(lane.speed_limit_types)
                first_lane.max_speed_limits = merged_max_speed_limits
                first_lane.min_speed_limits = merged_min_speed_limits
                first_lane.speed_limit_types = merged_speed_limit_types
                
                # Predecessor is the first lane's predecessor
                # Successor is the last lane's successor
                last_lane_id = lane_ids_sorted[-1]
                last_lane = self.builder.get_lane_by_id(last_lane_id)
                if last_lane:
                    first_lane.predecessor_lane_ids = list(last_lane.predecessor_lane_ids)
                    first_lane.successor_lane_ids = list(last_lane.successor_lane_ids)
                
                # Mark other lanes for removal
                for lane_id in lane_ids_sorted[1:]:
                    lanes_to_remove.append(lane_id)
        
        # Remove merged lanes from builder
        for lane_id in lanes_to_remove:
            self.builder._lanes.remove(lane_id)
            # Also remove from lane map
            if lane_id in self.builder._lane_map:
                del self.builder._lane_map[lane_id]
        
        logger.info(f"Merged {len(lanes_to_remove)} lanes across lane sections")
    
    def _process_lane_boundaries(
        self,
        odr_road,
        odr_lane,
        lanesection_s0: float,
        lanesection_end: float,
        lane: Lane
    ) -> None:
        """
        Process boundary segments for a lane.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            odr_lane: pyOpenDRIVE Lane object
            lanesection_s0: Lane section start s coordinate
            lane: LocalMap Lane object
        """
        road_id = lane.road_id
        lane_id = lane.original_lane_id
        
        left_boundary_indices = []
        right_boundary_indices = []
        
        # Extract both inner and outer boundaries for each lane
        # In XODR, each lane has two boundaries: inner (closer to road center) and outer (farther from road center)
        
        # For each lane, we need to extract both boundaries
        for is_outer in [True, False]:
            boundary_segment = self.converter.convert_boundary_segment(
                odr_road, odr_lane,
                is_outer=is_outer,
                road_id=road_id,
                lanesection_s0=lanesection_s0,
                lanesection_end=lanesection_end,
                lane_id=lane_id
            )
            
            if boundary_segment:
                # Add to builder
                if self.builder.add_boundary_segment(boundary_segment):
                    # Determine if this is left or right boundary based on lane ID and inner/outer
                    # For right-side lanes (positive ID): left = inner, right = outer
                    # For left-side lanes (negative ID): left = outer, right = inner
                    is_left_boundary = (lane_id < 0) == is_outer
                    
                    if is_left_boundary:
                        left_boundary_indices.append(boundary_segment.segment_id)
                    else:
                        right_boundary_indices.append(boundary_segment.segment_id)
        
        # Associate boundaries with lane
        self.builder.associate_lane_with_boundaries(lane, left_boundary_indices, right_boundary_indices)
    
    def process_traffic_elements(self) -> None:
        """Process traffic elements (signals, objects) from the loaded XODR map."""
        if not self.loader.is_loaded():
            logger.error("No map loaded, cannot process traffic elements")
            return
        
        map_data = self.loader.get_map_data()
        
        logger.info("Processing traffic signals and objects...")
        
        # Only process traffic elements from roads that are within map_range
        # Get filtered road IDs
        filtered_road_ids = set(self.converter._roads.keys())
        logger.info(f"Processing traffic elements from {len(filtered_road_ids)} filtered roads")
        
        # Process each road for traffic elements
        for odr_road in map_data.get_roads():
            road_id = int(odr_road.id.decode() if isinstance(odr_road.id, bytes) else odr_road.id)
            
            # Skip roads that are not in range
            if road_id not in filtered_road_ids:
                continue
            road_id = int(odr_road.id.decode() if isinstance(odr_road.id, bytes) else odr_road.id)
            
            # Process traffic signals
            if hasattr(odr_road, 'get_road_signals'):
                for odr_signal in odr_road.get_road_signals():
                    try:
                        # Determine if this is a traffic sign or light
                        signal_type = int(odr_signal.type) if hasattr(odr_signal, 'type') else 0
                        
                        # Check for known traffic sign types
                        sign_types = [274, 275, 205, 206, 209, 211, 222, 223, 224, 235]
                        
                        if signal_type in sign_types:
                            # Convert to traffic sign
                            sign = self.converter.convert_traffic_sign(odr_road, odr_signal, road_id)
                            if sign:
                                self.builder.add_traffic_sign(sign)
                        else:
                            # Assume traffic light
                            light = TrafficLight(
                                traffic_light_id=int(odr_signal.id),
                                position=Point3D(x=0, y=0, z=0),  # Will be calculated properly
                                current_state=self._create_default_traffic_light_state(),
                                associated_lane_id=0,  # Will be associated later
                                distance_to_stop_line=0.0,
                                associated_stop_line_id=0,
                                light_type=self._convert_signal_type_to_light_type(signal_type),
                                confidence=1.0
                            )
                            self.builder.add_traffic_light(light)
                    
                    except Exception as e:
                        logger.warning(f"Error processing signal {odr_signal.id}: {e}")
            
            # Process road objects
            if hasattr(odr_road, 'get_road_objects'):
                for odr_object in odr_road.get_road_objects():
                    try:
                        object_name = odr_object.name.decode() if isinstance(odr_object.name, bytes) else odr_object.name
                        
                        # Check for crosswalk
                        if 'crosswalk' in object_name.lower():
                            crosswalk = self.converter.convert_crosswalk(odr_road, odr_object, road_id)
                            if crosswalk:
                                self.builder.add_crosswalk(crosswalk)
                        # Check for road markings (arrows, stop lines, etc.)
                        elif any(keyword in object_name.lower() for keyword in 
                               ['arrow', 'stop', 'yield', 'marking']):
                            marking = self.converter.convert_road_marking(odr_road, odr_object, road_id)
                            if marking:
                                self.builder.add_road_marking(marking)
                    
                    except Exception as e:
                        logger.warning(f"Error processing object {odr_object.id}: {e}")
        
        logger.info(f"Processed {len(self.builder._traffic_signs)} traffic signs, "
                   f"{len(self.builder._traffic_lights)} traffic lights, "
                   f"{len(self.builder._road_markings)} road markings, "
                   f"{len(self.builder._crosswalks)} crosswalks")
    
    def _create_default_traffic_light_state(self):
        """Create a default traffic light state."""
        from common.local_map.local_map_data import TrafficLightState
        return TrafficLightState(
            timestamp=datetime.now(),
            color=self._get_default_light_color(),
            shape=self._get_default_light_shape(),
            status=self._get_default_light_status(),
            remaining_time=0.0
        )
    
    def _get_default_light_color(self):
        """Get default traffic light color."""
        from common.local_map.local_map_data import TrafficLightColor
        return TrafficLightColor.UNKNOWN
    
    def _get_default_light_shape(self):
        """Get default traffic light shape."""
        from common.local_map.local_map_data import TrafficLightShape
        return TrafficLightShape.UNKNOWN
    
    def _get_default_light_status(self):
        """Get default traffic light status."""
        from common.local_map.local_map_data import TrafficLightStatus
        return TrafficLightStatus.UNKNOWN
    
    def _convert_signal_type_to_light_type(self, signal_type: int):
        """Convert XODR signal type to traffic light type."""
        from common.local_map.local_map_data import TrafficLightType
        # Default to vehicle traffic light
        return TrafficLightType.VEHICLE
    
    def process_junction_connections(self) -> None:
        """Process junction connections to establish lane-to-lane relationships."""
        if not self.loader.is_loaded():
            logger.error("No map loaded, cannot process junction connections")
            return
        
        odr_map = self.loader.odr_map
        
        if not hasattr(odr_map, 'get_junctions'):
            logger.warning("Junctions not available, skipping connection processing")
            return
        
        logger.info("Processing junction connections...")
        
        for odr_junction in odr_map.get_junctions():
            junction_id = int(odr_junction.id.decode() if isinstance(odr_junction.id, bytes) else odr_junction.id)
            
            if not hasattr(odr_junction, 'id_to_connection'):
                continue
            
            for conn in odr_junction.id_to_connection.values():
                try:
                    incoming_road_id = int(conn.incoming_road)
                    connecting_road_id = int(conn.connecting_road)
                    contact_point = conn.contact_point.decode() if isinstance(conn.contact_point, bytes) else conn.contact_point
                    
                    # Get incoming and connecting roads
                    incoming_road = self.converter.get_roads().get(incoming_road_id)
                    connecting_road = self.converter.get_roads().get(connecting_road_id)
                    
                    if not incoming_road or not connecting_road:
                        continue
                    
                    # Process lane links
                    if hasattr(conn, 'lane_links'):
                        for lane_link in conn.lane_links:
                            # lane_link.frm and lane_link.to are properties that return int values
                            from_lane_id = lane_link.frm
                            to_lane_id = lane_link.to
                            
                            # Find the correct lanes by searching through all lanes in the road
                            # We need to match by original_lane_id, not generate lane_id with assumed s0
                            from_lane = None
                            to_lane = None
                            
                            # Search for the from_lane in incoming_road
                            if incoming_road and hasattr(incoming_road, 'lane_ids'):
                                for lane_id in incoming_road.lane_ids:
                                    lane = self.builder.get_lane_by_id(lane_id)
                                    if lane and lane.original_lane_id == from_lane_id:
                                        # For contact_point == 'end', we want the lane at the end of the road
                                        # For contact_point == 'start', we want the lane at the start
                                        # Check if this is the correct lane section based on contact_point
                                        from_lane = lane
                                        break
                            
                            # Search for the to_lane in connecting_road
                            if connecting_road and hasattr(connecting_road, 'lane_ids'):
                                for lane_id in connecting_road.lane_ids:
                                    lane = self.builder.get_lane_by_id(lane_id)
                                    if lane and lane.original_lane_id == to_lane_id:
                                        to_lane = lane
                                        break
                            
                            if from_lane and to_lane:
                                # IMPORTANT: Only add lane IDs, NOT junction IDs
                                if to_lane.lane_id not in from_lane.successor_lane_ids:
                                    from_lane.successor_lane_ids.append(to_lane.lane_id)
                                if from_lane.lane_id not in to_lane.predecessor_lane_ids:
                                    to_lane.predecessor_lane_ids.append(from_lane.lane_id)
                
                except Exception as e:
                    logger.error(f"Error processing junction connection: {e}")
        
        logger.info("Junction connections processed")
    
    def process_direct_road_connections(self) -> None:
        """
        Process direct road-to-road connections (not through junctions).
        This sets up lane successor/predecessor relationships for lanes
        in roads that are directly connected.
        
        Handles both successor and predecessor connections to ensure
        bidirectional lane connectivity.
        
        IMPORTANT: This method skips connections involving junction roads,
        as those are handled by process_junction_connections() based on
        the junction's lane_link definitions.
        """
        logger.info("Processing direct road-to-road connections...")
        
        # Get all roads
        roads = self.converter.get_roads()
        
        # DEBUG: Track centerline gaps
        gap_count = 0
        gap_details = []
        
        # Track processed connections to avoid duplicates
        processed_connections = set()
        
        for road_id, road in roads.items():
            # Process successor connections
            if road.successor_road_id is not None:
                successor_road_id = road.successor_road_id
                connection_key = (road_id, successor_road_id)
                
                if connection_key not in processed_connections and successor_road_id in roads:
                    processed_connections.add(connection_key)
                    successor_road = roads[successor_road_id]
                    
                    # Skip if successor road is a junction road (connecting road)
                    # Check by looking at the first lane's junction_id
                    # Junction road connections are handled by process_junction_connections
                    if successor_road.lane_ids:
                        first_lane = self.builder.get_lane_by_id(successor_road.lane_ids[0])
                        if first_lane and first_lane.junction_id is not None:
                            continue
                    
                    # For each lane in the current road, find the corresponding lane in the successor road
                    for lane_id in road.lane_ids:
                        lane = self.builder.get_lane_by_id(lane_id)
                        if not lane:
                            continue
                        
                        # Find the corresponding lane in the successor road
                        # Match by original lane ID (the lane ID from XODR)
                        for successor_lane_id in successor_road.lane_ids:
                            successor_lane = self.builder.get_lane_by_id(successor_lane_id)
                            if not successor_lane:
                                continue
                            
                            # Check if they have the same original lane ID
                            if lane.original_lane_id == successor_lane.original_lane_id:
                                # Set up the successor/predecessor relationship
                                if successor_lane_id not in lane.successor_lane_ids:
                                    lane.successor_lane_ids.append(successor_lane_id)
                                if lane_id not in successor_lane.predecessor_lane_ids:
                                    successor_lane.predecessor_lane_ids.append(lane_id)
                                
                                # DEBUG: Check centerline gap between connected lanes
                                if lane.centerline_points and successor_lane.centerline_points:
                                    last_point = lane.centerline_points[-1]
                                    first_point = successor_lane.centerline_points[0]
                                    gap = ((last_point.x - first_point.x)**2 +
                                           (last_point.y - first_point.y)**2)**0.5
                                    if gap > 1.0:  # Gap larger than 1 meter
                                        gap_count += 1
                                        if gap_count <= 10:  # Only log first 10 gaps
                                            gap_details.append(
                                                f"  Road {road_id} -> {successor_road_id}, "
                                                f"Lane {lane.original_lane_id}: gap={gap:.2f}m, "
                                                f"end=({last_point.x:.1f},{last_point.y:.1f}), "
                                                f"start=({first_point.x:.1f},{first_point.y:.1f})"
                                            )
                                break
            
            # Process predecessor connections
            if road.predecessor_road_id is not None:
                predecessor_road_id = road.predecessor_road_id
                connection_key = (predecessor_road_id, road_id)
                
                if connection_key not in processed_connections and predecessor_road_id in roads:
                    processed_connections.add(connection_key)
                    predecessor_road = roads[predecessor_road_id]
                    
                    # Skip if current road is a junction road (connecting road)
                    # Check by looking at the first lane's junction_id
                    # Junction road connections are handled by process_junction_connections
                    if road.lane_ids:
                        first_lane = self.builder.get_lane_by_id(road.lane_ids[0])
                        if first_lane and first_lane.junction_id is not None:
                            continue
                    
                    # For each lane in the current road, find the corresponding lane in the predecessor road
                    for lane_id in road.lane_ids:
                        lane = self.builder.get_lane_by_id(lane_id)
                        if not lane:
                            continue
                        
                        # Find the corresponding lane in the predecessor road
                        # Match by original lane ID (the lane ID from XODR)
                        for predecessor_lane_id in predecessor_road.lane_ids:
                            predecessor_lane = self.builder.get_lane_by_id(predecessor_lane_id)
                            if not predecessor_lane:
                                continue
                            
                            # Check if they have the same original lane ID
                            if lane.original_lane_id == predecessor_lane.original_lane_id:
                                # Set up the successor/predecessor relationship
                                # predecessor_road -> current_road
                                if lane_id not in predecessor_lane.successor_lane_ids:
                                    predecessor_lane.successor_lane_ids.append(lane_id)
                                if predecessor_lane_id not in lane.predecessor_lane_ids:
                                    lane.predecessor_lane_ids.append(predecessor_lane_id)
                                
                                # DEBUG: Check centerline gap between connected lanes
                                if lane.centerline_points and predecessor_lane.centerline_points:
                                    last_point = predecessor_lane.centerline_points[-1]
                                    first_point = lane.centerline_points[0]
                                    gap = ((last_point.x - first_point.x)**2 +
                                           (last_point.y - first_point.y)**2)**0.5
                                    if gap > 1.0:  # Gap larger than 1 meter
                                        gap_count += 1
                                        if gap_count <= 10:  # Only log first 10 gaps
                                            gap_details.append(
                                                f"  Road {predecessor_road_id} -> {road_id}, "
                                                f"Lane {lane.original_lane_id}: gap={gap:.2f}m, "
                                                f"end=({last_point.x:.1f},{last_point.y:.1f}), "
                                                f"start=({first_point.x:.1f},{first_point.y:.1f})"
                                            )
                                break
        
        # DEBUG: Log gap information
        if gap_count > 0:
            logger.warning(f"DEBUG: Found {gap_count} centerline gaps > 1m at road connections")
            for detail in gap_details:
                logger.warning(detail)
            
            logger.info("Direct road-to-road connections processed")
        
    def process_intra_road_lane_connections(self) -> None:
        """
        Process lane connections within the same road across lane sections.
        
        When a road has multiple lane sections, lanes with the same original_lane_id
        in consecutive sections should be connected as predecessor/successor.
        
        For example, if Road 1 has:
        - LaneSection 0: Lane -1 (s=0 to s=100)
        - LaneSection 1: Lane -1 (s=100 to s=200)
        
        Then Lane -1 in section 0 is the predecessor of Lane -1 in section 1.
        """
        logger.info("Processing intra-road lane section connections...")
        
        roads = self.converter.get_roads()
        connection_count = 0
        
        for road_id, road in roads.items():
            if len(road.lane_ids) < 2:
                continue
            
            # Group lanes by original_lane_id
            lanes_by_original_id = {}
            for lane_id in road.lane_ids:
                lane = self.builder.get_lane_by_id(lane_id)
                if not lane:
                    continue
                
                orig_id = lane.original_lane_id
                if orig_id not in lanes_by_original_id:
                    lanes_by_original_id[orig_id] = []
                
                # Store lane for sorting by lane_id
                # The lane_id was generated as: f"{road_id}_{lanesection_s0}_{lane_id}"
                # So sorting by lane_id should give us the correct order by lane section
                lanes_by_original_id[orig_id].append(lane)
            
            # For each group of lanes with the same original_lane_id,
            # connect them in order of their lane section s0
            for orig_id, lanes in lanes_by_original_id.items():
                if len(lanes) < 2:
                    continue
                
                # Sort lanes by their lane_id (which encodes the lane section s0)
                sorted_lanes = sorted(lanes, key=lambda l: l.lane_id)
                
                # Connect consecutive lanes
                for i in range(len(sorted_lanes) - 1):
                    current_lane = sorted_lanes[i]
                    next_lane = sorted_lanes[i + 1]
                    
                    # current_lane -> next_lane
                    if next_lane.lane_id not in current_lane.successor_lane_ids:
                        current_lane.successor_lane_ids.append(next_lane.lane_id)
                    if current_lane.lane_id not in next_lane.predecessor_lane_ids:
                        next_lane.predecessor_lane_ids.append(current_lane.lane_id)
                    
                    connection_count += 1
        
        logger.info(f"Intra-road lane section connections processed: {connection_count} connections")
    
    def construct_local_map(self) -> ConversionResult:
        """
        Construct the complete LocalMap.
        
        Returns:
            ConversionResult with LocalMap or error information
        """
        try:
            start_time = datetime.now()
            
            # Clear any previous data
            if self.converter:
                self.converter.clear_cache()
            if self.builder:
                self.builder.clear()
            
            # Process XODR elements
            self.process_roads_and_junctions()
            self.process_traffic_elements()
            self.process_junction_connections()
            self.process_direct_road_connections()
            self.process_intra_road_lane_connections()
            
            # Build LocalMap
            local_map = self.builder.build_local_map()
            
            # Create statistics
            stats = ConversionStatistics(
                start_time=start_time,
                end_time=datetime.now(),
                total_roads=len(self.converter.get_roads()),
                total_lanes=len(self.builder._lanes),
                total_lanesections=0,  # TODO: count lane sections
                total_junctions=len(self.converter.get_junctions()),
                total_connections=sum(j.connection_count for j in self.converter.get_junctions().values()),
                total_boundary_segments=len(self.builder._boundary_segments),
                shared_boundaries=0,  # TODO: count shared boundaries
                total_traffic_signs=len(self.builder._traffic_signs),
                total_traffic_lights=len(self.builder._traffic_lights),
                total_crosswalks=len(self.builder._crosswalks),
                total_stop_lines=len(self.builder._stop_lines),
                conversion_warnings=[],
                conversion_errors=[]
            )
            
            self.statistics = stats
            
            logger.info(f"LocalMap construction completed")
            logger.info(stats.get_summary())
            
            return ConversionResult(
                success=True,
                data=local_map,
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            logger.error(f"Failed to construct LocalMap: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return ConversionResult(
                success=False,
                data=None,
                errors=[f"LocalMap construction failed: {str(e)}"]
            )
    
    def convert(self, xodr_file_path: str) -> ConversionResult:
        """
        Convert XODR file to LocalMap.
        
        Args:
            xodr_file_path: Path to XODR file
            
        Returns:
            ConversionResult with LocalMap or error information
        """
        logger.info(f"Starting XODR to LocalMap conversion: {xodr_file_path}")
        
        # Load XODR map
        if not self.load_xodr_map(xodr_file_path):
            return ConversionResult(
                success=False,
                data=None,
                errors=["Failed to load XODR map"]
            )
        
        # Construct LocalMap
        return self.construct_local_map()
    
    def get_statistics(self) -> Optional[ConversionStatistics]:
        """
        Get conversion statistics.
        
        Returns:
            ConversionStatistics or None if no conversion performed
        """
        return self.statistics

    def _validate_adjacent_lane_relations(self):
        """
        验证所有Lane的邻接关系是否有效
        
        检查每个Lane的邻接ID是否都指向实际存在的Lane
        """
        if not self.builder._lanes:
            return
        
        # 构建所有lane_id的集合
        all_lane_ids = {lane.lane_id for lane in self.builder._lanes}
        
        # 验证每个lane的邻接ID
        invalid_count = 0
        for lane in self.builder._lanes:
            if lane.left_adjacent_lane_id is not None:
                if lane.left_adjacent_lane_id not in all_lane_ids:
                    logger.warning(
                        f"Lane {lane.lane_id} has invalid left_adjacent_lane_id: "
                        f"{lane.left_adjacent_lane_id} (not found in local_map)"
                    )
                    invalid_count += 1
            
            if lane.right_adjacent_lane_id is not None:
                if lane.right_adjacent_lane_id not in all_lane_ids:
                    logger.warning(
                        f"Lane {lane.lane_id} has invalid right_adjacent_lane_id: "
                        f"{lane.right_adjacent_lane_id} (not found in local_map)"
                    )
                    invalid_count += 1
        
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} invalid adjacent lane references")
        else:
            logger.info("All adjacent lane references are valid")
