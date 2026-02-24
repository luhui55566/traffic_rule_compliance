"""
Configuration management for traffic rule compliance verification system.
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MapConfig:
    """Map configuration."""
    osm_file: str = "configs/maps/Town10HD.osm"
    coordinate_type: str = "local"  # "local" or "geographic"
    origin_latitude: float = 0.0
    origin_longitude: float = 0.0
    coordinate_system: str = "WGS84"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MapConfig':
        """Create MapConfig from dictionary."""
        origin = data.get('origin', {})
        return cls(
            osm_file=data.get('osm_file', 'configs/maps/Town10HD.osm'),
            coordinate_type=data.get('coordinate_type', 'local'),
            origin_latitude=origin.get('latitude', 0.0),
            origin_longitude=origin.get('longitude', 0.0),
            coordinate_system=data.get('coordinate_system', 'WGS84')
        )


@dataclass
class SpeedLimitRuleConfig:
    """Speed limit rule configuration."""
    enabled: bool = True
    tolerance: float = 5.0  # km/h tolerance
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpeedLimitRuleConfig':
        """Create SpeedLimitRuleConfig from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            tolerance=data.get('tolerance', 5.0)
        )


@dataclass
class ContinuousLaneChangeRuleConfig:
    """Continuous lane change rule configuration."""
    enabled: bool = True
    time_window: float = 10.0  # seconds
    max_changes: int = 2
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContinuousLaneChangeRuleConfig':
        """Create ContinuousLaneChangeRuleConfig from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            time_window=data.get('time_window', 10.0),
            max_changes=data.get('max_changes', 2)
        )


@dataclass
class FishboneRuleConfig:
    """Fishbone line deceleration rule configuration."""
    enabled: bool = True
    required_deceleration: float = 2.0  # m/s²
    trigger_distance: float = 100.0  # meters
    max_speed_to_trigger: float = 40.0  # km/h
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FishboneRuleConfig':
        """Create FishboneRuleConfig from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            required_deceleration=data.get('required_deceleration', 2.0),
            trigger_distance=data.get('trigger_distance', 100.0),
            max_speed_to_trigger=data.get('max_speed_to_trigger', 40.0)
        )


@dataclass
class ConstructionSignRuleConfig:
    """Construction sign deceleration rule configuration."""
    enabled: bool = True
    required_deceleration: float = 1.5  # m/s²
    distance_threshold: float = 200.0  # meters
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConstructionSignRuleConfig':
        """Create ConstructionSignRuleConfig from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            required_deceleration=data.get('required_deceleration', 1.5),
            distance_threshold=data.get('distance_threshold', 200.0)
        )


@dataclass
class WrongWayRuleConfig:
    """Wrong way driving rule configuration."""
    enabled: bool = True
    heading_tolerance: float = 45.0  # degrees
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WrongWayRuleConfig':
        """Create WrongWayRuleConfig from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            heading_tolerance=data.get('heading_tolerance', 45.0)
        )


@dataclass
class TrafficRuleConfig:
    """
    Main configuration class for traffic rule compliance verification system.
    
    This class manages all configuration parameters including map settings,
    rule configurations, and system settings.
    """
    # Map configuration
    map: MapConfig = field(default_factory=MapConfig)
    
    # Rule configurations
    speed_limit: SpeedLimitRuleConfig = field(default_factory=SpeedLimitRuleConfig)
    continuous_lane_change: ContinuousLaneChangeRuleConfig = field(
        default_factory=ContinuousLaneChangeRuleConfig)
    fishbone: FishboneRuleConfig = field(default_factory=FishboneRuleConfig)
    construction_sign: ConstructionSignRuleConfig = field(
        default_factory=ConstructionSignRuleConfig)
    wrong_way: WrongWayRuleConfig = field(default_factory=WrongWayRuleConfig)
    
    # System configuration
    history_window: float = 10.0  # seconds of vehicle state history to keep
    cache_enabled: bool = True
    
    # Config file path (for resolving relative paths)
    config_file_path: Optional[str] = None
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'TrafficRuleConfig':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            TrafficRuleConfig instance
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        config = cls.from_dict(data)
        config.config_file_path = os.path.abspath(config_path)
        return config
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrafficRuleConfig':
        """
        Create TrafficRuleConfig from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            TrafficRuleConfig instance
        """
        return cls(
            map=MapConfig.from_dict(data.get('map', {})),
            speed_limit=SpeedLimitRuleConfig.from_dict(
                data.get('speed_limit', {})),
            continuous_lane_change=ContinuousLaneChangeRuleConfig.from_dict(
                data.get('continuous_lane_change', {})),
            fishbone=FishboneRuleConfig.from_dict(data.get('fishbone', {})),
            construction_sign=ConstructionSignRuleConfig.from_dict(
                data.get('construction_sign', {})),
            wrong_way=WrongWayRuleConfig.from_dict(data.get('wrong_way', {})),
            history_window=data.get('history_window', 10.0),
            cache_enabled=data.get('cache_enabled', True),
            config_file_path=None
        )
    
    def get_map_file_path(self) -> str:
        """
        Get the absolute path to the map file.
        
        Returns:
            Absolute path to the map file
        """
        map_file = self.map.osm_file
        if os.path.isabs(map_file):
            return map_file
        
        # Resolve relative to config file directory
        if self.config_file_path:
            config_dir = os.path.dirname(self.config_file_path)
            return os.path.abspath(os.path.join(config_dir, map_file))
        
        # Fallback to current directory
        return os.path.abspath(map_file)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'map': {
                'osm_file': self.map.osm_file,
                'coordinate_type': self.map.coordinate_type,
                'origin': {
                    'latitude': self.map.origin_latitude,
                    'longitude': self.map.origin_longitude
                },
                'coordinate_system': self.map.coordinate_system
            },
            'speed_limit': {
                'enabled': self.speed_limit.enabled,
                'tolerance': self.speed_limit.tolerance
            },
            'continuous_lane_change': {
                'enabled': self.continuous_lane_change.enabled,
                'time_window': self.continuous_lane_change.time_window,
                'max_changes': self.continuous_lane_change.max_changes
            },
            'fishbone': {
                'enabled': self.fishbone.enabled,
                'required_deceleration': self.fishbone.required_deceleration,
                'trigger_distance': self.fishbone.trigger_distance,
                'max_speed_to_trigger': self.fishbone.max_speed_to_trigger
            },
            'construction_sign': {
                'enabled': self.construction_sign.enabled,
                'required_deceleration': self.construction_sign.required_deceleration,
                'distance_threshold': self.construction_sign.distance_threshold
            },
            'wrong_way': {
                'enabled': self.wrong_way.enabled,
                'heading_tolerance': self.wrong_way.heading_tolerance
            },
            'history_window': self.history_window,
            'cache_enabled': self.cache_enabled
        }
    
    def save_to_file(self, config_path: str) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config_path: Path to save configuration file
        """
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
