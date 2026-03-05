"""
MapNode - 统一的地图处理节点

该模块提供统一的地图加载和局部地图生成接口。

Usage:
    from map_node import MapNode
    
    map_node = MapNode(config)
    if map_node.init():
        # 投影GPS坐标到地图坐标系
        map_x, map_y = map_node.project_gps(latitude, longitude)
        
        # 生成局部地图
        local_map = map_node.process(ego_state)
"""

import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING
from pyproj import Proj

from common.local_map.local_map_data import LocalMap, Pose, Point3D

if TYPE_CHECKING:
    from veh_status.veh_status import EgoVehicleState

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MapNode:
    """
    统一的地图处理节点
    
    负责：
    1. 加载高精度地图数据（支持OSM和XODR格式）
    2. 管理地图坐标系转换
    3. 根据自车GPS位置生成局部地图
    
    设计原则：
    - 地图数据仅在初始化时加载一次
    - 对外提供统一接口，隐藏内部格式差异
    - 内部处理GPS到地图坐标系的投影转换
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MapNode
        
        Args:
            config: 配置字典，需要包含map节点
        """
        self.config = config
        self.map_config = config.get('map', {})
        
        # 地图数据（仅加载一次）
        self._map_data: Optional[Any] = None
        self._map_format: str = self.map_config.get('format', 'xodr')
        self._map_loaded: bool = False
        
        # 坐标偏移配置
        offset_config = self.map_config.get('coordinate_offset', {})
        self._offset_x = offset_config.get('x', 0.0)
        self._offset_y = offset_config.get('y', 0.0)
        self._offset_z = offset_config.get('z', 0.0)
        self._rotation_rad = offset_config.get('headingz_rad', 0.0)
        
        # UTM投影器（用于GPS到UTM的转换）
        # 默认使用UTM zone 51N（上海地区）
        self._proj: Optional[Proj] = None
        self._utm_zone = 51
        
        # 局部地图构建器（延迟初始化）
        self._local_map_constructor = None
        
        # 默认配置
        self._map_range = 300.0  # 局部地图范围（米）
        self._eps = 0.5  # 采样分辨率（米）
        
        logger.info(f"MapNode初始化: format={self._map_format}")
    
    def init(self) -> bool:
        """
        初始化MapNode，加载地图数据
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("开始初始化MapNode...")
            
            # 1. 初始化UTM投影器
            self._proj = Proj(proj='utm', zone=self._utm_zone, ellps='WGS84')
            logger.info(f"UTM投影器初始化完成: zone={self._utm_zone}")
            
            # 2. 加载地图数据
            if not self._load_map():
                logger.error("地图加载失败")
                return False
            
            logger.info("MapNode初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"MapNode初始化失败: {e}")
            return False
    
    def _load_map(self) -> bool:
        """
        加载地图数据（内部方法）
        
        根据配置的地图格式，调用对应的加载器。
        地图数据仅加载一次，后续复用。
        
        Returns:
            bool: 加载是否成功
        """
        if self._map_loaded:
            logger.info("地图已加载，跳过重复加载")
            return True
        
        try:
            # 获取地图文件路径
            map_file = self.map_config.get('map_file', '')
            if not map_file:
                logger.error("未配置地图文件路径")
                return False
            
            # 构建完整路径（相对于configs目录）
            project_root = Path(__file__).parent.parent.parent
            full_path = project_root / 'configs' / map_file
            
            if not full_path.exists():
                logger.error(f"地图文件不存在: {full_path}")
                return False
            
            logger.info(f"加载地图: {full_path}")
            logger.info(f"地图格式: {self._map_format}")
            
            if self._map_format.lower() == 'xodr':
                return self._load_xodr_map(str(full_path))
            elif self._map_format.lower() == 'osm':
                return self._load_osm_map(str(full_path))
            else:
                logger.error(f"不支持的地图格式: {self._map_format}")
                return False
                
        except Exception as e:
            logger.error(f"地图加载异常: {e}")
            return False
    
    def _load_xodr_map(self, file_path: str) -> bool:
        """
        加载XODR格式地图
        
        Args:
            file_path: 地图文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            from map_node.maploader.loader_xodr import XODRLoader
            
            loader = XODRLoader()
            success = loader.load_map(file_path)
            
            if success:
                self._map_data = loader.get_map_data()
                self._map_loaded = True
                roads_count = len(self._map_data.get_roads()) if self._map_data else 0
                logger.info(f"XODR地图加载成功: {roads_count} 条道路")
                return True
            else:
                logger.error("XODR地图加载失败")
                return False
                
        except ImportError as e:
            logger.error(f"无法导入XODR加载器: {e}")
            return False
        except Exception as e:
            logger.error(f"XODR地图加载异常: {e}")
            return False
    
    def _load_osm_map(self, file_path: str) -> bool:
        """
        加载OSM格式地图
        
        Args:
            file_path: 地图文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            from map_node.maploader.loader import MapLoader
            
            loader = MapLoader()
            coordinate_type = self.map_config.get('coordinate_type', 'local')
            success = loader.load_map(file_path, coordinate_type=coordinate_type)
            
            if success:
                self._map_data = loader.get_map_data()
                self._map_loaded = True
                logger.info("OSM地图加载成功")
                return True
            else:
                logger.error("OSM地图加载失败")
                return False
                
        except ImportError as e:
            logger.error(f"无法导入OSM加载器: {e}")
            return False
        except Exception as e:
            logger.error(f"OSM地图加载异常: {e}")
            return False
    
    def project_gps(self, latitude: float, longitude: float) -> Tuple[float, float]:
        """
        将GPS坐标投影到地图坐标系
        
        转换流程：
        1. GPS (lat, lon) -> UTM (utm_x, utm_y)
        2. UTM -> 旋转（根据rotation_rad）
        3. 旋转后 -> 平移（根据offset_x, offset_y）
        
        Args:
            latitude: 纬度（度）
            longitude: 经度（度）
            
        Returns:
            Tuple[float, float]: 地图坐标系下的 (x, y)
        """
        if self._proj is None:
            logger.warning("投影器未初始化，返回原始坐标")
            return longitude, latitude
        
        # GPS -> UTM
        utm_x, utm_y = self._proj(longitude, latitude)
        
        # 旋转
        cos_r = math.cos(self._rotation_rad)
        sin_r = math.sin(self._rotation_rad)
        rotated_x = utm_x * cos_r - utm_y * sin_r
        rotated_y = utm_x * sin_r + utm_y * cos_r
        
        # 平移
        map_x = rotated_x + self._offset_x
        map_y = rotated_y + self._offset_y
        
        return map_x, map_y
    
    def project_gps_with_heading(
        self, 
        latitude: float, 
        longitude: float, 
        altitude: float,
        heading_deg: float
    ) -> Dict[str, float]:
        """
        将GPS坐标和航向角投影到地图坐标系
        
        Args:
            latitude: 纬度（度）
            longitude: 经度（度）
            altitude: 海拔高度（米）
            heading_deg: 航向角（度，GPS坐标系：0=北，顺时针）
            
        Returns:
            Dict[str, float]: 包含 x, y, z, heading（弧度）
        """
        map_x, map_y = self.project_gps(latitude, longitude)
        
        # 高度偏移
        map_z = altitude + self._offset_z
        
        # 航向角转换：GPS (0=北，顺时针) -> 地图 (0=东，逆时针)
        map_heading_deg = 90.0 - heading_deg
        # 归一化到 [0, 360)
        while map_heading_deg < 0:
            map_heading_deg += 360
        while map_heading_deg >= 360:
            map_heading_deg -= 360
        
        map_heading_rad = math.radians(map_heading_deg)
        
        return {
            'x': map_x,
            'y': map_y,
            'z': map_z,
            'heading': map_heading_rad
        }
    
    def process(self, ego_state: 'EgoVehicleState') -> Optional[LocalMap]:
        """
        根据自车状态生成局部地图
        
        Args:
            ego_state: 自车状态，包含GPS位置和航向
            
        Returns:
            LocalMap: 局部地图，如果生成失败则返回None
        """
        if not self._map_loaded:
            logger.error("地图未加载，无法生成局部地图")
            return None
        
        try:
            # 投影GPS到地图坐标系
            coord = self.project_gps_with_heading(
                ego_state.latitude,
                ego_state.longitude,
                ego_state.altitude if hasattr(ego_state, 'altitude') else 0.0,
                ego_state.heading
            )
            
            logger.debug(f"自车地图坐标: ({coord['x']:.2f}, {coord['y']:.2f}), "
                        f"航向: {math.degrees(coord['heading']):.1f}°")
            
            # 根据地图格式生成局部地图
            if self._map_format.lower() == 'xodr':
                return self._generate_xodr_local_map(coord, ego_state)
            elif self._map_format.lower() == 'osm':
                return self._generate_osm_local_map(coord, ego_state)
            else:
                logger.error(f"不支持的地图格式: {self._map_format}")
                return None
                
        except Exception as e:
            logger.error(f"生成局部地图失败: {e}")
            return None
    
    def _generate_xodr_local_map(
        self,
        coord: Dict[str, float],
        ego_state: 'EgoVehicleState'
    ) -> Optional[LocalMap]:
        """
        生成XODR格式的局部地图
        
        使用预加载的地图数据，避免重复加载地图文件。
        
        Args:
            coord: 地图坐标字典
            ego_state: 自车状态
            
        Returns:
            LocalMap: 局部地图
        """
        try:
            from map_node.localmap.xodrconvert.constructor import LocalMapConstructor as XODRLocalMapConstructor
            from map_node.localmap.xodrconvert.config_types import ConversionConfig
            
            # 创建转换配置
            config = ConversionConfig(
                eps=self._eps,
                map_range=self._map_range,
                include_junction_lanes=True,
                include_road_objects=True,
                include_traffic_signals=True,
                include_road_markings=True,
                ego_x=coord['x'],
                ego_y=coord['y'],
                ego_heading=coord['heading'],
                map_source_id="map_node"
            )
            
            # 延迟初始化或复用构造器
            if self._local_map_constructor is None:
                # 首次创建构造器
                self._local_map_constructor = XODRLocalMapConstructor(config=config)
                
                # 使用预加载的地图数据，避免重复加载
                if not self._local_map_constructor.set_map_data(self._map_data):
                    logger.error("设置地图数据失败")
                    self._local_map_constructor = None
                    return None
            else:
                # 复用构造器，仅更新配置（不重新加载地图）
                self._local_map_constructor.update_config(config)
            
            # 直接调用construct_local_map()，而不是convert()
            # convert()会重新加载地图，而construct_local_map()使用已加载的数据
            result = self._local_map_constructor.construct_local_map()
            
            if result.success:
                logger.debug(f"局部地图生成成功: {len(result.data.lanes) if result.data else 0} 条车道")
                return result.data
            else:
                logger.error(f"局部地图生成失败: {result.errors}")
                return None
                
        except ImportError as e:
            logger.error(f"无法导入XODR转换模块: {e}")
            return None
        except Exception as e:
            logger.error(f"XODR局部地图生成异常: {e}")
            return None
    
    def _generate_osm_local_map(
        self, 
        coord: Dict[str, float], 
        ego_state: 'EgoVehicleState'
    ) -> Optional[LocalMap]:
        """
        生成OSM格式的局部地图
        
        Args:
            coord: 地图坐标字典
            ego_state: 自车状态
            
        Returns:
            LocalMap: 局部地图
        """
        try:
            from map_node.localmap.osmconvert.local_map_construct.constructor import LocalMapConstructor as OSMLocalMapConstructor
            from map_node.localmap.osmconvert.local_map_construct.config_types import LocalMapConstructConfig
            from map_node.localmap.osmconvert.mapapi.api import MapAPI
            
            # 创建配置
            config = LocalMapConstructConfig(
                map_range=int(self._map_range),
                coordinate_precision=0.01
            )
            
            # 创建构造器
            constructor = OSMLocalMapConstructor(config)
            
            # 创建MapAPI
            map_api = MapAPI(self._map_data)
            
            # 创建Pose
            ego_pose = Pose(
                position=Point3D(x=coord['x'], y=coord['y'], z=coord['z']),
                heading=coord['heading']
            )
            
            # 构建局部地图
            result = constructor.construct_local_map(map_api, ego_pose)
            
            if result.success:
                logger.debug(f"局部地图生成成功")
                return result.local_map
            else:
                logger.error(f"局部地图生成失败")
                return None
                
        except ImportError as e:
            logger.error(f"无法导入OSM转换模块: {e}")
            return None
        except Exception as e:
            logger.error(f"OSM局部地图生成异常: {e}")
            return None
    
    def is_loaded(self) -> bool:
        """
        检查地图是否已加载
        
        Returns:
            bool: 地图是否已加载
        """
        return self._map_loaded
    
    def get_map_info(self) -> Dict[str, Any]:
        """
        获取地图信息
        
        Returns:
            Dict[str, Any]: 地图信息字典
        """
        return {
            'format': self._map_format,
            'loaded': self._map_loaded,
            'map_range': self._map_range,
            'offset': {
                'x': self._offset_x,
                'y': self._offset_y,
                'z': self._offset_z,
                'rotation_rad': self._rotation_rad
            }
        }
    
    def set_map_range(self, map_range: float) -> None:
        """
        设置局部地图范围
        
        Args:
            map_range: 范围（米）
        """
        self._map_range = map_range
        logger.debug(f"局部地图范围设置为: {map_range}m")
    
    def set_eps(self, eps: float) -> None:
        """
        设置采样分辨率
        
        Args:
            eps: 分辨率（米）
        """
        self._eps = eps
        logger.debug(f"采样分辨率设置为: {eps}m")


# 导出
__all__ = ['MapNode']
