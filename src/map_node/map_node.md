# map_node模块

## 1. 模块概述

map_node模块是交通规则符合性判定系统的地图处理节点，负责：
- 加载高精度地图数据（支持OSM和XODR格式）
- 管理地图坐标系转换
- 根据自车GPS位置生成局部地图

局部地图转换内容包括：
车道中线点和边界点生成
车道前后继关系建立
车道左右相邻关系建立


### 1.1 设计原则

1. **单次加载**：地图数据仅在初始化时加载一次，避免重复加载
2. **统一接口**：对外提供统一的MapNode类，隐藏内部格式差异
3. **坐标转换**：内部处理GPS到地图坐标系的投影转换

## 2. API接口

### 2.1 MapNode类

```python
from map_node import MapNode

# 创建MapNode实例
map_node = MapNode(config)

# 初始化（加载地图）
success = map_node.init()

# 投影GPS到地图坐标系
map_x, map_y = map_node.project_gps(latitude, longitude)

# 生成局部地图
local_map = map_node.process(ego_state)
```

### 2.2 方法说明

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `__init__(config)` | config: Dict | - | 构造函数，接收配置字典 |
| `init()` | - | bool | 初始化，加载地图数据 |
| `project_gps(lat, lon)` | lat, lon: float | (x, y): Tuple[float, float] | 将GPS坐标投影到地图坐标系 |
| `process(ego_state)` | ego_state: EgoVehicleState | LocalMap | 根据自车状态生成局部地图 |
| `is_loaded()` | - | bool | 检查地图是否已加载 |

## 3. 配置说明

配置通过config.yaml的map节点传入：

```yaml
map:
  # 地图格式: "osm" 或 "xodr"
  format: "xodr"
  
  # 地图文件路径（相对于configs目录）
  map_file: "maps/Town10HD.xodr"
  
  # GPS到地图坐标系的偏移量
  coordinate_offset:
    x: -368810.882003    # X方向偏移（米）
    y: -3435507.781697   # Y方向偏移（米）
    z: -1.365000         # Z方向偏移（米）
    headingz_rad: 0.005613  # 航向角偏移（弧度）
```

## 4. 内部结构

```
map_node/
├── __init__.py          # MapNode统一入口
├── map_node.md          # 本文档
├── map_common/          # 公共类型定义
│   ├── __init__.py
│   └── base.py          # Position, BoundingBox, MapInfo等
├── maploader/           # 地图加载器
│   ├── __init__.py
│   ├── loader.py        # OSM加载器（基于Lanelet2）
│   ├── loader_xodr.py   # XODR加载器（基于pyOpenDRIVE）
│   └── utils.py         # 坐标投影工具
├── localmap/            # 局部地图构建
│   ├── ARCHITECTURE.md  # 局部地图架构文档
│   ├── osmconvert/      # OSM转换模块
│   │   ├── mapapi/      # OSM地图查询API
│   │   └── local_map_construct/  # OSM局部地图构建
│   └── xodrconvert/     # XODR转换模块
│       ├── constructor.py  # XODR局部地图构建
│       ├── transformer.py  # 坐标转换
│       └── builder.py      # 地图构建
└── examples/            # 示例代码
```

## 5. 数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                          MapNode                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  init():                                                         │
│  ┌──────────┐    ┌───────────────┐    ┌──────────────────┐      │
│  │  Config  │───>│ MapLoader     │───>│ MapData (缓存)    │      │
│  │          │    │ (OSM/XODR)    │    │                  │      │
│  └──────────┘    └───────────────┘    └──────────────────┘      │
│                                                  │               │
│  process(ego_state):                             │               │
│  ┌──────────┐    ┌───────────────┐              │               │
│  │GPS(lat,  │───>│ project_gps() │──────────────┤               │
│  │lon)      │    │ 坐标投影       │              │               │
│  └──────────┘    └───────────────┘              │               │
│                         │                        │               │
│                         ▼                        ▼               │
│                  ┌──────────────────────────────────┐            │
│                  │ LocalMapConstructor              │            │
│                  │ (使用缓存的MapData)               │            │
│                  └──────────────────────────────────┘            │
│                                  │                               │
│                                  ▼                               │
│                         ┌───────────────┐                        │
│                         │  LocalMap     │                        │
│                         │  (局部地图)    │                        │
│                         └───────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## 6. 坐标系说明

### 6.1 GPS坐标系
- 原点：地球质心
- 单位：经纬度（度）
- 输入：自车GPS数据（latitude, longitude）

### 6.2 地图坐标系
- 原点：地图定义的参考点
- 单位：米
- 特点：平面直角坐标系，适合计算距离和方向

### 6.3 坐标转换公式

```python
# GPS到地图坐标
map_x = gps_longitude * scale_x + offset_x
map_y = gps_latitude * scale_y + offset_y

# 其中offset从配置文件读取
```

## 7. 使用示例

```python
from map_node import MapNode
from veh_status import EgoVehicleState

# 1. 创建配置
config = {
    'map': {
        'format': 'xodr',
        'map_file': 'maps/Town10HD.xodr',
        'coordinate_offset': {
            'x': -368810.882003,
            'y': -3435507.781697,
            'z': -1.365000,
            'headingz_rad': 0.005613
        }
    }
}

# 2. 初始化
map_node = MapNode(config)
if not map_node.init():
    print("地图加载失败")
    exit(1)

# 3. 投影GPS坐标
latitude, longitude = 31.0, 121.0
map_x, map_y = map_node.project_gps(latitude, longitude)
print(f"地图坐标: ({map_x:.2f}, {map_y:.2f})")

# 4. 生成局部地图
ego_state = EgoVehicleState(
    latitude=latitude,
    longitude=longitude,
    heading=0.0,
    speed_kmh=60.0
)
local_map = map_node.process(ego_state)
print(f"局部地图包含 {len(local_map.lanes)} 条车道")
```

## 8. 注意事项

1. **地图加载**：`init()`方法只需调用一次，地图数据会缓存在内存中
2. **线程安全**：当前实现不是线程安全的，多线程环境需要外部加锁
3. **内存占用**：高精度地图可能占用较大内存，请注意系统资源
4. **坐标偏移**：coordinate_offset必须与地图数据匹配，否则投影结果不正确
