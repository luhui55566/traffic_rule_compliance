# 交通规则符合性判定系统 - MapLoader模块

## 概述

MapLoader模块是基于Lanelet2的地图加载模块，支持OSM格式地图，通过共享内存模式实现MapLoader和MapAPI的完全解耦。

## 项目结构

```
lanelet_test/
├── architect.md                 # 主架构文档
├── maploader_architecture.md     # MapLoader模块架构文档
├── mapapi_architecture.md       # MapAPI模块架构文档
├── Town10HD.osm               # OSM地图文件
├── src/
│   ├── map/                    # 共享模块（基础数据结构）
│   │   ├── __init__.py
│   │   └── base.py             # 基础数据结构
│   ├── maploader/               # MapLoader模块
│   │   ├── __init__.py
│   │   ├── loader.py           # 地图加载器
│   │   └── utils.py            # 工具函数（坐标转换等）
│   └── mapapi/                 # MapAPI模块（待实现）
│       └── __init__.py
├── examples/                   # 示例代码
│   └── load_map_example.py  # 地图加载示例
├── tests/                     # 测试目录
│   ├── __init__.py
│   └── test_loader.py         # 地图加载器测试
└── configs/                   # 配置文件目录
```

## 安装依赖

### 安装Lanelet2

```bash
# Ubuntu/Debian
sudo apt-get install liblanelet2-dev python3-lanelet2

# 或从源码编译
git clone https://github.com/fzi-forschungszentrum-informatik/Lanelet2.git
cd Lanelet2
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

### 安装Python依赖

```bash
pip install pyyaml pytest
```

## 使用方法

### 1. 加载地图

```python
from maploader.loader import MapLoader
from maploader.utils import UtmProjectorWrapper
from lanelet2.io import Origin
from lanelet2.core import GPSPoint

# 创建地图加载器
loader = MapLoader()

# 创建投影器（必须手动指定原点）
gps_point = GPSPoint(lat=39.9042, lon=116.4074)
origin = Origin(gps_point)
projector = UtmProjectorWrapper(origin)

# 加载地图
success = loader.load_map("Town10HD.osm", projector)
if success:
    print("地图加载成功！")
    map_info = loader.get_map_info()
    print(f"车道数量: {map_info.num_lanelets}")
```

### 2. 运行示例

```bash
# 使用conda环境
conda run -n lanelet python examples/load_map_example.py

# 或直接运行
python examples/load_map_example.py
```

### 3. 运行测试

```bash
# 使用conda环境
conda run -n lanelet python tests/test_loader.py

# 或直接运行
python tests/test_loader.py
```

## 核心类说明

### MapLoader

地图加载器，负责加载OSM文件并初始化Lanelet2。

**主要方法：**
- `load_map(file_path, projector)` - 加载OSM地图文件
- `get_map_info()` - 获取地图信息
- `is_loaded()` - 检查地图是否已加载

### UtmProjectorWrapper

UTM投影器包装类，用于GPS坐标与地图坐标的转换。

**主要方法：**
- `forward(gps)` - GPS坐标转换为地图坐标
- `reverse(point)` - 地图坐标转换为GPS坐标

### MapDataStore

共享内存存储，用于MapLoader和MapAPI之间的数据共享。

**主要方法：**
- `set_lanelet_map(lanelet_map)` - 设置LaneletMap到共享内存
- `get_lanelet_map()` - 从共享内存获取LaneletMap
- `is_loaded()` - 检查地图是否已加载
- `clear()` - 清空共享内存

### Position

位置信息（WGS84坐标系）。

**属性：**
- `latitude` - 纬度
- `longitude` - 经度
- `altitude` - 海拔高度（可选）

### MapInfo

地图元信息。

**属性：**
- `map_type` - 地图类型
- `file_path` - 地图文件路径
- `num_lanelets` - 车道数量
- `bounds` - 地图边界框
- `coordinate_system` - 坐标系
- `is_loaded` - 是否已加载

## 设计原则

1. **完全解耦**：MapLoader和MapAPI通过共享内存完全解耦
2. **共享内存模式**：MapLoader将LaneletMap存储在共享内存，MapAPI从中读取
3. **手动配置**：Projector必须通过配置或参数指定，不自动计算
4. **类型安全**：使用Python类型注解确保代码质量

## 测试结果

```bash
$ conda run -n lanelet python tests/test_loader.py
...
----------------------------------------------------------------------
Ran 14 tests in 0.022s

OK
```

## 注意事项

1. **Projector必须手动指定**：不能自动计算，确保坐标转换的一致性
2. **共享内存**：MapLoader加载后，LaneletMap存储在共享内存中，MapAPI可以从中读取
3. **全局加载**：当前采用全局加载策略，加载整个地图到内存
4. **OSM格式**：仅支持OSM格式，XODR格式需要离线转换

## 下一步

- 实现MapAPI模块
- 实现场景识别模块
- 实现交规判定引擎

## 参考资料

- Lanelet2: https://github.com/fzi-forschungszentrum-informatik/Lanelet2
- OpenStreetMap: https://www.openstreetmap.org/
