# env_node 模块 - 环境模型节点

## 1. 模块概述

### 1.1 功能描述
环境模型节点（env_node）负责将车辆状态数据和地图数据统一融合，输出标准化的环境模型，为后续交通规则判定提供统一的数据接口。

### 1.2 当前阶段功能
- **坐标系转换子模块**: 将veh_status模块输出的自车状态转换为统一的EgoVehicleState格式
- **局部地图处理子模块**: 将map_node模块生成的局部地图透传到环境模型,判定自车所在车道id，egolane：
  - 自车所在车道id判断条件：1.通过航向和与中心线距离/夹角判断可能的自车道，2.自车中心在车道边界内；
- **历史轨迹管理子模块**: 管理自车历史轨迹数据


### 1.3 未来扩展功能
- 感知数据融合: 融合障碍物、红绿灯、临时限速牌等感知信息
- 多目标跟踪: 管理周围目标车辆/行人的状态

## 2. 输入输出定义

### 2.1 输入
| 数据项 | 类型 | 来源 | 描述 |
|--------|------|------|------|
| ego_states | List[EgoVehicleState] (veh_status) | veh_status模块 | 原始自车状态列表 |
| local_map | LocalMap | map_node模块 | 局部地图数据 |

### 2.2 输出
| 数据项 | 类型 | 描述 |
|--------|------|------|
| EnvironmentModel | dataclass | 统一的环境模型 |

### 2.3 EnvironmentModel 数据结构
```python
@dataclass
class EnvironmentModel:
    """环境模型"""
    timestamp: float                              # 当前时间戳
    local_map: Optional[LocalMap]                 # 局部地图
    ego_state: EgoVehicleState                    # 当前帧自车状态（统一格式）
    ego_history: List[EgoVehicleState]            # 历史自车状态列表
```

## 3. 数据映射关系

### 3.1 veh_status.EgoVehicleState -> common.EgoVehicleState 映射

| veh_status字段 | common字段 | 转换说明 |
|----------------|------------|----------|
| timestamp | timestamp | 直接映射 |
| latitude, longitude, altitude | global_state.position | GlobalPosition |
| heading, pitch, roll | global_state.euler_angles | EulerAngles (弧度) |
| velocity_east, velocity_north, velocity_up | global_state.linear_velocity | Vector3D |
| acc_x, acc_y, acc_z | global_state.linear_acceleration | Vector3D |
| gyro_x, gyro_y, gyro_z | global_state.angular_velocity | Vector3D |
| - | local_state | 由map_node计算得到局部坐标 |

### 3.2 局部坐标系转换
- 通过map_node的project_gps_with_heading方法将GPS坐标转换为局部地图坐标
- 局部坐标系原点为当前帧的自车位置
- 局部坐标系X轴指向自车航向方向

## 4. API接口

### 4.1 EnvNode类

```python
class EnvNode:
    """环境模型节点"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化"""
        pass
    
    def init(self) -> bool:
        """
        初始化模块
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    def process(
        self,
        veh_ego_state: EgoVehicleState,  # veh_status格式
        local_map: LocalMap,
        map_node: MapNode
    ) -> EnvironmentModel:
        """
        处理单帧数据
        
        Args:
            veh_ego_state: veh_status模块输出的自车状态
            local_map: map_node模块生成的局部地图
            map_node: 地图节点实例（用于坐标转换）
            
        Returns:
            EnvironmentModel: 统一的环境模型
        """
        pass
    
    def convert_ego_state(
        self,
        veh_ego_state: EgoVehicleState,  # veh_status格式
        map_node: MapNode
    ) -> EgoVehicleState:  # common格式
        """
        将veh_status的EgoVehicleState转换为common的EgoVehicleState
        
        Args:
            veh_ego_state: veh_status模块输出的自车状态
            map_node: 地图节点实例
            
        Returns:
            EgoVehicleState: 统一格式的自车状态
        """
        pass
```

## 5. 使用示例

```python
from src.env_node import EnvNode

# 初始化
env_node = EnvNode(config)
env_node.init()

# 处理单帧
env_model = env_node.process(veh_ego_state, local_map, map_node)

# 访问数据
print(f"当前时间戳: {env_model.timestamp}")
print(f"自车位置: {env_model.ego_state.local_state.position}")
print(f"局部地图道路数: {len(env_model.local_map.roads)}")
```

## 6. 依赖关系

```
env_node
├── common.ego_vehicle_state (EgoVehicleState, LocalState, GlobalState等)
├── common.local_map.local_map_data (LocalMap)
├── veh_status.veh_status (EgoVehicleState - 输入格式)
└── map_node (MapNode - 坐标转换)
```

## 7. 文件结构

```
src/env_node/
├── __init__.py          # 模块导出
├── env_node.py          # EnvNode主类实现
├── env_model.py         # EnvironmentModel数据结构定义
└── env_node.md          # 本文档
```
