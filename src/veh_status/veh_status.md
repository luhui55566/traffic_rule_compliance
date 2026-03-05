# veh_status 模块

## 1. 模块概述

veh_status模块是交通规则符合性判定系统的车辆状态数据读取模块，负责从pkl文件中读取并解析车辆状态数据，为后续的地图匹配和交通规则判定提供自车状态信息。

## 2. 功能描述

### 2.1 主要功能
- 读取指定目录下的pkl文件序列
- 解析pkl文件中的车辆状态数据，包括：
 - **GPS数据**：经纬度、高度、速度等
 - **姿态数据**：航向角、俯仰角、横滚角
 - **IMU数据**：角速度、加速度
 - **运动状态**：运动时间戳、运动航向等
- 按时间顺序输出自车状态列表

### 2.2 数据流程
```
pkl文件目录 → 逐帧读取 → 解析数据 → 封装状态对象 → 输出状态列表
```

## 3. 接口定义

### 3.1 输入
通过配置文件（configs/traffic_rule_config.yaml）指定：
```yaml
vehicle:
 pkl_directory: "datas/pkl" # pkl文件目录路径
```

### 3.2 输出
自车状态列表（List[EgoVehicleState]），每个状态包含：
- 时间戳信息
- GPS位置（经度、纬度、高度）
- 速度信息（东向速度、北向速度、天向速度）
- 姿态信息（航向角、俯仰角、横滚角）
- IMU数据（角速度、加速度）
- 帧文件名（用于追溯）

### 3.3 API接口

#### 类：`VehStatusReader`

```python
class VehStatusReader:
 """车辆状态读取器"""
 
 def __init__(self, config: Dict[str, Any]):
 """
 初始化车辆状态读取器
 
 Args:
 config: 配置字典，包含pkl文件路径等信息
 """
 pass
 
 def init(self) -> bool:
 """
 初始化模块，验证pkl目录有效性
 
 Returns:
 bool: 初始化是否成功
 """
 pass
 
 def process(self) -> List[EgoVehicleState]:
 """
 处理所有pkl文件，返回自车状态列表
 
 Returns:
 List[EgoVehicleState]: 自车状态列表，按时间戳排序
 """
 pass
 
 def get_frame_count(self) -> int:
 """
 获取总帧数
 
 Returns:
 int: pkl文件总数
 """
 pass
 
 def get_frame_by_index(self, index: int) -> Optional[EgoVehicleState]:
 """
 按索引获取单帧状态
 
 Args:
 index: 帧索引
 
 Returns:
 Optional[EgoVehicleState]: 单帧状态，索引无效时返回None
 """
 pass
 
 def get_iterator(self) -> Iterator[EgoVehicleState]:
 """
 获取状态迭代器，支持逐帧处理
 
 Yields:
 EgoVehicleState: 单帧车辆状态
 """
 pass
```

## 4. 数据结构

### 4.1 EgoVehicleState 数据类

| 字段 | 类型 | 描述 |
|------|------|------|
| timestamp | int | 时间戳（纳秒） |
| gps_week | int | GPS周数 |
| gps_time | float | GPS周内时间（秒） |
| latitude | float | 纬度（度） |
| longitude | float | 经度（度） |
| altitude | float | 高度（米） |
| heading | float | 航向角（度） |
| pitch | float | 俯仰角（度） |
| roll | float | 横滚角（度） |
| velocity_east | float | 东向速度（m/s） |
| velocity_north | float | 北向速度（m/s） |
| velocity_up | float | 天向速度（m/s） |
| gyro_x/y/z | float | 角速度（rad/s） |
| acc_x/y/z | float | 加速度（m/s²） |
| status | int | GPS状态标识 |
| pose | np.ndarray | 4x4位姿矩阵 |
| frame_name | str | 帧文件名 |

## 5. 使用示例

### 5.1 基本使用

```python
from src.veh_status import VehStatusReader
import yaml

# 加载配置
with open("configs/traffic_rule_config.yaml", 'r') as f:
 config = yaml.safe_load(f)

# 初始化读取器
reader = VehStatusReader(config)
reader.init()

# 获取所有状态
states = reader.process()
print(f"共读取 {len(states)} 帧数据")

# 遍历状态
for state in states:
 print(f"时间: {state.timestamp}, 位置: ({state.latitude}, {state.longitude})")
```

### 5.2 迭代器模式

```python
# 使用迭代器逐帧处理（内存友好）
for state in reader.get_iterator():
 # 处理单帧数据
 process_frame(state)
```

### 5.3 与allnodes集成

```python
# allnodes.py 中的调用方式
class AllNodes:
 def __init__(self, config_path: str):
 # 加载配置
 with open(config_path, 'r') as f:
 self.config = yaml.safe_load(f)
 
 # 初始化各模块
 self.veh_status_reader = VehStatusReader(self.config)
 
 def run(self):
 # 初始化veh_status模块
 if not self.veh_status_reader.init():
 raise RuntimeError("veh_status模块初始化失败")
 
 # 获取车辆状态列表
 self.ego_states = self.veh_status_reader.process()
 
 # 后续处理...
```

## 6. 错误处理

| 错误类型 | 描述 | 处理方式 |
|----------|------|----------|
| 目录不存在 | pkl目录路径无效 | 抛出FileNotFoundError |
| 文件读取失败 | pkl文件损坏或格式错误 | 记录警告，跳过该帧 |
| 数据字段缺失 | 必要字段不存在 | 使用默认值，记录警告 |

## 7. 性能考虑

- **缓存机制**：支持已加载文件的缓存，避免重复读取
- **惰性加载**：迭代器模式支持惰性处理，减少内存占用
- **批量处理**：支持一次性读取所有数据到内存

## 8. 依赖关系

- 输入依赖：pkl文件数据源
- 输出依赖：被map_node模块（提供GPS位置）、环境模型模块（提供车辆状态）使用
