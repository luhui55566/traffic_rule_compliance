# LocalMap模块使用指南
# LocalMap Module Usage Guide

## 概述 / Overview

LocalMap模块提供了统一的局部地图数据结构和API接口，支持map_node和traffic_rule模块使用。

The LocalMap module provides unified local map data structures and API interfaces, supporting both map_node and traffic_rule modules.

## 目录结构 / Directory Structure

```
src/common/local_map/
├── __init__.py              # 模块导出 / Module exports
├── local_map_data.py         # 数据结构定义 / Data structure definitions
├── local_map_api.py          # API接口实现 / API interface implementation
├── example_usage.py          # 使用示例 / Usage examples
├── test_local_map.py         # 基本功能测试 / Basic functionality tests
└── README.md               # 使用指南 / Usage guide
```

## 快速开始 / Quick Start

### 1. 导入模块 / Import Module

```python
from local_map import (
    LocalMap, Lane, TrafficLight, TrafficSign,
    Point3D, Pose, LaneType, TrafficLightColor,
    create_empty_local_map, LocalMapAPI
)
```

### 2. 创建局部地图 / Create Local Map

```python
# 创建自车位姿
ego_pose = Pose(
    position=Point3D(x=0.0, y=0.0, z=0.0),
    heading=0.0,
    pitch=0.0,
    roll=0.0
)

# 创建空的局部地图
local_map = create_empty_local_map(ego_pose, 200.0)
```

### 3. 使用API查询 / Use API for Queries

```python
# 创建API实例
api = LocalMapAPI(local_map)

# 查询车道
lane = api.get_lane_by_id(1)
if lane:
    print(f"Found lane: {lane.lane_id}, type: {lane.lane_type.name}")

# 查询交通信号灯
lights = api.get_traffic_lights_by_color(TrafficLightColor.RED)
print(f"Found {len(lights)} red lights")

# 几何计算
point = Point3D(x=10.0, y=5.0, z=0.0)
distance = api.calculate_distance_to_lane(point, 1)
if distance is not None:
    print(f"Distance to lane 1: {distance:.2f} meters")
```

## 主要功能 / Main Features

### 数据结构 / Data Structures

- **LocalMap**: 局部地图主结构
- **Lane**: 车道信息
- **TrafficLight**: 交通信号灯
- **TrafficSign**: 交通标志
- **LaneBoundarySegment**: 车道边界分段
- **SpeedLimitSegment**: 限速分段

### API功能 / API Features

- **查询功能**: 根据ID、类型、范围查询元素
- **几何计算**: 距离计算、最近点查找
- **数据验证**: 验证数据完整性
- **统计信息**: 获取地图统计信息

## 使用示例 / Usage Examples

### 车道查询 / Lane Queries

```python
# 根据ID获取车道
lane = api.get_lane_by_id(1)

# 根据类型获取车道
driving_lanes = api.get_lanes_by_type(LaneType.DRIVING)

# 获取相邻车道
left_lane, right_lane = api.get_adjacent_lanes(1)

# 获取连接车道
predecessors, successors = api.get_connected_lanes(1)
```

### 交通设施查询 / Traffic Facility Queries

```python
# 交通信号灯查询
red_lights = api.get_traffic_lights_by_color(TrafficLightColor.RED)
lights_in_range = api.get_traffic_lights_in_range((-50, 50), (-25, 25))

# 交通标志查询
speed_signs = api.get_traffic_signs_by_type(TrafficSignType.SPEED_LIMIT)
all_speed_signs = api.get_speed_limit_signs()
```

### 几何计算 / Geometry Calculations

```python
# 计算点到车道的距离
distance = api.calculate_distance_to_lane(point, lane_id)

# 查找最近的车道
nearest_result = api.find_nearest_lane(point)
if nearest_result:
    nearest_lane, nearest_distance = nearest_result

# 检查点是否在车道内
is_in_lane = api.is_point_in_lane(point, lane_id, tolerance=2.0)
```

## 测试 / Testing

运行基本功能测试：

Run basic functionality tests:

```bash
cd src/common/local_map
python test_local_map.py
```

运行使用示例：

Run usage examples:

```bash
cd src/common/local_map
python example_usage.py
```

## 扩展指南 / Extension Guide

### 添加新的数据结构 / Add New Data Structures

1. 在 `local_map_data.py` 中定义新的数据类
2. 在 `__init__.py` 中导出新的类
3. 在 `local_map_api.py` 中添加相应的查询方法

### 添加新的查询方法 / Add New Query Methods

1. 在 `LocalMapAPI` 类中添加新方法
2. 在构造函数中构建相应的缓存
3. 在测试文件中添加测试用例

## 注意事项 / Notes

1. **坐标系**: 所有坐标都在自车局部坐标系下
2. **单位**: 距离单位为米，速度单位为米/秒
3. **ID管理**: 各种元素使用唯一的ID标识
4. **边界共享**: 相邻车道可以共享边界分段
5. **限速分段**: 支持随位置变化的限速

## 与现有系统集成 / Integration with Existing Systems

### map_node集成 / map_node Integration

```python
from local_map import LocalMapAPI

# 在map_node中使用LocalMap API
class MapNode:
    def __init__(self):
        self.local_map_api = None
    
    def update_local_map(self, local_map):
        self.local_map_api = LocalMapAPI(local_map)
```

### traffic_rule集成 / traffic_rule Integration

```python
from local_map import LocalMapAPI

# 在traffic_rule中使用LocalMap API
class TrafficRuleEngine:
    def __init__(self, local_map_api: LocalMapAPI):
        self.api = local_map_api
    
    def check_speed_limit(self, position):
        # 使用API查询限速
        pass
```

## 性能优化 / Performance Optimization

1. **缓存机制**: API内部使用ID缓存提高查询效率
2. **范围查询**: 使用空间索引优化范围查询
3. **批量操作**: 支持批量查询减少函数调用开销

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

1. **导入错误**: 确保Python路径正确设置
2. **数据验证失败**: 检查边界分段索引是否正确
3. **几何计算错误**: 确保输入点在合理范围内

### 调试技巧 / Debugging Tips

1. 使用 `validate_data()` 方法检查数据完整性
2. 使用 `get_statistics()` 方法查看地图统计信息
3. 启用详细日志输出跟踪API调用

## 版本历史 / Version History

- v1.0: 初始版本，包含基本数据结构和API
- v1.1: 添加几何计算和范围查询
- v1.2: 优化性能和添加缓存机制

## 联系方式 / Contact

如有问题或建议，请联系开发团队。

For questions or suggestions, please contact the development team.