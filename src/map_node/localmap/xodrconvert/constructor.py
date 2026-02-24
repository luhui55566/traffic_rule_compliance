"""
Main constructor for XODR to LocalMap conversion.

This module provides the main interface for converting XODR maps
loaded by maploader to LocalMap format.
"""

import logging
from typing import Optional
from datetime import datetime

from common.local_map.local_map_data import LocalMap, Pose, Point3D, Lane, TrafficLight
from map_node.maploader.loader_xodr import XODRLoader, XODRMapData
from .config_types import ConversionConfig, ConversionResult, ConversionStatistics
from .transformer import XODRCoordinateTransformer
from .converter import XODRMapConverter
from .builder import LocalMapBuilder

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
            
            logger.info(f"XODR map loaded successfully with {len(self.loader.get_map_data().get_roads())} roads")
        else:
            logger.error("Failed to load XODR map")
        
        return success
    
    def process_roads_and_junctions(self) -> None:
        """Process all roads and junctions from the loaded XODR map."""
        if not self.loader.is_loaded():
            logger.error("No map loaded, cannot process roads and junctions")
            return
        
        map_data = self.loader.get_map_data()
        odr_map = self.loader.odr_map
        
        logger.info("Processing roads...")
        #allroads = map_data.get_roads()
        #alljunctions = map_data.get_junctions()
        # Process all roads
        for odr_road in map_data.get_roads():
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
                            
                            # Process speed limits
                            self._process_lane_speed_limits(odr_road, lane)
                        else:
                            logger.warning(f"Failed to convert lane: {result.errors}")
                
            except Exception as e:
                logger.error(f"Error processing road {odr_road.id}: {e}")
        
        logger.info("Processing junctions...")
        
        # Process all junctions
        if hasattr(odr_map, 'get_junctions'):
            for odr_junction in odr_map.get_junctions():
                try:
                    # Collect connected road IDs
                    connected_road_ids = []
                    if hasattr(odr_junction, 'id_to_connection'):
                        for conn in odr_junction.id_to_connection.values():
                            connected_road_ids.append(int(conn.incoming_road))
                            connected_road_ids.append(int(conn.connecting_road))
                    
                    # Convert Junction object
                    junction = self.converter.convert_junction_to_junction_object(
                        odr_junction, connected_road_ids
                    )
                    if junction:
                        self.converter._junctions[junction.junction_id] = junction
                except Exception as e:
                    logger.error(f"Error processing junction {odr_junction.id}: {e}")
        
        logger.info(f"Processed {len(self.converter._roads)} roads and "
                   f"{len(self.converter._junctions)} junctions")
        
        # Post-process: Merge lanes with same original_lane_id within same road
        #self._merge_lanes_across_sections()
    
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
                
                # Merge speed limits (remove duplicates)
                merged_speed_limits = []
                for lane_id in lane_ids_sorted:
                    lane = self.builder.get_lane_by_id(lane_id)
                    if not lane:
                        continue
                    for sl in lane.speed_limits:
                        if sl not in merged_speed_limits:
                            merged_speed_limits.append(sl)
                first_lane.speed_limits = merged_speed_limits
                
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
    
    def _process_lane_speed_limits(self, odr_road, lane: Lane) -> None:
        """
        Process speed limits for a lane.
        
        Args:
            odr_road: pyOpenDRIVE Road object
            lane: LocalMap Lane object
        """
        speed_limits = []
        
        # Get speed records from road
        if hasattr(odr_road, 'get_s_to_speed'):
            s_to_speed = odr_road.get_s_to_speed()
            if s_to_speed:
                for speed_record in s_to_speed.values():
                    speed_segment = self.converter.convert_speed_limit_segment(
                        odr_road, speed_record, lane.road_id
                    )
                    if speed_segment:
                        speed_limits.append(speed_segment)
        
        # Associate with lane
        if speed_limits:
            self.builder.associate_lane_with_speed_limits(lane, speed_limits)
    
    def process_traffic_elements(self) -> None:
        """Process traffic elements (signals, objects) from the loaded XODR map."""
        if not self.loader.is_loaded():
            logger.error("No map loaded, cannot process traffic elements")
            return
        
        map_data = self.loader.get_map_data()
        
        logger.info("Processing traffic signals and objects...")
        
        # Process each road for traffic elements
        for odr_road in map_data.get_roads():
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
                            
                            # Generate full lane IDs
                            from_full_id = self.converter.generate_lane_id(
                                incoming_road_id,
                                0.0 if contact_point == 'start' else incoming_road.length if hasattr(incoming_road, 'length') else 0.0,
                                from_lane_id
                            )
                            to_full_id = self.converter.generate_lane_id(
                                connecting_road_id,
                                0.0 if contact_point == 'start' else connecting_road.length if hasattr(connecting_road, 'length') else 0.0,
                                to_lane_id
                            )
                            
                            # Update lane connections
                            from_lane = self.builder.get_lane_by_id(from_full_id)
                            to_lane = self.builder.get_lane_by_id(to_full_id)
                            
                            if from_lane and to_lane:
                                # IMPORTANT: Only add lane IDs, NOT junction IDs
                                if to_full_id not in from_lane.successor_lane_ids:
                                    from_lane.successor_lane_ids.append(to_full_id)
                                if from_full_id not in to_lane.predecessor_lane_ids:
                                    to_lane.predecessor_lane_ids.append(from_full_id)
                
                except Exception as e:
                    logger.error(f"Error processing junction connection: {e}")
        
        logger.info("Junction connections processed")
    
    def process_direct_road_connections(self) -> None:
        """
        Process direct road-to-road connections (not through junctions).
        This sets up lane successor/predecessor relationships for lanes
        in roads that are directly connected.
        """
        logger.info("Processing direct road-to-road connections...")
        
        # Get all roads
        roads = self.converter.get_roads()
        
        for road_id, road in roads.items():
            # Check if this road has a direct successor (not through junction)
            if road.successor_road_id is not None:
                successor_road_id = road.successor_road_id
                
                # Get the successor road
                if successor_road_id in roads:
                    successor_road = roads[successor_road_id]
                    
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
                                break
        
        logger.info("Direct road-to-road connections processed")
    
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
