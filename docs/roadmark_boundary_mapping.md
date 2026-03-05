# XODR RoadMark 与 LocalMap Boundary 线型对应关系

本文档说明 XODR 格式中的 RoadMark 线型与 LocalMap 中 Boundary 线型的对应关系，以及可视化时的渲染方式。

## 1. XODR RoadMark 类型

XODR (OpenDRIVE) 标准中定义的 RoadMark `type` 属性值：

| XODR Type | 描述 | 示例 |
|-----------|------|------|
| `none` | 无标线 | 虚拟边界 |
| `solid` | 单实线 | ━━━━━ |
| `broken` | 单虚线 | ┅┅┅┅┅ |
| `solid solid` | 双实线 | ━═━═━ |
| `solid broken` | 左实右虚 | ━┅┅┅ |
| `broken solid` | 左虚右实 | ┅┅━┅ |
| `broken broken` | 双虚线 | ┅═┅═┅ |
| `botts_dots` | 圆点标线 | ●●●●● |
| `curb` | 路缘石 | ▓▓▓▓▓ |
| `edge` | 边缘线 | ━━━━━ |

## 2. LocalMap 数据结构

### 2.1 BoundaryLineShape 枚举

定义在 [`local_map_data.py`](../src/common/local_map/local_map_data.py:81):

```python
class BoundaryLineShape(IntEnum):
    UNKNOWN = 0                # 未知
    SOLID = 1                  # 实线
    DASHED = 2                 # 虚线
    DOUBLE_SOLID = 3           # 双实线
    DOUBLE_DASHED = 4          # 双虚线
    SOLID_DASHED = 5           # 实虚组合（保留）
    DOTTED = 6                 # 点线
    LEFT_SOLID_RIGHT_DASHED = 7  # 左实右虚
    LEFT_DASHED_RIGHT_SOLID = 8  # 左虚右实
```

### 2.2 BoundaryColor 枚举

定义在 [`local_map_data.py`](../src/common/local_map/local_map_data.py:94):

```python
class BoundaryColor(IntEnum):
    UNKNOWN = 0                # 未知
    WHITE = 1                  # 白色
    YELLOW = 2                 # 黄色
    BLUE = 3                   # 蓝色
    RED = 4                    # 红色
```

## 3. 映射关系

### 3.1 线型映射 (BoundaryLineShape)

XODR → LocalMap 转换逻辑在 [`converter.py`](../src/map_node/localmap/xodrconvert/converter.py:167):

| XODR RoadMark Type | LocalMap BoundaryLineShape | 枚举值 | 说明 |
|-------------------|---------------------------|--------|------|
| `solid` | SOLID | 1 | 单实线 |
| `broken` | DASHED | 2 | 单虚线 |
| `solid solid` | DOUBLE_SOLID | 3 | 双实线 |
| `solid broken` | LEFT_SOLID_RIGHT_DASHED | 7 | 左实右虚 |
| `broken solid` | LEFT_DASHED_RIGHT_SOLID | 8 | 左虚右实 |
| `broken broken` | DOUBLE_DASHED | 4 | 双虚线 |
| `botts_dots` | DOTTED | 6 | 圆点标线 |
| `none` | UNKNOWN | 0 | 虚拟边界（无实际标线） |
| `curb` | UNKNOWN | 0 | 路缘石（通过 BoundaryType 区分） |

### 3.2 颜色映射 (BoundaryColor)

XODR → LocalMap 转换逻辑在 [`converter.py`](../src/map_node/localmap/xodrconvert/converter.py:202):

| XODR RoadMark Color | LocalMap BoundaryColor | 枚举值 | 说明 |
|--------------------|------------------------|--------|------|
| `standard` | WHITE | 1 | OpenDRIVE 默认颜色，表示白色 |
| `white` | WHITE | 1 | 白色 |
| `yellow` | YELLOW | 2 | 黄色（通常用于分隔对向交通） |
| `blue` | BLUE | 3 | 蓝色（特殊用途） |
| `red` | RED | 4 | 红色（特殊用途） |
| 其他 | UNKNOWN | 0 | 未知颜色 |

### 3.3 边界类型映射 (BoundaryType)

| XODR RoadMark Type | LocalMap BoundaryType | 枚举值 |
|-------------------|----------------------|--------|
| `curb` | CURB | 2 |
| `solid`, `broken`, `botts_dots` | LINE | 1 |
| `none` | VIRTUAL | 5 |
| 其他 | UNKNOWN | 0 |

## 4. 可视化渲染

渲染逻辑在 [`visualization.py`](../src/common/local_map/visualization.py:141):

### 4.1 颜色渲染

```python
color_map = {
    0: 'cyan',      # UNKNOWN - 青色（用于虚拟边界，在黑色背景上明显）
    1: 'white',     # WHITE - 白色
    2: 'yellow',    # YELLOW - 黄色
    3: 'blue',      # BLUE - 蓝色
    4: 'red',       # RED - 红色
}
```

### 4.2 线型渲染

```python
linestyle_map = {
    0: (0, (2, 2, 2, 2)),  # UNKNOWN - 点划线（虚拟边界独特线型）
    1: '-',                 # SOLID - 实线━━━━━━━
    2: '--',                # DASHED - 虚线┅┅┅┅┅┅┅
    3: '-',                 # DOUBLE_SOLID - 实线（双线用粗线表示）
    4: '--',                # DOUBLE_DASHED - 虚线（双虚线用粗虚线表示）
    5: '-.',                # SOLID_DASHED - 点划线（保留）
    6: ':',                 # DOTTED - 点线 ●●●●●●
    7: (0, (5, 1, 1, 1)),   # LEFT_SOLID_RIGHT_DASHED - 长点划线
    8: (0, (1, 1, 5, 1)),   # LEFT_DASHED_RIGHT_SOLID - 短点划线
}
```

## 5. 完整对应表

### XODR → LocalMap → 可视化 完整映射

```
XODR RoadMark Type    LocalMap Shape           可视化线型
─────────────────────────────────────────────────────────
solid                 SOLID (1)                实线 ━━━━━━━
broken                DASHED (2)               虚线 ┅┅┅┅┅┅┅
solid solid           DOUBLE_SOLID (3)         实线（粗）
solid broken          LEFT_SOLID_RIGHT_DASHED  长点划线
broken solid          LEFT_DASHED_RIGHT_SOLID  短点划线
broken broken         DOUBLE_DASHED (4)        虚线（粗）
botts_dots            DOTTED (6)               点线 ●●●●●●
none                  UNKNOWN (0)              点划线（虚拟边界）
curb                  CURB                     实线（宽线）
```

### XODR Color → LocalMap Color → 可视化 Color

```
XODR RoadMark Color   LocalMap Color           可视化颜色
─────────────────────────────────────────────────────────
standard              WHITE (1)                white（白色）
white                 WHITE (1)                white（白色）
yellow                YELLOW (2)               yellow（黄色）
blue                  BLUE (3)                 blue（蓝色）
red                   RED (4)                  red（红色）
(other)               UNKNOWN (0)              cyan（青色）
```

## 6. 相关文件

- XODR 转换逻辑: [`src/map_node/localmap/xodrconvert/converter.py`](../src/map_node/localmap/xodrconvert/converter.py)
- LocalMap 数据结构: [`src/common/local_map/local_map_data.py`](../src/common/local_map/local_map_data.py)
- 可视化逻辑: [`src/common/local_map/visualization.py`](../src/common/local_map/visualization.py)
- 测试文件: [`src/map_node/localmap/xodrconvert/test/test_lane_point_conversion.py`](../src/map_node/localmap/xodrconvert/test/test_lane_point_conversion.py)
