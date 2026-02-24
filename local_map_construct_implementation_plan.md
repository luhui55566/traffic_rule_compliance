# LocalMapConstruct 实现计划

## 概述

本文档详细描述了LocalMapConstruct模块的实现计划，包括核心类设计、接口定义和集成方案。

## 1. 模块结构

```
src/map_node/local_map_construct/
├── __init__.py
├── constructor.py          # LocalMapConstructor主类
├── converter.py            # MapConverter类
├── transformer.py          # CoordinateTransformer类
├── cache.py                # CacheManager类
├── builder.py              # LocalMapBuilder类
└── types.py                # 类型定义
```

## 2. 核心类设计

### 2.1 LocalMapConstructor (constructor.py)

```python
class LocalMapConstructor:
    """LocalMap构造器主类，负责从MapAPI数据构建LocalMap"""
    
    def __init__(self, config: LocalMapConstructConfig):
        self.config = config
        self.converter = MapConverter()
        self.transformer = CoordinateTransformer()
        self.cache_manager = CacheManager(config.cache_config)
        self.builder = LocalMapBuilder()
        
    def construct_local_map(self, 
                          map_api: MapAPI, 
                          ego_pose: Pose, 
                          map_range: float = 200.0) -> LocalMap:
        """构建局部地图"""
        
    def update_local_map(self, 
                        local_map: LocalMap, 
                        map_api: MapAPI, 
                        ego_pose: Pose) -> LocalMap:
        """更新局部地图"""
```

### 2.2 MapConverter (converter.py)

```python
class MapConverter:
    """地图格式转换器，将MapAPI数据转换为LocalMap数据结构"""
    
    def convert_lanelet_to_lane(self, lanelet: Lanelet) -> Lane:
        """将Lanelet转换为Lane"""
        
    def convert_traffic_signs(self, traffic_signs: List[TrafficSign]) -> List[TrafficSign]:
        """转换交通标志"""
        
    def convert_traffic_lights(self, position: Position, radius: float) -> List[TrafficLight]:
        """转换交通信号灯"""
```

### 2.3 CoordinateTransformer (transformer.py)

```python
class CoordinateTransformer:
    """坐标转换器，处理全局坐标和局部坐标之间的转换"""
    
    def global_to_local(self, global_pos: Position, origin: Position) -> Point3D:
        """全局坐标转局部坐标"""
        
    def local_to_global(self, local_pos: Point3D, origin: Position) -> Position:
        """局部坐标转全局坐标"""
```

### 2.4 CacheManager (cache.py)

```python
class CacheManager:
    """缓存管理器，管理LocalMap缓存"""
    
    def get_cached_map(self, cache_key: str) -> Optional[LocalMap]:
        """获取缓存的地图"""
        
    def cache_map(self, cache_key: str, local_map: LocalMap) -> None:
        """缓存地图"""
        
    def is_cache_valid(self, cache_key: str, ego_pose: Pose, tolerance: float = 10.0) -> bool:
        """检查缓存是否有效"""
```

### 2.5 LocalMapBuilder (builder.py)

```python
class LocalMapBuilder:
    """LocalMap构建器，负责组装LocalMap数据结构"""
    
    def build_local_map(self, 
                       ego_pose: Pose, 
                       map_range: float,
                       lanes: List[Lane],
                       traffic_signs: List[TrafficSign],
                       traffic_lights: List[TrafficLight]) -> LocalMap:
        """构建LocalMap"""
        
    def update_metadata(self, local_map: LocalMap, ego_pose: Pose) -> None:
        """更新地图元数据"""
```

## 3. 集成方案

### 3.1 修改TrafficRuleVerificationSystem

```python
class TrafficRuleVerificationSystem:
    def __init__(self, config: TrafficRuleConfig):
        # 现有代码...
        self.local_map_constructor: Optional[LocalMapConstructor] = None
        self.local_map_api: Optional[LocalMapAPI] = None
        self.current_local_map: Optional[LocalMap] = None
        
    def initialize(self) -> bool:
        """初始化系统"""
        # 现有代码...
        
        # Step 4: Initialize LocalMapConstructor
        if not self._initialize_local_map_constructor():
            logger.error("Failed to initialize LocalMapConstructor")
            return False
            
        # Step 5: Initialize LocalMapAPI
        if not self._initialize_local_map_api():
            logger.error("Failed to initialize LocalMapAPI")
            return False
            
        self._initialized = True
        return True
        
    def _initialize_local_map_constructor(self) -> bool:
        """初始化LocalMapConstructor"""
        try:
            from map_node.local_map_construct.constructor import LocalMapConstructor
            from map_node.local_map_construct.types import LocalMapConstructConfig
            
            # 创建配置
            config = LocalMapConstructConfig(
                map_range=200.0,
                update_threshold=50.0,
                cache_enabled=True,
                max_cache_size=10
            )
            
            # 初始化构造器
            self.local_map_constructor = LocalMapConstructor(config)
            logger.info("LocalMapConstructor initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing LocalMapConstructor: {e}")
            return False
            
    def _initialize_local_map_api(self) -> None:
        """初始化LocalMapAPI"""
        # 创建初始局部地图
        ego_pose = Pose(
            x=0.0, y=0.0, z=0.0,
            roll=0.0, pitch=0.0, yaw=0.0
        )
        
        self.current_local_map = self.local_map_constructor.construct_local_map(
            self.map_manager.api, ego_pose
        )
        
        # 初始化LocalMapAPI
        from common.local_map.local_map_api import LocalMapAPI
        self.local_map_api = LocalMapAPI(self.current_local_map)
        
        logger.info("LocalMapAPI initialized")
```

### 3.2 修改环境数据获取方法

```python
def _get_environment_data(self, state: VehicleState) -> Dict[str, Any]:
    """获取环境数据，使用LocalMapAPI"""
    try:
        # 更新局部地图（如果需要）
        ego_pose = Pose(
            x=state.local_x if state.local_x is not None else 0.0,
            y=state.local_y if state.local_y is not None else 0.0,
            z=state.altitude if state.altitude is not None else 0.0,
            roll=0.0, pitch=0.0, yaw=state.heading if state.heading is not None else 0.0
        )
        
        # 检查是否需要更新局部地图
        if self._should_update_local_map(ego_pose):
            self.current_local_map = self.local_map_constructor.update_local_map(
                self.current_local_map, self.map_manager.api, ego_pose
            )
            self.local_map_api.update_local_map(self.current_local_map)
        
        # 使用LocalMapAPI获取环境数据
        current_lane = self.local_map_api.find_nearest_lane(
            Point3D(x=ego_pose.x, y=ego_pose.y, z=ego_pose.z)
        )
        
        speed_limit = None
        if current_lane:
            speed_limit = self.local_map_api.get_lane_speed_limit(
                current_lane[0].lane_id,
                Point3D(x=ego_pose.x, y=ego_pose.y, z=ego_pose.z)
            )
        
        # 获取附近的交通标志
        nearby_traffic_signs = self.local_map_api.get_traffic_signs_within_distance(
            Point3D(x=ego_pose.x, y=ego_pose.y, z=ego_pose.z),
            distance=100.0
        )
        
        # 获取附近的交通信号灯
        nearby_traffic_lights = self.local_map_api.get_traffic_lights_within_distance(
            Point3D(x=ego_pose.x, y=ego_pose.y, z=ego_pose.z),
            distance=100.0
        )
        
        return {
            'current_lane': current_lane[0] if current_lane else None,
            'speed_limit': speed_limit,
            'nearby_traffic_signs': nearby_traffic_signs,
            'nearby_traffic_lights': nearby_traffic_lights,
            'ego_pose': ego_pose
        }
        
    except Exception as e:
        logger.error(f"Error getting environment data: {e}")
        return {}
        
def _should_update_local_map(self, ego_pose: Pose) -> bool:
    """检查是否需要更新局部地图"""
    if not self.current_local_map or not self.current_local_map.metadata:
        return True
        
    # 计算与上次更新位置的距离
    last_pose = self.current_local_map.metadata.ego_pose
    distance = ((ego_pose.x - last_pose.x) ** 2 + 
                (ego_pose.y - last_pose.y) ** 2) ** 0.5
    
    # 如果距离超过阈值，需要更新
    return distance > self.local_map_constructor.config.update_threshold
```

## 4. 配置类定义

### 4.1 LocalMapConstructConfig (types.py)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    max_size: int = 10
    ttl_seconds: int = 300

@dataclass
class LocalMapConstructConfig:
    """LocalMapConstruct配置"""
    map_range: float = 200.0          # 局部地图范围（米）
    update_threshold: float = 50.0     # 更新阈值（米）
    cache_config: CacheConfig = None   # 缓存配置
    
    def __post_init__(self):
        if self.cache_config is None:
            self.cache_config = CacheConfig()
```

## 5. 实现步骤

1. **创建基础模块结构**
   - 创建local_map_construct目录
   - 创建__init__.py和types.py

2. **实现核心类**
   - 实现CoordinateTransformer
   - 实现MapConverter
   - 实现CacheManager
   - 实现LocalMapBuilder
   - 实现LocalMapConstructor

3. **修改TrafficRuleVerificationSystem**
   - 添加LocalMapConstructor初始化
   - 修改环境数据获取方法
   - 添加局部地图更新逻辑

4. **测试和验证**
   - 创建单元测试
   - 集成测试
   - 性能测试

## 6. 性能考虑

1. **缓存策略**
   - 基于位置的缓存
   - LRU淘汰策略
   - 缓存有效期管理

2. **增量更新**
   - 只更新变化的区域
   - 保留不变的地图元素

3. **异步处理**
   - 异步地图更新
   - 后台预加载

## 7. 错误处理

1. **数据转换错误**
   - 格式不匹配处理
   - 缺失数据处理

2. **坐标转换错误**
   - 坐标系不匹配
   - 转换失败处理

3. **缓存错误**
   - 缓存失效处理
   - 内存不足处理

这个实现计划提供了完整的LocalMapConstruct模块设计方案，包括详细的类定义、集成方案和实现步骤。