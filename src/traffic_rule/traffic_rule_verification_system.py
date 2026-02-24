"""
Traffic rule verification system module.

This module provides the TrafficRuleVerificationSystem class that
integrates map loading, map API, and traffic rule checking.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from map_node.map_common.base import Position
from map_node.maploader.loader import MapLoader
from map_node.maploader.utils import UtmProjectorWrapper
from lanelet2.io import Origin

from .config import TrafficRuleConfig
from .types import VehicleState, Violation, ViolationReport
from .rules import (
    TrafficRuleBase,
    SpeedLimitRule,
    ContinuousLaneChangeRule,
    FishboneRule,
    ConstructionSignRule,
    WrongWayRule
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrafficRuleVerificationSystem:
    """
    Main entry point for traffic rule compliance verification.
    
    This class integrates:
    - Map loading (via MapLoader)
    - Map API (via MapManager)
    - Traffic rule checking (via rule implementations)
    
    Usage:
        # Initialize with configuration
        config = TrafficRuleConfig.load_from_file('config.yaml')
        system = TrafficRuleVerificationSystem(config)
        
        # Process vehicle states
        states = [VehicleState(...), ...]
        report = system.verify_states(states)
        
        # Get results
        print(report.get_summary())
    """
    
    def __init__(self, config: TrafficRuleConfig):
        """
        Initialize traffic rule verification system.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.map_loader: Optional[MapLoader] = None
        self.map_manager = None
        self.rules: List[TrafficRuleBase] = []
        self.state_history: List[VehicleState] = []
        self._initialized = False
        
        logger.info("TrafficRuleVerificationSystem initialized")
    
    def initialize(self) -> bool:
        """
        Initialize system.
        
        This loads map and initializes all components.
        
        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            logger.info("Initializing TrafficRuleVerificationSystem...")
            
            # Step 1: Load map
            if not self._load_map():
                logger.error("Failed to load map")
                return False
            
            # Step 2: Initialize map manager
            if not self._initialize_map_manager():
                logger.error("Failed to initialize map manager")
                return False
            
            # Step 3: Initialize traffic rules
            self._initialize_rules()
            
            self._initialized = True
            logger.info("TrafficRuleVerificationSystem initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            return False
    
    def _load_map(self) -> bool:
        """
        Load map from configuration.
        
        Returns:
            True if map loaded successfully
        """
        try:
            # Get map file path (resolved relative to config file)
            map_file = self.config.get_map_file_path()
            
            # Check if file exists
            if not Path(map_file).exists():
                logger.error(f"Map file not found: {map_file}")
                return False
            
            # Get coordinate type from config
            coordinate_type = self.config.map.coordinate_type
            logger.info(f"Loading map with coordinate_type: {coordinate_type}")
            
            # Load map with coordinate_type parameter
            # The loader will handle the appropriate loading method internally
            self.map_loader = MapLoader()
            success = self.map_loader.load_map(
                map_file,
                coordinate_type=coordinate_type,
                projector=None  # Projector not used during loading
            )
            
            if success:
                map_info = self.map_loader.get_map_info()
                logger.info(f"Map loaded: {map_info}")
            else:
                logger.error("Failed to load map")
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading map: {e}")
            return False
    
    def _initialize_map_manager(self) -> bool:
        """
        Initialize map manager with loaded map data.
        
        Returns:
            True if map manager initialized successfully
        """
        try:
            from map_node.mapapi.manager import MapManager
            
            # Get map data from loader
            map_data = self.map_loader.get_map_data()
            
            # Initialize map manager (singleton)
            self.map_manager = MapManager()
            self.map_manager.initialize(map_data)
            
            # Configure cache
            self.map_manager.enable_cache(self.config.cache_enabled)
            
            logger.info("Map manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing map manager: {e}")
            return False
    
    def _initialize_rules(self) -> None:
        """Initialize all traffic rules based on configuration."""
        self.rules = []
        
        # Speed limit rule
        if self.config.speed_limit.enabled:
            self.rules.append(SpeedLimitRule(
                tolerance=self.config.speed_limit.tolerance,
                enabled=True
            ))
            logger.info("Speed limit rule enabled")
        
        # Continuous lane change rule
        if self.config.continuous_lane_change.enabled:
            self.rules.append(ContinuousLaneChangeRule(
                time_window=self.config.continuous_lane_change.time_window,
                max_changes=self.config.continuous_lane_change.max_changes,
                enabled=True
            ))
            logger.info("Continuous lane change rule enabled")
        
        # Fishbone rule
        if self.config.fishbone.enabled:
            self.rules.append(FishboneRule(
                required_deceleration=self.config.fishbone.required_deceleration,
                trigger_distance=self.config.fishbone.trigger_distance,
                max_speed_to_trigger=self.config.fishbone.max_speed_to_trigger,
                enabled=True
            ))
            logger.info("Fishbone rule enabled")
        
        # Construction sign rule
        if self.config.construction_sign.enabled:
            self.rules.append(ConstructionSignRule(
                required_deceleration=self.config.construction_sign.required_deceleration,
                distance_threshold=self.config.construction_sign.distance_threshold,
                enabled=True
            ))
            logger.info("Construction sign rule enabled")
        
        # Wrong way rule
        if self.config.wrong_way.enabled:
            self.rules.append(WrongWayRule(
                heading_tolerance=self.config.wrong_way.heading_tolerance,
                enabled=True
            ))
            logger.info("Wrong way rule enabled")
        
        logger.info(f"Total rules initialized: {len(self.rules)}")
    
    def verify_state(self, state: VehicleState) -> Optional[Violation]:
        """
        Verify a single vehicle state against all traffic rules.
        
        Args:
            state: Vehicle state to verify
            
        Returns:
            First violation found, or None if no violations
        """
        if not self._initialized:
            logger.warning("System not initialized. Call initialize() first.")
            return None
        
        # Update state history
        self.state_history.append(state)
        
        # Trim history to configured window
        window_start = state.timestamp - self.config.history_window
        self.state_history = [
            s for s in self.state_history 
            if s.timestamp >= window_start
        ]
        
        # Get environment data
        environment_data = self._get_environment_data(state)
        
        # Check all rules
        for rule in self.rules:
            if rule.is_enabled():
                violation = rule.check(state, self.state_history, environment_data)
                if violation is not None:
                    return violation
        
        return None
    
    def verify_states(self, states: List[VehicleState]) -> ViolationReport:
        """
        Verify multiple vehicle states against all traffic rules.
        
        Args:
            states: List of vehicle states to verify
            
        Returns:
            Violation report with all detected violations
        """
        if not self._initialized:
            logger.warning("System not initialized. Call initialize() first.")
            return ViolationReport(
                timestamp=datetime.now(),
                vehicle_states=states,
                violations=[]
            )
        
        logger.info(f"Verifying {len(states)} vehicle states...")
        
        # Clear history for new verification session
        self.state_history = []
        
        # Process each state
        all_violations = []
        for state in states:
            violation = self.verify_state(state)
            if violation is not None:
                all_violations.append(violation)
        
        # Generate report
        report = ViolationReport(
            timestamp=datetime.now(),
            vehicle_states=states,
            violations=all_violations
        )
        
        logger.info(f"Verification complete: {len(all_violations)} violations detected")
        return report
    
    def _get_environment_data(self, state: VehicleState) -> Dict[str, Any]:
        """
        Get environment data for a vehicle state.
        
        Args:
            state: Vehicle state
            
        Returns:
            Dictionary with environment data
        """
        # Handle both local and global coordinates
        if state.use_local_coords:
            # For local coordinates, use local_x, local_y, local_heading
            # Note: MapManager may need to be extended to support local coordinates
            # For now, we'll use the local coordinates directly
            position = Position(
                latitude=state.local_x if state.local_x is not None else 0.0,
                longitude=state.local_y if state.local_y is not None else 0.0,
                altitude=state.altitude
            )
        else:
            # For global coordinates, use latitude, longitude, heading
            position = Position(
                latitude=state.latitude if state.latitude is not None else 0.0,
                longitude=state.longitude if state.longitude is not None else 0.0,
                altitude=state.altitude
            )
        
        # Get current lanelet
        current_lanelet = self.map_manager.get_lanelet(position)
        
        # Get speed limit
        speed_limit = self.map_manager.get_speed_limit(position)
        
        # Get nearby fishbone lines (pass use_local_coords parameter)
        fishbones = self.map_manager.query_fishbone_lines(position, radius=100.0, use_local_coords=state.use_local_coords)
        nearby_fishbones = [
            {
                'id': fb.id,
                'latitude': fb.position.latitude,
                'longitude': fb.position.longitude,
                'direction': fb.direction,
                'length': fb.length
            }
            for fb in fishbones
        ]
        
        # Get nearby construction signs (pass use_local_coords parameter)
        construction_signs = self.map_manager.query_construction_signs(position, radius=200.0, use_local_coords=state.use_local_coords)
        nearby_construction_signs = [
            {
                'id': cs.id,
                'latitude': cs.position.latitude,
                'longitude': cs.position.longitude,
                'direction': cs.direction,
                'distance_threshold': cs.distance_threshold
            }
            for cs in construction_signs
        ]
        
        return {
            'current_lanelet': current_lanelet,
            'speed_limit': speed_limit,
            'nearby_fishbones': nearby_fishbones,
            'nearby_construction_signs': nearby_construction_signs
        }
    
    def add_rule(self, rule: TrafficRuleBase) -> None:
        """
        Add a custom traffic rule.
        
        Args:
            rule: Traffic rule to add
        """
        self.rules.append(rule)
        logger.info(f"Added custom rule: {rule.rule_name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a traffic rule by ID.
        
        Args:
            rule_id: Rule ID to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                self.rules.pop(i)
                logger.info(f"Removed rule: {rule_id}")
                return True
        return False
    
    def list_rules(self) -> List[str]:
        """
        List all registered rule IDs.
        
        Returns:
            List of rule IDs
        """
        return [rule.rule_id for rule in self.rules]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get system status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'initialized': self._initialized,
            'map_loaded': self.map_loader.is_loaded() if self.map_loader else False,
            'rules_enabled': len([r for r in self.rules if r.is_enabled()]),
            'rules_total': len(self.rules),
            'history_size': len(self.state_history),
            'map_info': self.map_loader.get_map_info().to_dict() if self.map_loader else None
        }
    
    def reset(self) -> None:
        """Reset system state."""
        self.state_history = []
        logger.info("System state reset")
    
    def shutdown(self) -> None:
        """Shutdown system and release resources."""
        if self.map_manager:
            self.map_manager.reset()
        self._initialized = False
        logger.info("TrafficRuleVerificationSystem shutdown")
