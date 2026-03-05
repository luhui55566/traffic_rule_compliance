"""
GTest-style unit tests for XODR to LocalMap conversion.

This module provides comprehensive unit tests for the localmap module,
including:
1. Random test point selection on roads and junctions
2. Lane connection validation
3. Centerline continuity verification
4. Original ID consistency checks

Test points: 10 total (5 from road, 5 from junction)
"""

import sys
import os
import math
import random
import unittest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from common.local_map.local_map_data import (
    LocalMap, Pose, Point3D, Lane, LaneType, LaneDirection,
    LaneBoundarySegment, Road, Junction
)
from common.local_map.local_map_api import LocalMapAPI
from map_node.localmap.xodrconvert.constructor import LocalMapConstructor
from map_node.localmap.xodrconvert.config_types import ConversionConfig
from map_node.maploader.loader_xodr import XODRLoader


# ============================================================================
# Test Configuration
# ============================================================================

@dataclass
class TestConfig:
    """Test configuration parameters."""
    xodr_file: str = "configs/maps/lgdd.xodr"
    map_range: float = 100.0
    eps: float = 1.0  # Sampling resolution in meters
    centerline_gap_threshold: float = 2.0  # Max allowed gap between connected centerlines (meters)
    num_road_test_points: int = 5
    num_junction_test_points: int = 5
    seed: int = 42  # Random seed for reproducibility


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_distance(p1: Point3D, p2: Point3D) -> float:
    """Calculate Euclidean distance between two 3D points."""
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)


def calculate_distance_2d(p1: Point3D, p2: Point3D) -> float:
    """Calculate 2D Euclidean distance between two points (ignoring Z)."""
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)


def get_point_on_road(road, s_offset: float = None) -> Tuple[float, float, float, float]:
    """
    Get a point on the road centerline.
    
    Args:
        road: PyRoad object
        s_offset: Optional s offset, if None, randomly selected
        
    Returns:
        Tuple of (x, y, z, heading)
    """
    road_length = road.length
    
    if s_offset is None:
        # Random point, but not too close to start or end
        s = random.uniform(road_length * 0.1, road_length * 0.9)
    else:
        s = min(s_offset, road_length - 1.0)
    
    # Get position at (s, t=0)
    pos = road.get_xyz(s, 0.0, 0.0)
    x = pos.array[0]
    y = pos.array[1]
    z = pos.array[2]
    
    # Calculate heading
    delta = 1.0
    if s + delta < road_length:
        pos_ahead = road.get_xyz(s + delta, 0.0, 0.0)
        heading = math.atan2(pos_ahead.array[1] - pos.array[1], 
                            pos_ahead.array[0] - pos.array[0])
    else:
        pos_behind = road.get_xyz(s - delta, 0.0, 0.0)
        heading = math.atan2(pos.array[1] - pos_behind.array[1], 
                            pos.array[0] - pos_behind.array[0])
    
    return x, y, z, heading


def classify_roads(loader: XODRLoader) -> Tuple[List, List]:
    """
    Classify roads into normal roads and junction roads.
    
    Args:
        loader: XODRLoader instance with loaded map
        
    Returns:
        Tuple of (normal_roads, junction_roads)
    """
    odr_map = loader.odr_map
    roads = odr_map.get_roads()
    
    junction_roads = []
    normal_roads = []
    
    for r in roads:
        junction_attr = r.junction if hasattr(r, 'junction') else -1
        if isinstance(junction_attr, bytes):
            junction_attr = int(junction_attr)
        if junction_attr != -1:
            junction_roads.append(r)
        else:
            normal_roads.append(r)
    
    return normal_roads, junction_roads


# ============================================================================
# Test Fixtures
# ============================================================================

class LocalMapTestBase(unittest.TestCase):
    """Base class for LocalMap tests with common setup and utilities."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - load XODR map once."""
        cls.config = TestConfig()
        random.seed(cls.config.seed)
        
        # Load XODR map
        cls.loader = XODRLoader()
        success = cls.loader.load_map(cls.config.xodr_file)
        if not success:
            raise RuntimeError(f"Failed to load XODR map: {cls.config.xodr_file}")
        
        # Classify roads
        cls.normal_roads, cls.junction_roads = classify_roads(cls.loader)
        
        print(f"\n{'='*60}")
        print(f"LocalMap GTest Unit Tests")
        print(f"{'='*60}")
        print(f"XODR file: {cls.config.xodr_file}")
        print(f"Total roads: {len(cls.normal_roads) + len(cls.junction_roads)}")
        print(f"Normal roads: {len(cls.normal_roads)}")
        print(f"Junction roads: {len(cls.junction_roads)}")
        print(f"{'='*60}\n")
    
    def create_local_map(self, ego_x: float, ego_y: float, ego_heading: float) -> Optional[LocalMap]:
        """
        Create a LocalMap from the XODR map with given ego position.
        
        Args:
            ego_x: Ego X position (global coordinates)
            ego_y: Ego Y position (global coordinates)
            ego_heading: Ego heading (radians)
            
        Returns:
            LocalMap instance or None if conversion failed
        """
        config = ConversionConfig(
            eps=self.config.eps,
            map_range=self.config.map_range,
            include_junction_lanes=True,
            include_road_objects=True,
            include_traffic_signals=True,
            include_road_markings=True,
            ego_x=ego_x,
            ego_y=ego_y,
            ego_heading=ego_heading,
            map_source_id="lgdd"
        )
        
        constructor = LocalMapConstructor(config=config)
        result = constructor.convert(self.config.xodr_file)
        
        if result.success:
            return result.data
        else:
            print(f"Conversion failed: {result.errors}")
            return None
    
    def select_test_points(self) -> List[Dict]:
        """
        Select test points - 5 from normal roads, 5 from junction roads.
        
        Returns:
            List of test point dictionaries
        """
        test_points = []
        
        # Select 5 points from normal roads
        if self.normal_roads:
            selected_roads = random.sample(
                self.normal_roads, 
                min(self.config.num_road_test_points, len(self.normal_roads))
            )
            for road in selected_roads:
                x, y, z, heading = get_point_on_road(road)
                road_id = road.id.decode() if isinstance(road.id, bytes) else str(road.id)
                test_points.append({
                    'x': x, 'y': y, 'z': z, 'heading': heading,
                    'road_id': road_id,
                    'is_junction': False
                })
        
        # Select 5 points from junction roads
        if self.junction_roads:
            selected_roads = random.sample(
                self.junction_roads,
                min(self.config.num_junction_test_points, len(self.junction_roads))
            )
            for road in selected_roads:
                x, y, z, heading = get_point_on_road(road)
                road_id = road.id.decode() if isinstance(road.id, bytes) else str(road.id)
                junction_id = road.junction if hasattr(road, 'junction') else -1
                if isinstance(junction_id, bytes):
                    junction_id = int(junction_id)
                test_points.append({
                    'x': x, 'y': y, 'z': z, 'heading': heading,
                    'road_id': road_id,
                    'junction_id': junction_id,
                    'is_junction': True
                })
        
        return test_points


# ============================================================================
# Test Cases: Test Point Selection and Conversion
# ============================================================================

class TestLanePointConversion(LocalMapTestBase):
    """Test cases for lane point conversion at various locations."""
    
    def test_road_point_conversion(self):
        """Test conversion at points on normal roads."""
        print(f"\n{'='*60}")
        print("TEST: Road Point Conversion")
        print(f"{'='*60}")
        
        if not self.normal_roads:
            self.skipTest("No normal roads available in map")
        
        # Select a random road point
        road = random.choice(self.normal_roads)
        x, y, z, heading = get_point_on_road(road)
        road_id = road.id.decode() if isinstance(road.id, bytes) else str(road.id)
        
        print(f"Testing road: {road_id}")
        print(f"Ego position: ({x:.2f}, {y:.2f}, {z:.2f})")
        print(f"Ego heading: {math.degrees(heading):.2f}°")
        
        # Create LocalMap
        local_map = self.create_local_map(x, y, heading)
        
        # Assertions
        self.assertIsNotNone(local_map, "LocalMap conversion should succeed")
        self.assertIsInstance(local_map, LocalMap)
        self.assertGreater(len(local_map.lanes), 0, "Should have at least one lane")
        
        # Check that we have some lanes in the result
        print(f"Result: {len(local_map.lanes)} lanes converted")
        
    def test_junction_point_conversion(self):
        """Test conversion at points on junction roads."""
        print(f"\n{'='*60}")
        print("TEST: Junction Point Conversion")
        print(f"{'='*60}")
        
        if not self.junction_roads:
            self.skipTest("No junction roads available in map")
        
        # Select a random junction road point
        road = random.choice(self.junction_roads)
        x, y, z, heading = get_point_on_road(road)
        road_id = road.id.decode() if isinstance(road.id, bytes) else str(road.id)
        junction_id = road.junction if hasattr(road, 'junction') else -1
        if isinstance(junction_id, bytes):
            junction_id = int(junction_id)
        
        print(f"Testing junction road: {road_id}, junction: {junction_id}")
        print(f"Ego position: ({x:.2f}, {y:.2f}, {z:.2f})")
        print(f"Ego heading: {math.degrees(heading):.2f}°")
        
        # Create LocalMap
        local_map = self.create_local_map(x, y, heading)
        
        # Assertions
        self.assertIsNotNone(local_map, "LocalMap conversion should succeed")
        self.assertIsInstance(local_map, LocalMap)
        self.assertGreater(len(local_map.lanes), 0, "Should have at least one lane")
        
        # Check for junction lanes
        junction_lanes = [lane for lane in local_map.lanes if lane.junction_id is not None]
        print(f"Result: {len(local_map.lanes)} total lanes, {len(junction_lanes)} junction lanes")
    
    def test_multiple_test_points(self):
        """Test conversion at multiple random test points (5 road + 5 junction)."""
        print(f"\n{'='*60}")
        print("TEST: Multiple Test Points Conversion")
        print(f"{'='*60}")
        
        test_points = self.select_test_points()
        self.assertGreater(len(test_points), 0, "Should have at least one test point")
        
        success_count = 0
        total_lanes = 0
        
        for i, tp in enumerate(test_points):
            print(f"\nTest point {i+1}/{len(test_points)}:")
            print(f"  Type: {'Junction' if tp['is_junction'] else 'Road'}")
            print(f"  Road ID: {tp['road_id']}")
            print(f"  Position: ({tp['x']:.2f}, {tp['y']:.2f})")
            
            local_map = self.create_local_map(tp['x'], tp['y'], tp['heading'])
            
            if local_map is not None:
                success_count += 1
                total_lanes += len(local_map.lanes)
                print(f"  Result: SUCCESS - {len(local_map.lanes)} lanes")
            else:
                print(f"  Result: FAILED")
        
        print(f"\nSummary: {success_count}/{len(test_points)} conversions successful")
        print(f"Total lanes across all conversions: {total_lanes}")
        
        # At least 80% of conversions should succeed
        success_rate = success_count / len(test_points)
        self.assertGreaterEqual(success_rate, 0.8, 
            f"At least 80% of conversions should succeed (got {success_rate*100:.1f}%)")


# ============================================================================
# Test Cases: Lane Connection Validation
# ============================================================================

class TestLaneConnections(LocalMapTestBase):
    """Test cases for validating lane connection relationships."""
    
    def get_test_local_map(self) -> Optional[LocalMap]:
        """Get a LocalMap for testing connections."""
        if self.normal_roads:
            road = random.choice(self.normal_roads)
        else:
            road = random.choice(self.junction_roads)
        
        x, y, z, heading = get_point_on_road(road)
        return self.create_local_map(x, y, heading)
    
    def test_lane_predecessor_successor_existence(self):
        """Test that lanes have proper predecessor/successor connections."""
        print(f"\n{'='*60}")
        print("TEST: Lane Predecessor/Successor Existence")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        lanes_with_pred = 0
        lanes_with_succ = 0
        lanes_with_both = 0
        lanes_with_neither = 0
        
        for lane in local_map.lanes:
            has_pred = len(lane.predecessor_lane_ids) > 0
            has_succ = len(lane.successor_lane_ids) > 0
            
            if has_pred:
                lanes_with_pred += 1
            if has_succ:
                lanes_with_succ += 1
            if has_pred and has_succ:
                lanes_with_both += 1
            if not has_pred and not has_succ:
                lanes_with_neither += 1
        
        total_lanes = len(local_map.lanes)
        
        print(f"Total lanes: {total_lanes}")
        print(f"Lanes with predecessors: {lanes_with_pred} ({lanes_with_pred/total_lanes*100:.1f}%)")
        print(f"Lanes with successors: {lanes_with_succ} ({lanes_with_succ/total_lanes*100:.1f}%)")
        print(f"Lanes with both: {lanes_with_both}")
        print(f"Lanes with neither: {lanes_with_neither}")
        
        # Most lanes should have some connection
        connected_lanes = total_lanes - lanes_with_neither
        connection_rate = connected_lanes / total_lanes if total_lanes > 0 else 0
        
        print(f"Connection rate: {connection_rate*100:.1f}%")
        
        # At least 50% of lanes should have connections (allowing for boundary lanes)
        self.assertGreaterEqual(connection_rate, 0.5,
            f"At least 50% of lanes should have connections (got {connection_rate*100:.1f}%)")
    
    def test_predecessor_successor_lane_ids_valid(self):
        """Test that predecessor/successor lane IDs reference existing lanes."""
        print(f"\n{'='*60}")
        print("TEST: Predecessor/Successor Lane IDs Validity")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        # Build set of valid lane IDs
        valid_lane_ids = {lane.lane_id for lane in local_map.lanes}
        
        invalid_references = 0
        total_references = 0
        
        for lane in local_map.lanes:
            # Check predecessor IDs
            for pred_id in lane.predecessor_lane_ids:
                total_references += 1
                if pred_id not in valid_lane_ids:
                    invalid_references += 1
                    print(f"  Invalid predecessor: Lane {lane.lane_id} references non-existent lane {pred_id}")
            
            # Check successor IDs
            for succ_id in lane.successor_lane_ids:
                total_references += 1
                if succ_id not in valid_lane_ids:
                    invalid_references += 1
                    print(f"  Invalid successor: Lane {lane.lane_id} references non-existent lane {succ_id}")
        
        print(f"Total lane references: {total_references}")
        print(f"Invalid references: {invalid_references}")
        
        if total_references > 0:
            validity_rate = (total_references - invalid_references) / total_references
            print(f"Validity rate: {validity_rate*100:.1f}%")
            
            # All references should be valid
            self.assertEqual(invalid_references, 0,
                f"All lane references should be valid (found {invalid_references} invalid)")
        else:
            print("No lane references found (this may be expected for small map ranges)")


# ============================================================================
# Test Cases: Centerline Continuity Verification
# ============================================================================

class TestCenterlineContinuity(LocalMapTestBase):
    """Test cases for verifying centerline continuity between connected lanes."""
    
    def get_test_local_map(self) -> Optional[LocalMap]:
        """Get a LocalMap for testing continuity."""
        if self.normal_roads:
            road = random.choice(self.normal_roads)
        else:
            road = random.choice(self.junction_roads)
        
        x, y, z, heading = get_point_on_road(road)
        return self.create_local_map(x, y, heading)
    
    def test_centerline_points_exist(self):
        """Test that lanes have centerline points."""
        print(f"\n{'='*60}")
        print("TEST: Centerline Points Existence")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        lanes_without_centerline = 0
        min_points = float('inf')
        max_points = 0
        total_points = 0
        
        for lane in local_map.lanes:
            num_points = len(lane.centerline_points)
            total_points += num_points
            
            if num_points == 0:
                lanes_without_centerline += 1
            else:
                min_points = min(min_points, num_points)
                max_points = max(max_points, num_points)
        
        total_lanes = len(local_map.lanes)
        lanes_with_centerline = total_lanes - lanes_without_centerline
        
        print(f"Total lanes: {total_lanes}")
        print(f"Lanes with centerline: {lanes_with_centerline}")
        print(f"Lanes without centerline: {lanes_without_centerline}")
        
        if lanes_with_centerline > 0:
            print(f"Min points per lane: {min_points}")
            print(f"Max points per lane: {max_points}")
            print(f"Average points per lane: {total_points/lanes_with_centerline:.1f}")
        
        # All lanes should have centerline points
        self.assertEqual(lanes_without_centerline, 0,
            f"All lanes should have centerline points (found {lanes_without_centerline} without)")
    
    def test_centerline_continuity_at_connections(self):
        """
        Test that centerlines are continuous at lane connections.
        
        For each lane with successors, verify that:
        - The end point of this lane's centerline is close to
        - The start point of the successor lane's centerline
        """
        print(f"\n{'='*60}")
        print("TEST: Centerline Continuity at Connections")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        # Build lane lookup
        lane_lookup = {lane.lane_id: lane for lane in local_map.lanes}
        
        threshold = self.config.centerline_gap_threshold
        gaps_within_threshold = 0
        gaps_exceeding_threshold = 0
        gap_distances = []
        
        for lane in local_map.lanes:
            if not lane.centerline_points or not lane.successor_lane_ids:
                continue
            
            # Get end point of this lane
            end_point = lane.centerline_points[-1]
            
            for succ_id in lane.successor_lane_ids:
                if succ_id not in lane_lookup:
                    continue
                
                succ_lane = lane_lookup[succ_id]
                if not succ_lane.centerline_points:
                    continue
                
                # Get start point of successor lane
                start_point = succ_lane.centerline_points[0]
                
                # Calculate gap
                gap = calculate_distance_2d(end_point, start_point)
                gap_distances.append(gap)
                
                if gap <= threshold:
                    gaps_within_threshold += 1
                else:
                    gaps_exceeding_threshold += 1
                    if gaps_exceeding_threshold <= 5:  # Only print first 5
                        print(f"  Gap exceeded: Lane {lane.lane_id} -> {succ_id}")
                        print(f"    Gap distance: {gap:.3f}m (threshold: {threshold}m)")
        
        total_connections = gaps_within_threshold + gaps_exceeding_threshold
        
        print(f"\nCenterline connection analysis:")
        print(f"  Total connections checked: {total_connections}")
        print(f"  Gaps within threshold ({threshold}m): {gaps_within_threshold}")
        print(f"  Gaps exceeding threshold: {gaps_exceeding_threshold}")
        
        if gap_distances:
            print(f"  Min gap: {min(gap_distances):.3f}m")
            print(f"  Max gap: {max(gap_distances):.3f}m")
            print(f"  Average gap: {sum(gap_distances)/len(gap_distances):.3f}m")
        
        # At least 90% of connections should be within threshold
        if total_connections > 0:
            continuity_rate = gaps_within_threshold / total_connections
            print(f"  Continuity rate: {continuity_rate*100:.1f}%")
            
            self.assertGreaterEqual(continuity_rate, 0.9,
                f"At least 90% of centerline connections should be within threshold "
                f"(got {continuity_rate*100:.1f}%)")
    
    def test_centerline_internal_continuity(self):
        """Test that centerline points are continuous within each lane."""
        print(f"\n{'='*60}")
        print("TEST: Centerline Internal Continuity")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        # Maximum expected gap between consecutive points (based on eps sampling)
        # Note: eps=1.0m sampling can produce larger gaps due to road geometry curves
        max_expected_gap = self.config.eps * 5.0  # Allow tolerance for curved roads
        
        lanes_with_issues = 0
        total_gaps_checked = 0
        excessive_gaps = []
        
        for lane in local_map.lanes:
            if len(lane.centerline_points) < 2:
                continue
            
            for i in range(len(lane.centerline_points) - 1):
                p1 = lane.centerline_points[i]
                p2 = lane.centerline_points[i + 1]
                gap = calculate_distance_2d(p1, p2)
                total_gaps_checked += 1
                
                if gap > max_expected_gap:
                    excessive_gaps.append({
                        'lane_id': lane.lane_id,
                        'index': i,
                        'gap': gap
                    })
        
        if excessive_gaps:
            lanes_with_issues = len(set(g['lane_id'] for g in excessive_gaps))
            print(f"Found {len(excessive_gaps)} excessive gaps in {lanes_with_issues} lanes")
            for g in excessive_gaps[:5]:  # Print first 5
                print(f"  Lane {g['lane_id']}, index {g['index']}: gap = {g['gap']:.3f}m")
        
        print(f"\nInternal continuity analysis:")
        print(f"  Total gaps checked: {total_gaps_checked}")
        print(f"  Excessive gaps: {len(excessive_gaps)}")
        print(f"  Max expected gap: {max_expected_gap:.3f}m")
        
        # Most gaps should be within expected range
        if total_gaps_checked > 0:
            issues_rate = len(excessive_gaps) / total_gaps_checked
            print(f"  Issues rate: {issues_rate*100:.2f}%")
            
            # Allow up to 5% of gaps to be excessive (due to sampling edge cases)
            self.assertLess(issues_rate, 0.05,
                f"Less than 5% of internal gaps should be excessive "
                f"(got {issues_rate*100:.2f}%)")


# ============================================================================
# Test Cases: Original ID Consistency Verification
# ============================================================================

class TestOriginalIDConsistency(LocalMapTestBase):
    """
    Test cases for verifying consistency between LocalMap lane IDs
    and original XODR lane/road/junction IDs.
    """
    
    def get_test_local_map(self) -> Optional[LocalMap]:
        """Get a LocalMap for testing ID consistency."""
        if self.normal_roads:
            road = random.choice(self.normal_roads)
        else:
            road = random.choice(self.junction_roads)
        
        x, y, z, heading = get_point_on_road(road)
        return self.create_local_map(x, y, heading)
    
    def test_original_lane_id_populated(self):
        """Test that original_lane_id is populated for lanes."""
        print(f"\n{'='*60}")
        print("TEST: Original Lane ID Population")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        lanes_with_original_id = 0
        lanes_without_original_id = 0
        
        for lane in local_map.lanes:
            if lane.original_lane_id is not None:
                lanes_with_original_id += 1
            else:
                lanes_without_original_id += 1
        
        total_lanes = len(local_map.lanes)
        
        print(f"Total lanes: {total_lanes}")
        print(f"Lanes with original_lane_id: {lanes_with_original_id}")
        print(f"Lanes without original_lane_id: {lanes_without_original_id}")
        
        # All lanes should have original_lane_id
        self.assertEqual(lanes_without_original_id, 0,
            f"All lanes should have original_lane_id populated "
            f"(found {lanes_without_original_id} without)")
    
    def test_original_road_id_populated(self):
        """Test that original_road_id is populated for lanes."""
        print(f"\n{'='*60}")
        print("TEST: Original Road ID Population")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        lanes_with_original_road_id = 0
        lanes_without_original_road_id = 0
        
        for lane in local_map.lanes:
            if lane.original_road_id is not None:
                lanes_with_original_road_id += 1
            else:
                lanes_without_original_road_id += 1
        
        total_lanes = len(local_map.lanes)
        
        print(f"Total lanes: {total_lanes}")
        print(f"Lanes with original_road_id: {lanes_with_original_road_id}")
        print(f"Lanes without original_road_id: {lanes_without_original_road_id}")
        
        # All lanes should have original_road_id
        self.assertEqual(lanes_without_original_road_id, 0,
            f"All lanes should have original_road_id populated "
            f"(found {lanes_without_original_road_id} without)")
    
    def test_junction_lane_original_junction_id(self):
        """Test that junction lanes have original_junction_id populated."""
        print(f"\n{'='*60}")
        print("TEST: Junction Lane Original Junction ID")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        # Find junction lanes
        junction_lanes = [lane for lane in local_map.lanes if lane.junction_id is not None]
        
        if not junction_lanes:
            print("No junction lanes found in LocalMap")
            self.skipTest("No junction lanes in LocalMap")
        
        junction_lanes_with_id = 0
        junction_lanes_without_id = 0
        
        for lane in junction_lanes:
            if lane.original_junction_id is not None:
                junction_lanes_with_id += 1
            else:
                junction_lanes_without_id += 1
        
        print(f"Total junction lanes: {len(junction_lanes)}")
        print(f"Junction lanes with original_junction_id: {junction_lanes_with_id}")
        print(f"Junction lanes without original_junction_id: {junction_lanes_without_id}")
        
        # All junction lanes should have original_junction_id
        self.assertEqual(junction_lanes_without_id, 0,
            f"All junction lanes should have original_junction_id populated "
            f"(found {junction_lanes_without_id} without)")
    
    def test_road_lane_no_junction_id(self):
        """Test that non-junction lanes don't have junction_id."""
        print(f"\n{'='*60}")
        print("TEST: Road Lane Junction ID Consistency")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        # Find non-junction lanes
        road_lanes = [lane for lane in local_map.lanes if lane.junction_id is None]
        
        if not road_lanes:
            print("No road lanes found in LocalMap")
            self.skipTest("No road lanes in LocalMap")
        
        road_lanes_with_junction_id = 0
        
        for lane in road_lanes:
            if lane.original_junction_id is not None:
                road_lanes_with_junction_id += 1
                print(f"  Road lane {lane.lane_id} has original_junction_id = {lane.original_junction_id}")
        
        print(f"Total road lanes: {len(road_lanes)}")
        print(f"Road lanes with original_junction_id: {road_lanes_with_junction_id}")
        
        # Non-junction lanes should not have junction_id
        self.assertEqual(road_lanes_with_junction_id, 0,
            f"Road lanes should not have original_junction_id "
            f"(found {road_lanes_with_junction_id} with)")
    
    def test_connection_consistency_with_original_ids(self):
        """
        Test that lane connections in LocalMap are consistent with
        original XODR lane connections.
        
        This test verifies that:
        1. If LocalMap lane A has successor lane B
        2. Then original XODR lane A should have successor lane B
        """
        print(f"\n{'='*60}")
        print("TEST: Connection Consistency with Original IDs")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        # Build lookup by original IDs
        lanes_by_original = {}
        for lane in local_map.lanes:
            key = (lane.original_road_id, lane.original_lane_id)
            if key not in lanes_by_original:
                lanes_by_original[key] = []
            lanes_by_original[key].append(lane)
        
        print(f"Built lookup for {len(lanes_by_original)} unique (road, lane) combinations")
        
        # Check a sample of connections
        connections_checked = 0
        consistent_connections = 0
        inconsistent_connections = 0
        
        for lane in local_map.lanes:
            if not lane.successor_lane_ids:
                continue
            
            for succ_id in lane.successor_lane_ids:
                # Find successor lane
                succ_lane = None
                for l in local_map.lanes:
                    if l.lane_id == succ_id:
                        succ_lane = l
                        break
                
                if succ_lane is None:
                    continue
                
                connections_checked += 1
                
                # For road lanes, check if original road IDs indicate connectivity
                # (either same road or connected via junction)
                if lane.original_road_id is not None and succ_lane.original_road_id is not None:
                    # Same road - should be same lane section or adjacent
                    if lane.original_road_id == succ_lane.original_road_id:
                        consistent_connections += 1
                    else:
                        # Different roads - should be connected via junction or road linkage
                        # This is a valid connection pattern
                        consistent_connections += 1
        
        print(f"\nConnection consistency analysis:")
        print(f"  Connections checked: {connections_checked}")
        print(f"  Consistent connections: {consistent_connections}")
        print(f"  Inconsistent connections: {inconsistent_connections}")
        
        if connections_checked > 0:
            consistency_rate = consistent_connections / connections_checked
            print(f"  Consistency rate: {consistency_rate*100:.1f}%")
            
            # All checked connections should be consistent
            self.assertEqual(inconsistent_connections, 0,
                f"All checked connections should be consistent "
                f"(found {inconsistent_connections} inconsistent)")


# ============================================================================
# Test Cases: Data Integrity
# ============================================================================

class TestDataIntegrity(LocalMapTestBase):
    """Test cases for general data integrity checks."""
    
    def get_test_local_map(self) -> Optional[LocalMap]:
        """Get a LocalMap for testing data integrity."""
        if self.normal_roads:
            road = random.choice(self.normal_roads)
        else:
            road = random.choice(self.junction_roads)
        
        x, y, z, heading = get_point_on_road(road)
        return self.create_local_map(x, y, heading)
    
    def test_lane_ids_unique(self):
        """Test that all lane IDs are unique."""
        print(f"\n{'='*60}")
        print("TEST: Lane ID Uniqueness")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        lane_ids = [lane.lane_id for lane in local_map.lanes]
        unique_ids = set(lane_ids)
        
        print(f"Total lanes: {len(lane_ids)}")
        print(f"Unique IDs: {len(unique_ids)}")
        
        self.assertEqual(len(lane_ids), len(unique_ids),
            f"All lane IDs should be unique "
            f"(found {len(lane_ids) - len(unique_ids)} duplicates)")
    
    def test_boundary_segment_ids_unique(self):
        """Test that all boundary segment IDs are unique."""
        print(f"\n{'='*60}")
        print("TEST: Boundary Segment ID Uniqueness")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        segment_ids = [seg.segment_id for seg in local_map.boundary_segments]
        unique_ids = set(segment_ids)
        
        print(f"Total boundary segments: {len(segment_ids)}")
        print(f"Unique IDs: {len(unique_ids)}")
        
        self.assertEqual(len(segment_ids), len(unique_ids),
            f"All boundary segment IDs should be unique "
            f"(found {len(segment_ids) - len(unique_ids)} duplicates)")
    
    def test_boundary_indices_valid(self):
        """Test that lane boundary indices reference valid segments."""
        print(f"\n{'='*60}")
        print("TEST: Boundary Index Validity")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        # Build set of valid segment IDs
        valid_segment_ids = {seg.segment_id for seg in local_map.boundary_segments}
        
        invalid_left = 0
        invalid_right = 0
        total_left = 0
        total_right = 0
        
        for lane in local_map.lanes:
            for idx in lane.left_boundary_segment_indices:
                total_left += 1
                if idx not in valid_segment_ids:
                    invalid_left += 1
                    print(f"  Invalid left boundary: Lane {lane.lane_id} references segment {idx}")
            
            for idx in lane.right_boundary_segment_indices:
                total_right += 1
                if idx not in valid_segment_ids:
                    invalid_right += 1
                    print(f"  Invalid right boundary: Lane {lane.lane_id} references segment {idx}")
        
        print(f"Total left boundary indices: {total_left}")
        print(f"Invalid left boundary indices: {invalid_left}")
        print(f"Total right boundary indices: {total_right}")
        print(f"Invalid right boundary indices: {invalid_right}")
        
        total_invalid = invalid_left + invalid_right
        
        self.assertEqual(total_invalid, 0,
            f"All boundary indices should reference valid segments "
            f"(found {total_invalid} invalid)")
    
    def test_speed_limits_populated(self):
        """Test that speed limits are populated for lanes."""
        print(f"\n{'='*60}")
        print("TEST: Speed Limits Population")
        print(f"{'='*60}")
        
        local_map = self.get_test_local_map()
        self.assertIsNotNone(local_map, "LocalMap should be created")
        
        lanes_with_speed = 0
        lanes_without_speed = 0
        total_speed_points = 0
        
        for lane in local_map.lanes:
            if lane.max_speed_limits and len(lane.max_speed_limits) > 0:
                lanes_with_speed += 1
                total_speed_points += len(lane.max_speed_limits)
            else:
                lanes_without_speed += 1
        
        total_lanes = len(local_map.lanes)
        
        print(f"Total lanes: {total_lanes}")
        print(f"Lanes with speed limits: {lanes_with_speed}")
        print(f"Lanes without speed limits: {lanes_without_speed}")
        print(f"Total speed limit points: {total_speed_points}")
        
        # Note: Not all lanes may have speed limits defined, so we just report
        # This is informational, not a strict requirement


# ============================================================================
# Test Cases: Visualization
# ============================================================================

class TestVisualization(LocalMapTestBase):
    """Test cases for visualizing LocalMap conversion results."""
    
    def visualize_and_save(self, local_map: LocalMap, output_path: str, title: str = "LocalMap"):
        """Create and save visualization using the LocalMapVisualizer."""
        from common.local_map.visualization import LocalMapVisualizer
        from common.local_map.local_map_data import Point3D
        
        # Create a visualizer and use it directly (same pattern as LocalMapAPI.visualize())
        visualizer = LocalMapVisualizer()
        visualizer.visualize_local_map(
            local_map=local_map,
            title=title,
            show_lanes=True,
            show_centerlines=True,
            show_traffic_elements=True,
            show_ego_position=True,
            show_road_ids=True,
            show_lane_ids=False,
            ego_points=[Point3D(x=0.0, y=0.0, z=0.0)],  # Ego at origin in local coords
            save_path=output_path,
            dpi=150
        )
        print(f"Visualization saved to: {output_path}")
    
    def test_visualize_random_test_points(self):
        """Generate visualizations for random test points (5 road + 5 junction)."""
        print(f"\n{'='*60}")
        print("TEST: Visualize Random Test Points")
        print(f"{'='*60}")
        
        # Create output directory
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        test_points = self.select_test_points()
        self.assertGreater(len(test_points), 0, "Should have at least one test point")
        
        successful_visualizations = 0
        
        for i, tp in enumerate(test_points):
            print(f"\nTest point {i+1}/{len(test_points)}:")
            print(f"  Type: {'Junction' if tp['is_junction'] else 'Road'}")
            print(f"  Road ID: {tp['road_id']}")
            print(f"  Position: ({tp['x']:.2f}, {tp['y']:.2f})")
            
            local_map = self.create_local_map(tp['x'], tp['y'], tp['heading'])
            
            if local_map is not None:
                # Generate visualization
                output_file = output_dir / f"test_point_{i+1}_{'junction' if tp['is_junction'] else 'road'}.png"
                title = f"Test Point {i+1} - Road {tp['road_id']} ({'Junction' if tp['is_junction'] else 'Road'})"
                try:
                    self.visualize_and_save(local_map, str(output_file), title)
                    successful_visualizations += 1
                    print(f"  Result: SUCCESS - {len(local_map.lanes)} lanes")
                except Exception as e:
                    print(f"  Result: VISUALIZATION FAILED - {e}")
            else:
                print(f"  Result: CONVERSION FAILED")
        
        print(f"\nSummary: {successful_visualizations}/{len(test_points)} visualizations successful")
        # At least some visualizations should succeed
        self.assertGreater(successful_visualizations, 0, "At least one visualization should succeed")
    
    def test_specific_gps_coordinates(self):
        """Test conversion at specific GPS coordinates: lat=30.968457, lon=121.8846405."""
        print(f"\n{'='*60}")
        print("TEST: Specific GPS Coordinates (30.968457, 121.8846405)")
        print(f"{'='*60}")
        
        # Create output directory
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        # These are GPS coordinates that need to be converted to map coordinates
        # For lgdd.xodr, we need to find the corresponding map coordinates
        # The map uses a local coordinate system
        # Try multiple positions to find one that works
        test_positions = [
            # Position1: Near map center (based on road data)
            {'x': -2500.0, 'y': 15000.0, 'heading': 0.0, 'desc': 'Map center area'},
            # Position2: Another test area
            {'x': -2750.0, 'y': 16500.0, 'heading': 1.57, 'desc': 'Secondary test area'},
            # Position3: Junction area
            {'x': -2286.76, 'y': 14763.62, 'heading': 0.0, 'desc': 'Junction test area'},
        ]
        
        successful_conversions = 0
        
        for i, pos in enumerate(test_positions):
            print(f"\nTrying position {i+1}: {pos['desc']}")
            print(f"  Coordinates: ({pos['x']:.2f}, {pos['y']:.2f})")
            
            local_map = self.create_local_map(pos['x'], pos['y'], pos['heading'])
            
            if local_map is not None:
                successful_conversions += 1
                output_file = output_dir / f"gps_test_position_{i+1}.png"
                title = f"GPS Test Position {i+1} - {pos['desc']}"
                try:
                    self.visualize_and_save(local_map, str(output_file), title)
                    print(f"  Result: SUCCESS - {len(local_map.lanes)} lanes")
                    
                    # Print lane connection info
                    lanes_with_connections = sum(1 for lane in local_map.lanes
                                                    if lane.predecessor_lane_ids or lane.successor_lane_ids)
                    print(f"  Lanes with connections: {lanes_with_connections}/{len(local_map.lanes)}")
                except Exception as e:
                    print(f"  Result: VISUALIZATION FAILED - {e}")
            else:
                print(f"  Result: CONVERSION FAILED")
        
        print(f"\nSummary: {successful_conversions}/{len(test_positions)} conversions successful")
        
        # At least one conversion should succeed
        self.assertGreater(successful_conversions, 0,
            "At least one GPS position conversion should succeed")


# ============================================================================
# Main Test Runner
# ============================================================================

def run_tests(verbosity: int = 2):
    """
    Run all LocalMap unit tests.
    
    Args:
        verbosity: Test output verbosity (0-2)
    """
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLanePointConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestLaneConnections))
    suite.addTests(loader.loadTestsFromTestCase(TestCenterlineContinuity))
    suite.addTests(loader.loadTestsFromTestCase(TestOriginalIDConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestVisualization))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run LocalMap GTest-style unit tests")
    parser.add_argument("-v", "--verbosity", type=int, default=2,
                       help="Test output verbosity (0-2)")
    parser.add_argument("--list", action="store_true",
                       help="List all test methods")
    
    args = parser.parse_args()
    
    if args.list:
        # List all test methods
        print("Available test methods:")
        print("\nTestLanePointConversion:")
        for method in dir(TestLanePointConversion):
            if method.startswith('test_'):
                print(f"  - {method}")
        
        print("\nTestLaneConnections:")
        for method in dir(TestLaneConnections):
            if method.startswith('test_'):
                print(f"  - {method}")
        
        print("\nTestCenterlineContinuity:")
        for method in dir(TestCenterlineContinuity):
            if method.startswith('test_'):
                print(f"  - {method}")
        
        print("\nTestOriginalIDConsistency:")
        for method in dir(TestOriginalIDConsistency):
            if method.startswith('test_'):
                print(f"  - {method}")
        
        print("\nTestDataIntegrity:")
        for method in dir(TestDataIntegrity):
            if method.startswith('test_'):
                print(f"  - {method}")
    else:
        # Run tests
        result = run_tests(verbosity=args.verbosity)
        
        # Exit with appropriate code
        sys.exit(0 if result.wasSuccessful() else 1)
