
def create_right_angle_turn_map() -> LocalMap:
    """
    创建直角弯道地图
    Create right angle turn map
    
    Returns:
        LocalMap: 直角弯道地图 / Right angle turn map
    """
    # Ego position at start of the road
    ego_pose = Pose(
        position=Point3D(x=0.0, y=0.0, z=0.0),
        heading=0.0,
        pitch=0.0,
        roll=0.0
    )
    
    # Create empty local map with 200m radius
    local_map = create_empty_local_map(ego_pose, 200.0)
    
    # ==================== 创建边界分段 / Create Boundary Segments ====================
    # 双向四车道：2个方向 x 2车道 = 4车道
    # 每个方向3段边界（直道、弯道、出口）x 2方向 = 12段边界
    # 加上中间的分隔线 = 总共13段边界
    # Bidirectional 4 lanes: 2 directions x 2 lanes = 4 lanes
    # Each direction has 3 boundary segments (straight, curve, exit) x 2 directions = 12 segments
    # Plus centerline divider = Total 13 boundary segments
    
    boundary_segments = []
    
    # ==================== 正向车道边界 (Forward Direction Lanes) ====================
    # 正向车道1（内侧车道）- 左边界
    boundary_segments.append(LaneBoundarySegment(
        segment_id=1,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=-1.75, z=0.0),
            Point3D(x=-10.0, y=-1.75, z=0.0),
        ]
    ))
    
    # 正向车道1（内侧车道）- 弯道左边界
    curve_points_f1_left = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 11.75 * math.sin(rad)
        y = -1.75 + 11.75 * (1 - math.cos(rad))
        curve_points_f1_left.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=2,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=curve_points_f1_left
    ))
    
    # 正向车道1（内侧车道）- 出口左边界
    boundary_segments.append(LaneBoundarySegment(
        segment_id=3,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=1.75, y=10.0, z=0.0),
            Point3D(x=1.75, y=50.0, z=0.0),
        ]
    ))
    
    # ==================== 中间分隔线 (Centerline Divider) ====================
    # 直道中间线
    boundary_segments.append(LaneBoundarySegment(
        segment_id=4,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DOUBLE_SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.20,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=0.0, z=0.0),
            Point3D(x=-10.0, y=0.0, z=0.0),
        ]
    ))
    
    # 弯道中间线
    curve_points_center = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 10.0 * math.sin(rad)
        y = 10.0 * (1 - math.cos(rad))
        curve_points_center.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=5,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DOUBLE_SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.20,
        is_virtual=False,
        boundary_points=curve_points_center
    ))
    
    # 出口中间线
    boundary_segments.append(LaneBoundarySegment(
        segment_id=6,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DOUBLE_SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.20,
        is_virtual=False,
        boundary_points=[
            Point3D(x=0.0, y=10.0, z=0.0),
            Point3D(x=0.0, y=50.0, z=0.0),
        ]
    ))
    
    # ==================== 正向车道2（外侧车道）- 右边界 ====================
    # 直道右边界
    boundary_segments.append(LaneBoundarySegment(
        segment_id=7,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=1.75, z=0.0),
            Point3D(x=-10.0, y=1.75, z=0.0),
        ]
    ))
    
    # 弯道右边界
    curve_points_f2_right = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 8.25 * math.sin(rad)
        y = 1.75 + 8.25 * (1 - math.cos(rad))
        curve_points_f2_right.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=8,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=curve_points_f2_right
    ))
    
    # 出口右边界
    boundary_segments.append(LaneBoundarySegment(
        segment_id=9,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-1.75, y=10.0, z=0.0),
            Point3D(x=-1.75, y=50.0, z=0.0),
        ]
    ))
    
    # ==================== 反向车道边界 (Backward Direction Lanes) ====================
    # 反向车道1（内侧车道）- 左边界（即正向车道的右边界）
    # 已经在上面添加了segment_id=7,8,9
    
    # 反向车道2（外侧车道）- 右边界
    boundary_segments.append(LaneBoundarySegment(
        segment_id=10,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=3.5, z=0.0),
            Point3D(x=-10.0, y=3.5, z=0.0),
        ]
    ))
    
    # 弯道右边界（反向车道2）
    curve_points_b2_right = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 6.5 * math.sin(rad)
        y = 3.5 + 6.5 * (1 - math.cos(rad))
        curve_points_b2_right.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=11,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=curve_points_b2_right
    ))
    
    # 出口右边界（反向车道2）
    boundary_segments.append(LaneBoundarySegment(
        segment_id=12,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.SOLID,
        boundary_color=BoundaryColor.YELLOW,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-3.5, y=10.0, z=0.0),
            Point3D(x=-3.5, y=50.0, z=0.0),
        ]
    ))
    
    # 反向车道1与车道2之间的分隔线
    boundary_segments.append(LaneBoundarySegment(
        segment_id=13,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-50.0, y=1.75, z=0.0),
            Point3D(x=-10.0, y=1.75, z=0.0),
        ]
    ))
    
    # 弯道分隔线（反向车道1与车道2之间）
    curve_points_b_divider = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 8.25 * math.sin(rad)
        y = 1.75 + 8.25 * (1 - math.cos(rad))
        curve_points_b_divider.append(Point3D(x=x, y=y, z=0.0))
    
    boundary_segments.append(LaneBoundarySegment(
        segment_id=14,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=curve_points_b_divider
    ))
    
    # 出口分隔线（反向车道1与车道2之间）
    boundary_segments.append(LaneBoundarySegment(
        segment_id=15,
        boundary_type=BoundaryType.LINE,
        boundary_line_shape=BoundaryLineShape.DASHED,
        boundary_color=BoundaryColor.WHITE,
        boundary_thickness=0.15,
        is_virtual=False,
        boundary_points=[
            Point3D(x=-1.75, y=10.0, z=0.0),
            Point3D(x=-1.75, y=50.0, z=0.0),
        ]
    ))
    
    local_map.boundary_segments.extend(boundary_segments)
    
    # ==================== 创建车道 / Create Lanes ====================
    # 双向四车道：2个方向 x 2车道 = 4车道
    # 每个车道分为3段：直道、弯道、出口
    # Bidirectional 4 lanes: 2 directions x 2 lanes = 4 lanes
    # Each lane has 3 segments: straight, curve, exit
    # 车道宽度统一为1.75米 / Lane width is 1.75m
    
    lanes = []
    
    # ==================== 正向车道1（内侧车道）Forward Lane 1 (Inner) ====================
    # 直道部分 - 中心线在 y=-0.875
    f1_straight_centerline = [
        Point3D(x=-50.0, y=-0.875, z=0.0),
        Point3D(x=-40.0, y=-0.875, z=0.0),
        Point3D(x=-30.0, y=-0.875, z=0.0),
        Point3D(x=-20.0, y=-0.875, z=0.0),
        Point3D(x=-10.0, y=-0.875, z=0.0),
    ]
    
    lane_f1_straight = Lane(
        lane_id=1,
        original_lane_id=1,
        original_road_id=100,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f1_straight_centerline,
        left_boundary_segment_indices=[0],  # segment_id=1 (y=-1.75)
        right_boundary_segment_indices=[3],  # segment_id=4 (y=0.0)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=1,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-50.0, y=-0.875, z=0.0),
                end_position=Point3D(x=-10.0, y=-0.875, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=2,
        predecessor_lane_ids=[],
        successor_lane_ids=[4],  # Connect to curve lane
        road_id=hash("RightAngleTurn_100"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_f1_straight)
    
    # 弯道部分 - 90度右转，半径10.875米
    f1_curve_centerline = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 10.875 * math.sin(rad)
        y = 10.875 * (1 - math.cos(rad))
        f1_curve_centerline.append(Point3D(x=x, y=y, z=0.0))
    
    lane_f1_curve = Lane(
        lane_id=4,
        original_lane_id=1,
        original_road_id=200,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f1_curve_centerline,
        left_boundary_segment_indices=[1],  # segment_id=2 (radius 11.75m)
        right_boundary_segment_indices=[4],  # segment_id=5 (radius 10m)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=4,
                speed_limit=8.33,  # 30 km/h
                start_position=Point3D(x=-10.0, y=-0.875, z=0.0),
                end_position=Point3D(x=0.875, y=10.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=5,
        predecessor_lane_ids=[1],  # From straight lane
        successor_lane_ids=[7],  # Connect to exit lane
        road_id=hash("RightAngleTurn_200"),
        junction_id=hash("RightAngleTurn_999"),
        is_junction_lane=True
    )
    lanes.append(lane_f1_curve)
    
    # 出口直道部分 - 中心线在 x=0.875
    f1_exit_centerline = [
        Point3D(x=0.875, y=10.0, z=0.0),
        Point3D(x=0.875, y=20.0, z=0.0),
        Point3D(x=0.875, y=30.0, z=0.0),
        Point3D(x=0.875, y=40.0, z=0.0),
        Point3D(x=0.875, y=50.0, z=0.0),
    ]
    
    lane_f1_exit = Lane(
        lane_id=7,
        original_lane_id=1,
        original_road_id=300,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f1_exit_centerline,
        left_boundary_segment_indices=[2],  # segment_id=3 (x=1.75)
        right_boundary_segment_indices=[5],  # segment_id=6 (x=0.0)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=7,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=0.875, y=10.0, z=0.0),
                end_position=Point3D(x=0.875, y=50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=8,
        predecessor_lane_ids=[4],  # From curve lane
        successor_lane_ids=[],
        road_id=hash("RightAngleTurn_300"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_f1_exit)
    
    # ==================== 正向车道2（外侧车道）Forward Lane 2 (Outer) ====================
    # 直道部分 - 中心线在 y=0.875
    f2_straight_centerline = [
        Point3D(x=-50.0, y=0.875, z=0.0),
        Point3D(x=-40.0, y=0.875, z=0.0),
        Point3D(x=-30.0, y=0.875, z=0.0),
        Point3D(x=-20.0, y=0.875, z=0.0),
        Point3D(x=-10.0, y=0.875, z=0.0),
    ]
    
    lane_f2_straight = Lane(
        lane_id=2,
        original_lane_id=2,
        original_road_id=100,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f2_straight_centerline,
        left_boundary_segment_indices=[3],  # segment_id=4 (y=0.0)
        right_boundary_segment_indices=[6],  # segment_id=7 (y=1.75)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=2,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-50.0, y=0.875, z=0.0),
                end_position=Point3D(x=-10.0, y=0.875, z=0.0)
            )
        ],
        left_adjacent_lane_id=1,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[],
        successor_lane_ids=[5],  # Connect to curve lane
        road_id=hash("RightAngleTurn_100"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_f2_straight)
    
    # 弯道部分 - 90度右转，半径9.125米
    f2_curve_centerline = []
    for angle in range(0, 91, 10):
        rad = math.radians(angle)
        x = -10.0 + 9.125 * math.sin(rad)
        y = 9.125 * (1 - math.cos(rad))
        f2_curve_centerline.append(Point3D(x=x, y=y, z=0.0))
    
    lane_f2_curve = Lane(
        lane_id=5,
        original_lane_id=2,
        original_road_id=200,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f2_curve_centerline,
        left_boundary_segment_indices=[4],  # segment_id=5 (radius 10m)
        right_boundary_segment_indices=[7],  # segment_id=8 (radius 8.25m)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=5,
                speed_limit=8.33,  # 30 km/h
                start_position=Point3D(x=-10.0, y=0.875, z=0.0),
                end_position=Point3D(x=-0.875, y=10.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=4,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[2],  # From straight lane
        successor_lane_ids=[8],  # Connect to exit lane
        road_id=hash("RightAngleTurn_200"),
        junction_id=hash("RightAngleTurn_999"),
        is_junction_lane=True
    )
    lanes.append(lane_f2_curve)
    
    # 出口直道部分 - 中心线在 x=-0.875
    f2_exit_centerline = [
        Point3D(x=-0.875, y=10.0, z=0.0),
        Point3D(x=-0.875, y=20.0, z=0.0),
        Point3D(x=-0.875, y=30.0, z=0.0),
        Point3D(x=-0.875, y=40.0, z=0.0),
        Point3D(x=-0.875, y=50.0, z=0.0),
    ]
    
    lane_f2_exit = Lane(
        lane_id=8,
        original_lane_id=2,
        original_road_id=300,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.FORWARD,
        centerline_points=f2_exit_centerline,
        left_boundary_segment_indices=[5],  # segment_id=6 (x=0.0)
        right_boundary_segment_indices=[8],  # segment_id=9 (x=-1.75)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=8,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-0.875, y=10.0, z=0.0),
                end_position=Point3D(x=-0.875, y=50.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=7,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[5],  # From curve lane
        successor_lane_ids=[],
        road_id=hash("RightAngleTurn_300"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_f2_exit)
    
    # ==================== 反向车道1（内侧车道）Backward Lane 1 (Inner) ====================
    # 直道部分 - 中心线在 x=-0.875 (注意：反向车道，所以x坐标相同但y坐标相反)
    b1_straight_centerline = [
        Point3D(x=-0.875, y=50.0, z=0.0),
        Point3D(x=-0.875, y=40.0, z=0.0),
        Point3D(x=-0.875, y=30.0, z=0.0),
        Point3D(x=-0.875, y=20.0, z=0.0),
        Point3D(x=-0.875, y=10.0, z=0.0),
    ]
    
    lane_b1_straight = Lane(
        lane_id=3,
        original_lane_id=-1,
        original_road_id=101,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.BACKWARD,  # 反向车道
        centerline_points=b1_straight_centerline,
        left_boundary_segment_indices=[8],  # segment_id=9 (x=-1.75)
        right_boundary_segment_indices=[5],  # segment_id=6 (x=0.0)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=3,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-0.875, y=50.0, z=0.0),
                end_position=Point3D(x=-0.875, y=10.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=6,
        predecessor_lane_ids=[],  # 反向车道，前驱为空
        successor_lane_ids=[9],  # Connect to curve lane
        road_id=hash("RightAngleTurn_101"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_b1_straight)
    
    # 弯道部分 - 90度左转，半径9.125米 (反向行驶)
    b1_curve_centerline = []
    for angle in range(90, -1, -10):
        rad = math.radians(angle)
        x = -10.0 + 9.125 * math.sin(rad)
        y = 9.125 * (1 - math.cos(rad))
        b1_curve_centerline.append(Point3D(x=x, y=y, z=0.0))
    
    lane_b1_curve = Lane(
        lane_id=9,
        original_lane_id=-1,
        original_road_id=201,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.BACKWARD,  # 反向车道
        centerline_points=b1_curve_centerline,
        left_boundary_segment_indices=[7],  # segment_id=8 (radius 8.25m)
        right_boundary_segment_indices=[4],  # segment_id=5 (radius 10m)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=9,
                speed_limit=8.33,  # 30 km/h
                start_position=Point3D(x=-0.875, y=10.0, z=0.0),
                end_position=Point3D(x=-10.0, y=0.875, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=10,
        predecessor_lane_ids=[3],  # From straight lane
        successor_lane_ids=[11],  # Connect to exit lane
        road_id=hash("RightAngleTurn_201"),
        junction_id=hash("RightAngleTurn_999"),
        is_junction_lane=True
    )
    lanes.append(lane_b1_curve)
    
    # 出口直道部分 - 中心线在 y=0.875 (反向行驶)
    b1_exit_centerline = [
        Point3D(x=-10.0, y=0.875, z=0.0),
        Point3D(x=-20.0, y=0.875, z=0.0),
        Point3D(x=-30.0, y=0.875, z=0.0),
        Point3D(x=-40.0, y=0.875, z=0.0),
        Point3D(x=-50.0, y=0.875, z=0.0),
    ]
    
    lane_b1_exit = Lane(
        lane_id=11,
        original_lane_id=-1,
        original_road_id=301,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.BACKWARD,  # 反向车道
        centerline_points=b1_exit_centerline,
        left_boundary_segment_indices=[6],  # segment_id=7 (y=1.75)
        right_boundary_segment_indices=[3],  # segment_id=4 (y=0.0)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=11,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-10.0, y=0.875, z=0.0),
                end_position=Point3D(x=-50.0, y=0.875, z=0.0)
            )
        ],
        left_adjacent_lane_id=None,
        right_adjacent_lane_id=12,
        predecessor_lane_ids=[9],  # From curve lane
        successor_lane_ids=[],  # 反向车道，后继为空
        road_id=hash("RightAngleTurn_301"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_b1_exit)
    
    # ==================== 反向车道2（外侧车道）Backward Lane 2 (Outer) ====================
    # 直道部分 - 中心线在 x=0.875 (注意：反向车道，所以x坐标相同但y坐标相反)
    b2_straight_centerline = [
        Point3D(x=0.875, y=50.0, z=0.0),
        Point3D(x=0.875, y=40.0, z=0.0),
        Point3D(x=0.875, y=30.0, z=0.0),
        Point3D(x=0.875, y=20.0, z=0.0),
        Point3D(x=0.875, y=10.0, z=0.0),
    ]
    
    lane_b2_straight = Lane(
        lane_id=6,
        original_lane_id=-2,
        original_road_id=101,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.BACKWARD,  # 反向车道
        centerline_points=b2_straight_centerline,
        left_boundary_segment_indices=[5],  # segment_id=6 (x=0.0)
        right_boundary_segment_indices=[2],  # segment_id=3 (x=1.75)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=6,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=0.875, y=50.0, z=0.0),
                end_position=Point3D(x=0.875, y=10.0, z=0.0)
            )
        ],
        left_adjacent_lane_id=3,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[],  # 反向车道，前驱为空
        successor_lane_ids=[10],  # Connect to curve lane
        road_id=hash("RightAngleTurn_101"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_b2_straight)
    
    # 弯道部分 - 90度左转，半径10.875米 (反向行驶)
    b2_curve_centerline = []
    for angle in range(90, -1, -10):
        rad = math.radians(angle)
        x = -10.0 + 10.875 * math.sin(rad)
        y = 10.875 * (1 - math.cos(rad))
        b2_curve_centerline.append(Point3D(x=x, y=y, z=0.0))
    
    lane_b2_curve = Lane(
        lane_id=10,
        original_lane_id=-2,
        original_road_id=201,
        original_junction_id=999,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.BACKWARD,  # 反向车道
        centerline_points=b2_curve_centerline,
        left_boundary_segment_indices=[4],  # segment_id=5 (radius 10m)
        right_boundary_segment_indices=[1],  # segment_id=2 (radius 11.75m)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=10,
                speed_limit=8.33,  # 30 km/h
                start_position=Point3D(x=0.875, y=10.0, z=0.0),
                end_position=Point3D(x=-10.0, y=-0.875, z=0.0)
            )
        ],
        left_adjacent_lane_id=9,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[6],  # From straight lane
        successor_lane_ids=[12],  # Connect to exit lane
        road_id=hash("RightAngleTurn_201"),
        junction_id=hash("RightAngleTurn_999"),
        is_junction_lane=True
    )
    lanes.append(lane_b2_curve)
    
    # 出口直道部分 - 中心线在 y=-0.875 (反向行驶)
    b2_exit_centerline = [
        Point3D(x=-10.0, y=-0.875, z=0.0),
        Point3D(x=-20.0, y=-0.875, z=0.0),
        Point3D(x=-30.0, y=-0.875, z=0.0),
        Point3D(x=-40.0, y=-0.875, z=0.0),
        Point3D(x=-50.0, y=-0.875, z=0.0),
    ]
    
    lane_b2_exit = Lane(
        lane_id=12,
        original_lane_id=-2,
        original_road_id=301,
        original_junction_id=None,
        map_source_type="XODR",
        map_source_id="RightAngleTurn",
        lane_type=LaneType.DRIVING,
        lane_direction=LaneDirection.BACKWARD,  # 反向车道
        centerline_points=b2_exit_centerline,
        left_boundary_segment_indices=[3],  # segment_id=4 (y=0.0)
        right_boundary_segment_indices=[0],  # segment_id=1 (y=-1.75)
        speed_limits=[
            SpeedLimitSegment(
                segment_id=12,
                speed_limit=16.67,  # 60 km/h
                start_position=Point3D(x=-10.0, y=-0.875, z=0.0),
                end_position=Point3D(x=-50.0, y=-0.875, z=0.0)
            )
        ],
        left_adjacent_lane_id=11,
        right_adjacent_lane_id=None,
        predecessor_lane_ids=[10],  # From curve lane
        successor_lane_ids=[],  # 反向车道，后继为空
        road_id=hash("RightAngleTurn_301"),
        junction_id=None,
        is_junction_lane=False
    )
    lanes.append(lane_b2_exit)
    
    local_map.lanes.extend(lanes)
    
    # ==================== 添加交通信号灯 / Add Traffic Lights ====================
    # 在弯道入口添加交通信号灯（两个方向）
    # 正向交通灯
    traffic_light_forward = TrafficLight(
        traffic_light_id=1,
        associated_lane_id=1,  # 关联正向直道车道
        position=Point3D(x=-12.0, y=-2.0, z=5.0),
        current_state=TrafficLightState(
            timestamp=datetime.now(),
            color=TrafficLightColor.GREEN,
            shape=None,
            status=None,
            remaining_time=30.0
        ),
        distance_to_stop_line=2.0,
        associated_stop_line_id=0,
        light_type=None,
        confidence=1.0
    )
    local_map.traffic_lights.append(traffic_light_forward)
    
    # 反向交通灯
    traffic_light_backward = TrafficLight(
        traffic_light_id=2,
        associated_lane_id=3,  # 关联反向直道车道
        position=Point3D(x=-2.0, y=12.0, z=5.0),
        current_state=TrafficLightState(
            timestamp=datetime.now(),
            color=TrafficLightColor.RED,
            shape=None,
            status=None,
            remaining_time=30.0
        ),
        distance_to_stop_line=2.0,
        associated_stop_line_id=0,
        light_type=None,
        confidence=1.0
    )
    local_map.traffic_lights.append(traffic_light_backward)
    
    # ==================== 添加交通标志 / Add Traffic Signs ====================
    # 添加限速标志（两个方向）
    for lane_id, x, y in [(1, -40.0, -2.0), (3, -2.0, 40.0)]:
        traffic_sign = TrafficSign(
            traffic_sign_id=len(local_map.traffic_signs) + 1,
            associated_lane_id=lane_id,
            position=Point3D(x=x, y=y, z=3.0),
            sign_type=TrafficSignType.SPEED_LIMIT,
            distance_to_sign=5.0,
            value=60.0,  # 60 km/h
            text_content="60",
            confidence=1.0,
            is_valid=True,
            valid_until=None
        )
        local_map.traffic_signs.append(traffic_sign)
    
    # 添加弯道警告标志（两个方向）
    traffic_sign_curve_forward = TrafficSign(
        traffic_sign_id=len(local_map.traffic_signs) + 1,
        associated_lane_id=4,
        position=Point3D(x=-12.0, y=2.0, z=3.0),
        sign_type=TrafficSignType.CURVE_RIGHT,  # 右急弯 / Right curve
        distance_to_sign=5.0,
        value=None,
        text_content="Right Turn",
        confidence=1.0,
        is_valid=True,
        valid_until=None
    )
    local_map.traffic_signs.append(traffic_sign_curve_forward)
    
    traffic_sign_curve_backward = TrafficSign(
        traffic_sign_id=len(local_map.traffic_signs) + 1,
        associated_lane_id=9,
        position=Point3D(x=2.0, y=12.0, z=3.0),
        sign_type=TrafficSignType.CURVE_LEFT,  # 左急弯 / Left curve (反向行驶)
        distance_to_sign=5.0,
        value=None,
        text_content="Left Turn",
        confidence=1.0,
        is_valid=True,
        valid_until=None
    )
    local_map.traffic_signs.append(traffic_sign_curve_backward)
    
    return local_map
