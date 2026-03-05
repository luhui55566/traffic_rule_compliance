# Local Map Data Structures Hierarchy

## Hierarchy Overview / 层级总览

| LocalMap (主结构) | Elements (元素) | Sub-Elements (次级元素) |
|-------------------|-----------------|-------------------------|
| **LocalMap** | `header: Header` | `timestamp: datetime` (时间戳)<br>`frame_id: str` (坐标系ID)<br>`sequence_number: int` (序列号) |
| | `metadata: LocalMapMetadata` | `map_range_x: float` (X轴范围/米)<br>`map_range_y: float` (Y轴范围/米)<br>`map_range_z: float` (Z轴范围/米)<br>`ego_vehicle_x: float` (自车X坐标)<br>`ego_vehicle_y: float` (自车Y坐标)<br>`ego_vehicle_heading: float` (自车航向角/弧度)<br>`ego_vehicle_velocity: float` (自车速度/米/秒)<br>`timestamp: datetime` (数据生成时间戳) |
| | `lanes: List[Lane]` | `lane_id: int` (车道唯一标识符)<br>`lane_type: LaneType` (车道类型)<br>`lane_direction: LaneDirection` (车道方向)<br>`original_lane_id: Optional[int]` (原始lane ID)<br>`original_road_id: Optional[int]` (原始road ID)<br>`original_junction_id: Optional[int]` (原始junction ID)<br>`map_source_type: str` (地图源类型)<br>`map_source_id: str` (地图源标识)<br>`centerline_points: List[Point3D]` (中心线点集)<br>`left_boundary_segment_indices: List[int]` (左边界分段索引)<br>`right_boundary_segment_indices: List[int]` (右边界分段索引)<br>`speed_limits: List[SpeedLimitSegment]` (限速分段列表)<br>`associated_traffic_light_ids: List[int]` (关联信号灯ID)<br>`associated_traffic_sign_ids: List[int]` (关联交通标志ID)<br>`associated_stop_line_ids: List[int]` (关联停止线ID)<br>`associated_crosswalk_ids: List[int]` (关联人行横道ID)<br>`associated_road_marking_ids: List[int]` (关联道路标线ID)<br>`associated_intersection_id: Optional[int]` (关联交叉口ID)<br>`left_adjacent_lane_id: Optional[int]` (左侧相邻车道ID)<br>`right_adjacent_lane_id: Optional[int]` (右侧相邻车道ID)<br>`predecessor_lane_ids: List[int]` (前继车道ID列表)<br>`successor_lane_ids: List[int]` (后继车道ID列表)<br>`road_id: Optional[int]` (全局唯一道路ID)<br>`junction_id: Optional[int]` (全局唯一交叉口ID)<br>`is_junction_lane: bool` (是否为交叉口内部车道) |
| | `traffic_lights: List[TrafficLight]` | `traffic_light_id: int` (信号灯唯一标识符)<br>`position: Point3D` (信号灯位置)<br>`current_state: TrafficLightState` (当前状态)<br>`associated_lane_id: int` (关联车道ID)<br>`predicted_states: List[TrafficLightState]` (预测状态序列)<br>`distance_to_stop_line: float` (到停止线距离/米)<br>`associated_stop_line_id: int` (关联停止线ID)<br>`light_type: TrafficLightType` (信号灯类型)<br>`confidence: float` (检测置信度) |
| | `traffic_signs: List[TrafficSign]` | `traffic_sign_id: int` (标志唯一标识符)<br>`position: Point3D` (标志位置)<br>`sign_type: TrafficSignType` (标志类型)<br>`associated_lane_id: int` (关联车道ID)<br>`distance_to_sign: float` (到标志距离/米)<br>`value: float` (标志数值, 如限速值)<br>`text_content: str` (标志文本内容)<br>`confidence: float` (检测置信度)<br>`is_valid: bool` (标志是否有效)<br>`valid_until: Optional[datetime]` (有效期截止时间) |
| | `road_markings: List[RoadMarking]` | `road_marking_id: int` (标线唯一标识符)<br>`marking_type: RoadMarkingType` (标线类型)<br>`marking_points: List[Point3D]` (标线点集)<br>`marking_width: float` (标线宽度/米)<br>`marking_color: RoadMarkingColor` (标线颜色)<br>`associated_lane_id: int` (关联车道ID)<br>`confidence: float` (检测置信度) |
| | `crosswalks: List[Crosswalk]` | `crosswalk_id: int` (人行横道唯一标识符)<br>`polygon_points: List[Point3D]` (多边形顶点)<br>`crosswalk_width: float` (人行横道宽度/米)<br>`crosswalk_length: float` (人行横道长度/米)<br>`has_traffic_light: bool` (是否有信号灯控制)<br>`associated_traffic_light_id: int` (关联信号灯ID)<br>`associated_lane_id: int` (关联车道ID)<br>`has_pedestrian_island: bool` (是否有安全岛)<br>`confidence: float` (检测置信度) |
| | `stop_lines: List[StopLine]` | `stop_line_id: int` (停止线唯一标识符)<br>`line_points: List[Point3D]` (停止线点集)<br>`stop_line_type: StopLineType` (停止线类型)<br>`associated_lane_id: int` (关联车道ID)<br>`associated_traffic_light_id: int` (关联信号灯ID)<br>`associated_sign_id: int` (关联标志ID)<br>`distance_to_stop_line: float` (到停止线距离/米)<br>`is_mandatory: bool` (是否强制停止)<br>`confidence: float` (检测置信度) |
| | `intersections: List[Intersection]` | `intersection_id: int` (交叉口唯一标识符)<br>`intersection_type: IntersectionType` (交叉口类型)<br>`polygon_points: List[Point3D]` (多边形顶点)<br>`incoming_lane_ids: List[int]` (进入车道ID列表)<br>`outgoing_lane_ids: List[int]` (离开车道ID列表)<br>`traffic_light_ids: List[int]` (信号灯ID列表)<br>`stop_line_ids: List[int]` (停止线ID列表)<br>`crosswalk_ids: List[int]` (人行横道ID列表)<br>`has_traffic_light: bool` (是否有信号灯控制)<br>`has_stop_sign: bool` (是否有停车标志)<br>`is_roundabout: bool` (是否为环岛)<br>`associated_lane_id: int` (关联车道ID)<br>`confidence: float` (检测置信度) |
| | `boundary_segments: List[LaneBoundarySegment]` | `segment_id: int` (分段唯一标识符)<br>`boundary_points: List[Point3D]` (边界点列表)<br>`boundary_type_segments: List[Tuple[Point3D, BoundaryType]]`<br>`boundary_line_shape_segments: List[Tuple[Point3D, BoundaryLineShape]]`<br>`boundary_color_segments: List[Tuple[Point3D, BoundaryColor]]`<br>`boundary_thickness_segments: List[Tuple[Point3D, float]]`<br>`is_virtual_segments: List[Tuple[Point3D, bool]]` |
| | `roads: List[Road]` | `road_id: int` (道路唯一标识符)<br>`road_name: str` (道路名称)<br>`road_length: float` (道路长度/米)<br>`road_type: str` (道路类型)<br>`predecessor_road_id: Optional[int]` (前继道路ID)<br>`successor_road_id: Optional[int]` (后继道路ID)<br>`predecessor_junction_id: Optional[int]` (前继交叉口ID)<br>`successor_junction_id: Optional[int]` (后继交叉口ID)<br>`lane_ids: List[int]` (包含的车道ID列表)<br>`reference_line: List[Point3D]` (参考线点集)<br>`speed_limit: float` (道路限速/米/秒) |
| | `junctions: List[Junction]` | `junction_id: int` (交叉口唯一标识符)<br>`junction_name: str` (交叉口名称)<br>`junction_type: str` (交叉口类型)<br>`road_ids: List[int]` (连接的道路ID列表)<br>`connection_count: int` (连接数量)<br>`has_traffic_light: bool` (是否有信号灯控制)<br>`controller_ids: List[int]` (控制器ID列表)<br>`polygon_points: List[Point3D]` (多边形顶点)<br>`center_point: Point3D` (中心点) |
| | `custom_data: List[CustomData]` | `key: str` (数据键)<br>`value: str` (数据值) |
| | `reserved_bytes: bytes` | 预留字节 |
| | `reserved_string: str` | 预留字符串 |

---

## Nested Sub-Elements / 嵌套次级元素

### Point3D (基础类型)
| Field | Type | Description |
|-------|------|-------------|
| x | float | X坐标（米）/ X coordinate (meters) |
| y | float | Y坐标（米）/ Y coordinate (meters) |
| z | float | Z坐标（米）/ Z coordinate (meters) |

### TrafficLightState (TrafficLight的current_state字段)
| Field | Type | Description |
|-------|------|-------------|
| timestamp | datetime | 状态时间戳 / State timestamp |
| color | TrafficLightColor | 灯光颜色 / Light color |
| shape | TrafficLightShape | 灯光形状 / Light shape |
| status | TrafficLightStatus | 灯光状态 / Light status |
| remaining_time | float | 剩余时间（秒）/ Remaining time (seconds), 默认0.0 |

### SpeedLimitSegment (Lane的speed_limits字段)
| Field | Type | Description |
|-------|------|-------------|
| segment_id | int | 分段唯一标识符 / Unique segment identifier |
| speed_limit | float | 限速值（米/秒）/ Speed limit (m/s) |
| min_speed_limit | float | 最低限速值（米/秒）/ Minimum speed limit (m/s), 默认0.0 |
| associated_sign_id | Optional[int] | 产生此限速的交通标志ID / Traffic sign ID |
| speed_limit_type | SpeedLimitType | 限速类型 / Speed limit type, 默认REGULAR |
| start_position | Point3D | 分段起始位置（绝对坐标）/ Segment start position |
| end_position | Point3D | 分段结束位置（绝对坐标）/ Segment end position |

---

## Enum Types Reference / 枚举类型参考

### LaneType (Lane.lane_type)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | DRIVING | 行驶车道 / Driving lane |
| 2 | SHOULDER | 路肩 / Shoulder |
| 3 | PARKING | 停车位 / Parking spot |
| 4 | BIKING | 自行车道 / Biking lane |
| 5 | SIDEWALK | 人行道 / Sidewalk |
| 6 | CROSSWALK | 人行横道 / Crosswalk |
| 7 | EXIT | 出口车道 / Exit lane |
| 8 | ENTRY | 入口车道 / Entry lane |
| 9 | MERGE | 合并车道 / Merge lane |
| 10 | SPLIT | 分叉车道 / Split lane |

### LaneDirection (Lane.lane_direction)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | FORWARD | 前进 / Forward |
| 2 | BACKWARD | 后退 / Backward |
| 3 | BIDIRECTIONAL | 双向 / Bidirectional |

### BoundaryType (LaneBoundarySegment.boundary_type_segments)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | LINE | 线型边界 / Line boundary |
| 2 | CURB | 路缘石 / Curb |
| 3 | GUARDRAIL | 护栏 / Guardrail |
| 4 | WALL | 墙壁 / Wall |
| 5 | VIRTUAL | 虚拟边界 / Virtual boundary |

### BoundaryLineShape (LaneBoundarySegment.boundary_line_shape_segments)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | SOLID | 实线 / Solid |
| 2 | DASHED | 虚线 / Dashed |
| 3 | DOUBLE_SOLID | 双实线 / Double solid |
| 4 | DOUBLE_DASHED | 双虚线 / Double dashed |
| 5 | SOLID_DASHED | 实虚组合 / Solid-dashed combination |
| 6 | DOTTED | 点线 / Dotted |
| 7 | LEFT_SOLID_RIGHT_DASHED | 左实右虚 / Left solid right dashed |
| 8 | LEFT_DASHED_RIGHT_SOLID | 左虚右实 / Left dashed right solid |

### BoundaryColor (LaneBoundarySegment.boundary_color_segments)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | WHITE | 白色 / White |
| 2 | YELLOW | 黄色 / Yellow |
| 3 | BLUE | 蓝色 / Blue |
| 4 | RED | 红色 / Red |

### SpeedLimitType (SpeedLimitSegment.speed_limit_type)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | REGULAR | 常规限速：道路默认限速 |
| 2 | TEMPORARY | 临时限速：临时限速牌产生的限速 |
| 3 | SCHOOL_ZONE | 学校区域限速 |
| 4 | CONSTRUCTION_ZONE | 施工区域限速 |
| 5 | WEATHER_CONDITION | 天气条件限速 |

### TrafficLightColor (TrafficLightState.color)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | RED | 红色 / Red |
| 2 | YELLOW | 黄色 / Yellow |
| 3 | GREEN | 绿色 / Green |
| 4 | RED_YELLOW | 红黄组合 / Red-yellow combination |
| 5 | FLASHING_RED | 闪烁红 / Flashing red |
| 6 | FLASHING_YELLOW | 闪烁黄 / Flashing yellow |
| 7 | FLASHING_GREEN | 闪烁绿 / Flashing green |

### TrafficLightShape (TrafficLightState.shape)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | CIRCLE | 圆形 / Circle |
| 2 | LEFT_ARROW | 左箭头 / Left arrow |
| 3 | RIGHT_ARROW | 右箭头 / Right arrow |
| 4 | UP_ARROW | 上箭头 / Up arrow |
| 5 | DOWN_ARROW | 下箭头 / Down arrow |
| 6 | UP_LEFT_ARROW | 左上箭头 / Up-left arrow |
| 7 | UP_RIGHT_ARROW | 右上箭头 / Up-right arrow |
| 8 | CROSS | 叉号 / Cross |

### TrafficLightStatus (TrafficLightState.status)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | SOLID_OFF | 常灭 / Solid off |
| 2 | SOLID_ON | 常亮 / Solid on |
| 3 | FLASHING | 闪烁 / Flashing |

### TrafficLightType (TrafficLight.light_type)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | VEHICLE | 机动车信号灯 / Vehicle traffic light |
| 2 | PEDESTRIAN | 行人信号灯 / Pedestrian traffic light |
| 3 | BICYCLE | 自行车信号灯 / Bicycle traffic light |
| 4 | LANE_CONTROL | 车道控制信号灯 / Lane control light |

### TrafficSignType (TrafficSign.sign_type)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | SPEED_LIMIT | 限速 / Speed limit |
| 2 | SPEED_LIMIT_END | 解除限速 / End of speed limit |
| 3 | MINIMUM_SPEED | 最低限速 / Minimum speed |
| 4 | SPEED_LIMIT_ZONE_START | 限速区开始 / Speed limit zone start |
| 5 | SPEED_LIMIT_ZONE_END | 限速区结束 / Speed limit zone end |
| 10 | NO_ENTRY | 禁止驶入 / No entry |
| 11 | NO_PARKING | 禁止停车 / No parking |
| 12 | NO_STOPPING | 禁止停车（临时）/ No stopping |
| 13 | NO_OVERTAKING | 禁止超车 / No overtaking |
| 14 | NO_LEFT_TURN | 禁止左转 / No left turn |
| 15 | NO_RIGHT_TURN | 禁止右转 / No right turn |
| 16 | NO_U_TURN | 禁止掉头 / No U-turn |
| 17 | NO_HONKING | 禁止鸣笛 / No honking |
| 20 | CURVE_LEFT | 左急弯 / Left curve |
| 21 | CURVE_RIGHT | 右急弯 / Right curve |
| 22 | WINDING_ROAD | 连续弯路 / Winding road |
| 23 | STEEP_ASCENT | 陡坡上坡 / Steep ascent |
| 24 | STEEP_DESCENT | 陡坡下坡 / Steep descent |
| 25 | NARROW_ROAD | 窄路 / Narrow road |
| 26 | ROAD_WORKS | 施工 / Road works |
| 27 | TRAFFIC_SIGNAL_AHEAD | 前方信号灯 / Traffic signal ahead |
| 28 | PEDESTRIAN_CROSSING | 人行横道 / Pedestrian crossing |
| 29 | SCHOOL_ZONE | 学校区域 / School zone |
| 30 | SLIPPERY_ROAD | 湿滑路面 / Slippery road |
| 31 | FALLING_ROCKS | 落石 / Falling rocks |
| 32 | ANIMAL_CROSSING | 动物出没 / Animal crossing |
| 40 | STRAIGHT_ONLY | 直行 / Straight only |
| 41 | LEFT_TURN_ONLY | 左转 / Left turn only |
| 42 | RIGHT_TURN_ONLY | 右转 / Right turn only |
| 43 | STRAIGHT_OR_LEFT | 直行或左转 / Straight or left |
| 44 | STRAIGHT_OR_RIGHT | 直行或右转 / Straight or right |
| 45 | KEEP_LEFT | 靠左行驶 / Keep left |
| 46 | KEEP_RIGHT | 靠右行驶 / Keep right |
| 47 | ROUNDABOUT | 环岛 / Roundabout |
| 48 | PASS_EITHER_SIDE | 两侧通行 / Pass either side |
| 50 | HIGHWAY_ENTRANCE | 高速公路入口 / Highway entrance |
| 51 | HIGHWAY_EXIT | 高速公路出口 / Highway exit |
| 52 | SERVICE_AREA | 服务区 / Service area |
| 53 | PARKING_AREA | 停车场 / Parking area |
| 54 | HOSPITAL | 医院 / Hospital |
| 55 | GAS_STATION | 加油站 / Gas station |
| 56 | REST_AREA | 休息区 / Rest area |
| 60 | TEMPORARY_SPEED_LIMIT | 临时限速 / Temporary speed limit |
| 61 | TEMPORARY_NO_OVERTAKING | 临时禁止超车 / Temporary no overtaking |
| 62 | TEMPORARY_LANE_CLOSURE | 临时车道封闭 / Temporary lane closure |
| 63 | TEMPORARY_ROAD_CLOSURE | 临时道路封闭 / Temporary road closure |

### RoadMarkingType (RoadMarking.marking_type)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | STOP_LINE | 停止线 / Stop line |
| 2 | CROSSWALK | 人行横道 / Crosswalk |
| 3 | ZEBRA_CROSSING | 斑马线 / Zebra crossing |
| 4 | ARROW_LEFT | 左转箭头 / Left turn arrow |
| 5 | ARROW_RIGHT | 右转箭头 / Right turn arrow |
| 6 | ARROW_STRAIGHT | 直行箭头 / Straight arrow |
| 7 | ARROW_U_TURN | 掉头箭头 / U-turn arrow |
| 8 | YIELD_LINE | 让行线 / Yield line |
| 9 | TEXT_MARKING | 文字标线 / Text marking |
| 10 | DIAGONAL_MARKING | 斜线标线 / Diagonal marking |
| 11 | CHECKERBOARD | 棋盘格标线 / Checkerboard marking |

### RoadMarkingColor (RoadMarking.marking_color)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | WHITE | 白色 / White |
| 2 | YELLOW | 黄色 / Yellow |
| 3 | BLUE | 蓝色 / Blue |
| 4 | RED | 红色 / Red |

### StopLineType (StopLine.stop_line_type)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | TRAFFIC_LIGHT | 信号灯停止线 / Traffic light stop line |
| 2 | STOP_SIGN | 停车标志停止线 / Stop sign stop line |
| 3 | CROSSWALK | 人行横道停止线 / Crosswalk stop line |
| 4 | RAILWAY | 铁路道口停止线 / Railway crossing stop line |
| 5 | YIELD | 让行线 / Yield line |
| 6 | CHECKPOINT | 检查站停止线 / Checkpoint stop line |

### IntersectionType (Intersection.intersection_type)
| Value | Name | Description |
|-------|------|-------------|
| 0 | UNKNOWN | 未知 / Unknown |
| 1 | FOUR_WAY | 十字路口 / Four-way intersection |
| 2 | THREE_WAY | 三岔路口 / Three-way intersection |
| 3 | T_JUNCTION | T型路口 / T-junction |
| 4 | Y_JUNCTION | Y型路口 / Y-junction |
| 5 | ROUNDABOUT | 环岛 / Roundabout |
| 6 | MULTI_LEG | 多岔路口 / Multi-leg intersection |

---

## Utility Functions / 工具函数

| Function Name | Parameters | Return Type | Description |
|---------------|-------------|-------------|-------------|
| `create_empty_local_map` | `ego_pose: Pose`, `map_range: float = 200.0` | `LocalMap` | 创建空的局部地图 |
| `get_lane_by_id` | `local_map: LocalMap`, `lane_id: int` | `Optional[Lane]` | 根据车道ID获取车道对象 |
| `get_boundary_segment_by_id` | `local_map: LocalMap`, `segment_id: int` | `Optional[LaneBoundarySegment]` | 根据边界分段ID获取边界分段对象 |
| `get_traffic_light_by_id` | `local_map: LocalMap`, `traffic_light_id: int` | `Optional[TrafficLight]` | 根据信号灯ID获取信号灯对象 |
| `get_traffic_sign_by_id` | `local_map: LocalMap`, `traffic_sign_id: int` | `Optional[TrafficSign]` | 根据交通标志ID获取交通标志对象 |
| `get_lanes_in_range` | `local_map: LocalMap`, `x_range: tuple`, `y_range: tuple` | `List[Lane]` | 获取指定范围内的车道 |
| `validate_local_map` | `local_map: LocalMap` | `List[str]` | 验证局部地图数据的有效性 |

---

## Abstract Class / 抽象类

| Class Name | Methods | Description |
|------------|---------|-------------|
| `HDMapConverter` | `convert_to_local_map(hd_map, ego_pose, range) -> LocalMap`<br>`get_supported_format() -> str` | 高精地图转换器基类 / Base class for HD map converters |
