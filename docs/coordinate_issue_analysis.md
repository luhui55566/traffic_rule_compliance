# 坐标问题分析报告

## 问题描述

使用 [`MapLoader`](src/maploader/loader.py) 加载 Town10HD.osm 地图后，可视化显示的点坐标与原始 OSM 文件中的 `local_x`/`local_y` 标签值不一致，特别是 Y 坐标。

## 根本原因

### OSM 文件结构分析

Town10HD.osm 文件中的节点包含两种坐标表示：

```xml
<node id="1" lat="8.4440784312e-05" lon="0.00097084469596" version="1" visible="True">
  <tag k="local_y" v="9.34613037109"/>
  <tag k="local_x" v="108.179916382"/>
  <tag k="ele" v="0.0"/>
</node>
```

- `lat`/`lon`: 值非常小（例如 lat=0.00008444, lon=0.00097084），这些不是真实的 GPS 坐标，而是相对于某个原点的偏移量
- `local_x`/`local_y`: 真实的局部坐标值（例如 local_x=108.18, local_y=9.35）

### Lanelet2 默认加载行为

[`MapLoader`](src/maploader/loader.py) 使用 Lanelet2 的 `lanelet2.io.load()` 函数加载地图：

```python
self.lanelet_map = lanelet2.io.load(file_path, projector.origin)
```

Lanelet2 将 `lat`/`lon` 当作 GPS 坐标处理，并使用 UTM 投影进行坐标转换。由于这些值不是真实的 GPS 坐标，转换后的结果与 `local_x`/`local_y` 不一致。

### 测试结果

使用原点 (0,0) 加载：
```
Node 1:
  OSM local_x=108.18, local_y=9.35
  Lanelet2 x=108.07, y=9.40
  差异: dx=-0.11, dy=0.05
```

使用北京天安门原点加载：
```
Node 1:
  OSM local_x=108.18, local_y=9.35
  Lanelet2 x=82.91, y=7.21
  差异: dx=-25.27, dy=-2.14
```

## 解决方案

创建了新的 [`LocalMapLoader`](src/maploader/loader_local.py) 类，直接使用 `local_x`/`local_y` 标签加载地图：

### 主要特点

1. **直接解析 OSM 文件**：使用 XML 解析器读取 OSM 文件
2. **使用 local_x/local_y**：直接从标签中读取坐标值，不进行投影转换
3. **手动构建地图对象**：
   - 解析节点 → 创建 `Point3d`
   - 解析路径 → 创建 `LineString3d`
   - 解析关系 → 创建 `Lanelet`

### 使用示例

```python
from maploader.loader_local import LocalMapLoader

loader = LocalMapLoader()
success = loader.load_map("Town10HD.osm")

if success:
    map_data = loader.get_map_data()
    lanelet_map = map_data['lanelet_map']
    # 使用 lanelet_map 进行可视化或其他操作
```

### 测试结果

使用 [`LocalMapLoader`](src/maploader/loader_local.py) 加载：
```
点数量: 9214
线数量: 279
车道数量: 168

Point 9688: x=-28.82, y=-22.85, z=0.00
```

坐标与 OSM 文件中的 `local_x`/`local_y` 完全一致。

## 文件说明

| 文件 | 说明 |
|------|------|
| [`src/maploader/loader.py`](src/maploader/loader.py) | 原始加载器，使用 Lanelet2 默认加载方式 |
| [`src/maploader/loader_local.py`](src/maploader/loader_local.py) | 新的加载器，直接使用 local_x/local_y |
| [`examples/debug_coordinates2.py`](examples/debug_coordinates2.py) | 坐标调试脚本，分析问题根源 |
| [`examples/test_local_loader.py`](examples/test_local_loader.py) | LocalMapLoader 测试脚本 |

## 建议

1. 对于包含 `local_x`/`local_y` 标签的 OSM 文件，使用 [`LocalMapLoader`](src/maploader/loader_local.py)
2. 对于标准 GPS 坐标的 OSM 文件，使用原始的 [`MapLoader`](src/maploader/loader.py)
3. 可以在 [`MapLoader`](src/maploader/loader.py) 中添加自动检测逻辑，根据文件内容选择合适的加载方式
