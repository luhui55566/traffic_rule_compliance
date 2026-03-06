#!/usr/bin/env python3
"""
LocalMapProcessor - 局部地图处理子模块

负责处理局部地图数据，包括判定自车所在车道。

主要功能:
    - 局部地图透传
    - 判定自车所在车道（egolane）
    - 获取自车车道信息
    - 判定自车与车道边界的关系

注意:
    - 车道中心线的航向不区分0和pi（正向和反向）
    - 在判断航向一致性时，需要考虑自车行进方向与车道方向的关系
"""

import math
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from enum import IntEnum

# 导入局部地图数据类型
from common.local_map.local_map_data import LocalMap, Lane, Point3D, BoundaryType

# 导入通用数据类型
from common.ego_vehicle_state import EgoVehicleState

# 配置日志
logger = logging.getLogger(__name__)


class EgoLaneContainmentType(IntEnum):
    """自车与车道边界的包含关系枚举"""
    UNKNOWN = 0                # 未知（无法判定）
    CENTER_INSIDE = 1          # 自车中心点在车道边界内，但轮廓部分在边界外
    FULLY_INSIDE = 2           # 车辆外轮廓都在边界内
    CENTER_OUTSIDE = 3         # 自车中心点在车道边界外


@dataclass
class EgoLaneResult:
    """自车车道判定结果"""
    lane_id: Optional[int] = None                      # 车道ID
    lane: Optional[Lane] = None                        # 车道对象
    containment_type: EgoLaneContainmentType = EgoLaneContainmentType.UNKNOWN  # 包含关系
    distance_to_centerline: float = float('inf')       # 到中心线的距离
    distance_to_left_boundary: float = float('inf')    # 到左边界的距离
    distance_to_right_boundary: float = float('inf')   # 到右边界的距离
    longitudinal_ratio: float = 0.0                    # 纵向位置比例（0-1）
    heading_diff: float = 0.0                          # 航向差（弧度，考虑方向后的最小差值）


class LocalMapProcessor:
    """
    局部地图处理器
    
    负责处理局部地图数据，包括判定自车所在车道。
    
    航向判断说明:
        车道中心线的航向不区分0和pi（正向和反向），因为中心线本身没有方向性。
        在判断自车航向与车道航向是否一致时，我们计算两个方向的航向差：
        - 正向航向差：直接计算的航向差
        - 反向航向差：将车道航向旋转pi后的航向差
        取较小的那个作为最终的航向差，如果小于阈值则认为航向一致。
    """
    
    # 默认参数
    DEFAULT_MAX_DISTANCE_TO_LANE = 5.0       # 自车到车道的最大距离（米）
    DEFAULT_MAX_HEADING_DIFF = math.pi / 4   # 自车与车道方向的最大航向差（弧度）
    DEFAULT_VEHICLE_LENGTH = 4.5             # 默认车长（米）
    DEFAULT_VEHICLE_WIDTH = 1.8              # 默认车宽（米）
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化局部地图处理器
        
        Args:
            config: 配置字典
        """
        # 配置参数
        env_config = config.get('env_node', {})
        vehicle_config = config.get('vehicle', {})
        
        self.max_distance_to_lane = env_config.get('max_distance_to_lane', self.DEFAULT_MAX_DISTANCE_TO_LANE)
        self.max_heading_diff = env_config.get('max_heading_diff', self.DEFAULT_MAX_HEADING_DIFF)
        
        # 车辆尺寸（从配置文件读取）
        self.vehicle_length = vehicle_config.get('length', self.DEFAULT_VEHICLE_LENGTH)
        self.vehicle_width = vehicle_config.get('width', self.DEFAULT_VEHICLE_WIDTH)
    
    def reset(self) -> None:
        """重置局部地图处理器"""
        pass
    
    def get_local_map_origin_tuple(
        self,
        local_map: Optional[LocalMap]
    ) -> Optional[tuple]:
        """
        获取局部地图原点的元组表示（用于比较）
        
        Args:
            local_map: 局部地图
            
        Returns:
            Optional[tuple]: (x, y, heading) 元组，如果没有局部地图则返回None
        """
        if local_map is not None and hasattr(local_map, 'metadata'):
            metadata = local_map.metadata
            return (metadata.ego_vehicle_x, metadata.ego_vehicle_y, metadata.ego_vehicle_heading)
        return None
    
    def find_ego_lane(
        self,
        ego_state: EgoVehicleState,
        local_map: LocalMap
    ) -> EgoLaneResult:
        """
        查找自车所在的车道
        
        通过以下条件判定自车所在车道：
        1. 自车中心点在车道边界内（如果车道边界非虚拟）
        2. 自车位置到车道中心线的距离最小
        3. 自车航向与车道方向一致（考虑正反两个方向）
        4. 自车在车道的纵向范围内
        
        Args:
            ego_state: 自车状态（统一格式）
            local_map: 局部地图
            
        Returns:
            EgoLaneResult: 自车车道判定结果
        """
        result = EgoLaneResult()
        
        if ego_state is None or ego_state.local_state is None:
            return result
        
        if local_map is None or not hasattr(local_map, 'lanes'):
            return result
        
        ego_pos = ego_state.local_state.position
        ego_yaw = ego_state.local_state.orientation.yaw
        
        best_result = None
        best_distance = float('inf')
        
        for lane in local_map.lanes:
            # 检查车道是否有中心线
            if not lane.centerline_points:
                continue
            
            # 检查车道类型是否为可通行类型（只考虑DRIVING类型的车道）
            from common.local_map.local_map_data import LaneType
            if lane.lane_type != LaneType.DRIVING:
                logger.debug(f"跳过非行驶车道: lane_id={lane.lane_id}, type={lane.lane_type.name}")
                continue
            
            # 获取车道边界点（提前获取，用于快速过滤）
            left_boundary_points = self._get_boundary_points(lane.left_boundary_segment_indices, local_map)
            right_boundary_points = self._get_boundary_points(lane.right_boundary_segment_indices, local_map)
            
            # 首先检查自车中心点是否在车道边界内（快速过滤）
            if left_boundary_points and right_boundary_points:
                if not self._is_point_in_lane_boundary(ego_pos, left_boundary_points, right_boundary_points):
                    continue
            
            # 计算自车到车道中心线的最小距离
            min_dist, closest_idx, longitudinal_ratio = self._calculate_distance_to_lane(
                ego_pos, lane.centerline_points
            )
            
            # 检查自车是否在车道的纵向范围内
            if longitudinal_ratio < 0 or longitudinal_ratio > 1:
                continue
            
            # 计算车道在最近点处的航向
            lane_heading = self._get_lane_heading_at_index(lane.centerline_points, closest_idx)
            
            # 计算航向差（考虑正反两个方向）
            heading_diff = self._calculate_heading_diff_bidirectional(ego_yaw, lane_heading)
            
            # 检查航向差异
            if heading_diff > self.max_heading_diff:
                continue
            
            # 计算到左右边界的距离
            dist_to_left, dist_to_right = self._calculate_distance_to_boundaries(
                ego_pos, left_boundary_points, right_boundary_points
            )
            
            # 检查自车与车道边界的完整包含关系
            containment_type = self._check_containment(
                ego_pos, ego_yaw, lane, local_map, left_boundary_points, right_boundary_points
            )
            
            # 选择距离最小的车道
            if min_dist < best_distance:
                best_distance = min_dist
                best_result = EgoLaneResult(
                    lane_id=lane.lane_id,
                    lane=lane,
                    containment_type=containment_type,
                    distance_to_centerline=min_dist,
                    distance_to_left_boundary=dist_to_left,
                    distance_to_right_boundary=dist_to_right,
                    longitudinal_ratio=longitudinal_ratio,
                    heading_diff=heading_diff
                )
        
        return best_result if best_result else result
    
    def find_ego_lane_id(
        self,
        ego_state: EgoVehicleState,
        local_map: LocalMap
    ) -> Optional[int]:
        """
        查找自车所在车道的ID
        
        Args:
            ego_state: 自车状态（统一格式）
            local_map: 局部地图
            
        Returns:
            Optional[int]: 自车所在车道ID，如果未找到则返回None
        """
        result = self.find_ego_lane(ego_state, local_map)
        return result.lane_id
    
    def get_ego_lane_info(
        self,
        ego_state: EgoVehicleState,
        local_map: LocalMap
    ) -> Dict[str, Any]:
        """
        获取自车车道的详细信息
        
        Args:
            ego_state: 自车状态（统一格式）
            local_map: 局部地图
            
        Returns:
            Dict[str, Any]: 自车车道信息字典
        """
        result = self.find_ego_lane(ego_state, local_map)
        
        if result.lane is None:
            return {
                'found': False,
                'lane_id': None,
                'containment_type': EgoLaneContainmentType.UNKNOWN.name,
                'distance_to_centerline': float('inf'),
                'distance_to_left_boundary': float('inf'),
                'distance_to_right_boundary': float('inf'),
                'lane_type': None,
                'speed_limit': None,
                'left_lane_id': None,
                'right_lane_id': None
            }
        
        lane = result.lane
        
        # 获取限速信息
        speed_limit = None
        if lane.max_speed_limits:
            # 取第一个点的限速值
            speed_limit = lane.max_speed_limits[0]
        
        return {
            'found': True,
            'lane_id': lane.lane_id,
            'containment_type': result.containment_type.name,
            'distance_to_centerline': result.distance_to_centerline,
            'distance_to_left_boundary': result.distance_to_left_boundary,
            'distance_to_right_boundary': result.distance_to_right_boundary,
            'longitudinal_ratio': result.longitudinal_ratio,
            'heading_diff': result.heading_diff,
            'lane_type': lane.lane_type.name if lane.lane_type else None,
            'speed_limit': speed_limit,
            'left_lane_id': lane.left_adjacent_lane_id,
            'right_lane_id': lane.right_adjacent_lane_id,
            'original_road_id': lane.original_road_id,
            'original_lane_id': lane.original_lane_id
        }
    
    def _calculate_heading_diff_bidirectional(self, ego_yaw: float, lane_heading: float) -> float:
        """
        计算自车航向与车道航向的双向差异
        
        由于车道中心线的航向不区分0和pi（正向和反向），
        我们需要计算两个方向的航向差，取较小的那个。
        
        Args:
            ego_yaw: 自车航向（弧度）
            lane_heading: 车道航向（弧度）
            
        Returns:
            float: 最小的航向差（弧度，0到pi/2之间）
        """
        # 计算正向航向差
        forward_diff = abs(self._normalize_angle(ego_yaw - lane_heading))
        
        # 计算反向航向差（车道航向旋转pi）
        reverse_diff = abs(self._normalize_angle(ego_yaw - (lane_heading + math.pi)))
        
        # 取较小的那个
        return min(forward_diff, reverse_diff)
    
    def _calculate_distance_to_boundaries(
        self,
        ego_pos: Point3D,
        left_boundary: List[Point3D],
        right_boundary: List[Point3D]
    ) -> Tuple[float, float]:
        """
        计算自车到左右边界的距离（到边界线段的垂直距离）
        
        改进：使用点到线段的距离，而不是点到点的距离，
        这样即使边界点稀疏（3-5米间距）也能准确计算距离。
        
        Args:
            ego_pos: 自车位置
            left_boundary: 左边界点集
            right_boundary: 右边界点集
            
        Returns:
            Tuple[float, float]: (到左边界距离, 到右边界距离)
        """
        dist_to_left = float('inf')
        dist_to_right = float('inf')
        
        if left_boundary and len(left_boundary) >= 2:
            min_dist = float('inf')
            # 计算到每条边界线段的距离
            for i in range(len(left_boundary) - 1):
                dist = self._point_to_segment_distance(
                    ego_pos, left_boundary[i], left_boundary[i + 1]
                )
                if dist < min_dist:
                    min_dist = dist
            dist_to_left = min_dist
        elif left_boundary:
            # 只有一个点的情况，退化为点到点距离
            min_dist = float('inf')
            for pt in left_boundary:
                dist = math.sqrt((ego_pos.x - pt.x)**2 + (ego_pos.y - pt.y)**2)
                if dist < min_dist:
                    min_dist = dist
            dist_to_left = min_dist
        
        if right_boundary and len(right_boundary) >= 2:
            min_dist = float('inf')
            # 计算到每条边界线段的距离
            for i in range(len(right_boundary) - 1):
                dist = self._point_to_segment_distance(
                    ego_pos, right_boundary[i], right_boundary[i + 1]
                )
                if dist < min_dist:
                    min_dist = dist
            dist_to_right = min_dist
        elif right_boundary:
            # 只有一个点的情况，退化为点到点距离
            min_dist = float('inf')
            for pt in right_boundary:
                dist = math.sqrt((ego_pos.x - pt.x)**2 + (ego_pos.y - pt.y)**2)
                if dist < min_dist:
                    min_dist = dist
            dist_to_right = min_dist
        
        return dist_to_left, dist_to_right
    
    def _point_to_segment_distance(
        self,
        point: Point3D,
        seg_start: Point3D,
        seg_end: Point3D
    ) -> float:
        """
        计算点到线段的最短距离
        
        Args:
            point: 待计算的点
            seg_start: 线段起点
            seg_end: 线段终点
            
        Returns:
            float: 点到线段的最短距离
        """
        # 线段向量
        dx = seg_end.x - seg_start.x
        dy = seg_end.y - seg_start.y
        
        # 线段长度的平方
        seg_len_sq = dx * dx + dy * dy
        
        if seg_len_sq < 1e-10:
            # 线段退化为点
            return math.sqrt((point.x - seg_start.x)**2 + (point.y - seg_start.y)**2)
        
        # 计算投影参数 t（0表示在起点，1表示在终点）
        t = ((point.x - seg_start.x) * dx + (point.y - seg_start.y) * dy) / seg_len_sq
        t = max(0, min(1, t))  # 限制在 [0, 1] 范围内
        
        # 计算投影点
        proj_x = seg_start.x + t * dx
        proj_y = seg_start.y + t * dy
        
        # 返回点到投影点的距离
        return math.sqrt((point.x - proj_x)**2 + (point.y - proj_y)**2)
    
    def _check_containment(
        self,
        ego_pos: Point3D,
        ego_yaw: float,
        lane: Lane,
        local_map: LocalMap,
        left_boundary: List[Point3D],
        right_boundary: List[Point3D]
    ) -> EgoLaneContainmentType:
        """
        检查自车与车道边界的包含关系
        
        Args:
            ego_pos: 自车位置
            ego_yaw: 自车航向
            lane: 车道对象
            local_map: 局部地图
            left_boundary: 左边界点集
            right_boundary: 右边界点集
            
        Returns:
            EgoLaneContainmentType: 包含关系类型
        """
        # 如果没有边界信息，使用中心线距离判定
        if not left_boundary or not right_boundary:
            min_dist, _, _ = self._calculate_distance_to_lane(ego_pos, lane.centerline_points)
            if min_dist <= self.max_distance_to_lane:
                return EgoLaneContainmentType.CENTER_INSIDE
            return EgoLaneContainmentType.CENTER_OUTSIDE
        
        # 检查自车中心点是否在边界内
        center_inside = self._is_point_in_lane_boundary(ego_pos, left_boundary, right_boundary)
        
        if not center_inside:
            return EgoLaneContainmentType.CENTER_OUTSIDE
        
        # 检查车辆外轮廓是否都在边界内
        vehicle_corners = self._get_vehicle_corners(ego_pos, ego_yaw)
        all_corners_inside = all(
            self._is_point_in_lane_boundary(corner, left_boundary, right_boundary)
            for corner in vehicle_corners
        )
        
        if all_corners_inside:
            return EgoLaneContainmentType.FULLY_INSIDE
        else:
            return EgoLaneContainmentType.CENTER_INSIDE
    
    def _get_boundary_points(
        self,
        boundary_indices: List[int],
        local_map: LocalMap
    ) -> List[Point3D]:
        """
        获取边界点集
        
        假设每个边界分段内部的点已经是按顺序的。
        当有多个分段时，按索引顺序连接。
        
        Args:
            boundary_indices: 边界分段索引列表
            local_map: 局部地图
            
        Returns:
            List[Point3D]: 边界点列表
        """
        points = []
        if not hasattr(local_map, 'boundary_segments'):
            return points
        
        for idx in boundary_indices:
            if 0 <= idx < len(local_map.boundary_segments):
                segment = local_map.boundary_segments[idx]
                points.extend(segment.boundary_points)
        
        return points
    

    def _is_point_in_lane_boundary(
        self,
        point: Point3D,
        left_boundary: List[Point3D],
        right_boundary: List[Point3D]
    ) -> bool:
        """
        检查点是否在车道边界内（优化版）
        
        使用叉积方法判断点是否在左右边界之间：
        1. 找到距离点最近的边界线段
        2. 使用叉积判断点是否在边界的正确一侧
        3. 点必须在左边界右侧且在右边界左侧才算在车道内
        
        Args:
            point: 待检查的点
            left_boundary: 左边界点集
            right_boundary: 右边界点集
            
        Returns:
            bool: 是否在边界内
        """
        if not left_boundary or not right_boundary:
            return False
        
        # 找到左边界上距离点最近的线段
        # 确保线段的两个端点不重合
        left_min_idx = self._find_closest_point_idx(point, left_boundary)
        if left_min_idx == 0:
            # 最近点是第一个点，使用第一条线段 [0, 1]
            left_segment_start = 0
            left_segment_end = min(1, len(left_boundary) - 1)
        elif left_min_idx == len(left_boundary) - 1:
            # 最近点是最后一个点，使用最后一条线段 [n-2, n-1]
            left_segment_start = max(0, len(left_boundary) - 2)
            left_segment_end = len(left_boundary) - 1
        else:
            # 使用包含最近点的线段 [min_idx-1, min_idx] 或 [min_idx, min_idx+1]
            # 选择距离更近的线段
            left_segment_start = left_min_idx
            left_segment_end = left_min_idx + 1
        
        # 找到右边界上距离点最近的线段
        right_min_idx = self._find_closest_point_idx(point, right_boundary)
        if right_min_idx == 0:
            right_segment_start = 0
            right_segment_end = min(1, len(right_boundary) - 1)
        elif right_min_idx == len(right_boundary) - 1:
            right_segment_start = max(0, len(right_boundary) - 2)
            right_segment_end = len(right_boundary) - 1
        else:
            right_segment_start = right_min_idx
            right_segment_end = right_min_idx + 1
        
        # 计算点相对于左边界线段的位置
        left_p1 = left_boundary[left_segment_start]
        left_p2 = left_boundary[left_segment_end]
        left_cross = self._cross_product(left_p1, left_p2, point)
        
        # 计算点相对于右边界线段的位置
        right_p1 = right_boundary[right_segment_start]
        right_p2 = right_boundary[right_segment_end]
        right_cross = self._cross_product(right_p1, right_p2, point)
        
        # 计算到左边界和右边界的最短距离
        min_dist_left = self._point_to_polyline_distance_optimized(point, left_boundary)
        min_dist_right = self._point_to_polyline_distance_optimized(point, right_boundary)
        
        # 计算左右边界之间的近似宽度（在最近点处）
        left_closest_pt = left_boundary[left_min_idx]
        right_closest_pt = right_boundary[right_min_idx]
        lane_width_estimate = math.sqrt(
            (left_closest_pt.x - right_closest_pt.x)**2 +
            (left_closest_pt.y - right_closest_pt.y)**2
        )
        
        # 判定逻辑：
        # 1. 点到两个边界的距离之和应该小于等于车道宽度（允许一定误差）
        dist_sum = min_dist_left + min_dist_right
        width_tolerance = 0.5  # 0.5米容差
        is_between_boundaries = dist_sum <= lane_width_estimate + width_tolerance
        
        # 2. 使用叉积确认点在边界之间
        # 如果叉积符号相反，说明点在两个边界之间
        cross_product_check = (left_cross > 0 and right_cross < 0) or (left_cross < 0 and right_cross > 0)
        
        result = is_between_boundaries and cross_product_check
        
        return result
    
    def _cross_product(
        self,
        p1: Point3D,
        p2: Point3D,
        p3: Point3D
    ) -> float:
        """
        计算向量 p1->p2 和 p1->p3 的叉积
        
        叉积结果：
        - 正值：p3 在 p1->p2 的左侧
        - 负值：p3 在 p1->p2 的右侧
        - 零：三点共线
        
        Args:
            p1: 线段起点
            p2: 线段终点
            p3: 待判断的点
            
        Returns:
            float: 叉积值
        """
        return (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x)
    
    def _point_to_polyline_distance_optimized(
        self, 
        point: Point3D, 
        polyline: List[Point3D]
    ) -> float:
        """
        计算点到折线的最短距离（优化版）
        
        步骤：
        1. 在有序点序列中找到距离最近的点（单峰搜索）
        2. 计算该点前后两条线段到目标点的垂直距离
        3. 取最小值
        
        Args:
            point: 目标点
            polyline: 有序点序列
            
        Returns:
            float: 最短距离
        """
        if not polyline:
            return float('inf')
        
        if len(polyline) == 1:
            # 只有一个点，直接计算点到点距离
            return math.sqrt((point.x - polyline[0].x)**2 + (point.y - polyline[0].y)**2)
        
        # 1. 找到距离最近的边界点（点到点距离，单峰搜索）
        min_idx = self._find_closest_point_idx(point, polyline)
        
        # 2. 计算到前后两条线段的垂直距离
        min_dist = float('inf')
        
        # 检查前一条线段：polyline[min_idx-1] -> polyline[min_idx]
        if min_idx > 0:
            dist = self._point_to_segment_distance(
                point, polyline[min_idx - 1], polyline[min_idx]
            )
            min_dist = min(min_dist, dist)
        
        # 检查后一条线段：polyline[min_idx] -> polyline[min_idx+1]
        if min_idx < len(polyline) - 1:
            dist = self._point_to_segment_distance(
                point, polyline[min_idx], polyline[min_idx + 1]
            )
            min_dist = min(min_dist, dist)
        
        # 如果只有一条线段的情况（只有一个方向的线段）
        if min_dist == float('inf'):
            # 退化情况：返回点到最近点的距离
            pt = polyline[min_idx]
            min_dist = math.sqrt((point.x - pt.x)**2 + (point.y - pt.y)**2)
        
        return min_dist
    
    def _find_closest_point_idx(self, point: Point3D, polyline: List[Point3D]) -> int:
        """
        在有序点序列中找到距离目标点最近的点的索引（单峰搜索）
        
        利用距离先减小后增大的特性，提前终止搜索
        
        Args:
            point: 目标点
            polyline: 有序点序列
            
        Returns:
            int: 最近点的索引
        """
        if not polyline:
            return -1
        
        min_dist = float('inf')
        min_idx = 0
        prev_dist = float('inf')
        
        for i, pt in enumerate(polyline):
            # 计算点到点距离
            dist = math.sqrt((point.x - pt.x)**2 + (point.y - pt.y)**2)
            
            # 更新最小值
            if dist < min_dist:
                min_dist = dist
                min_idx = i
            
            # 检查是否开始增大（过了最近点）
            # 如果当前距离大于前一个距离，且前一个距离已经是最小值附近
            if i > 0 and dist > prev_dist and prev_dist <= min_dist:
                # 距离开始增大，提前终止
                break
            
            prev_dist = dist
        
        return min_idx
    
    def _point_to_segment_distance(
        self, 
        point: Point3D, 
        p1: Point3D, 
        p2: Point3D
    ) -> float:
        """
        计算点到线段的最短距离（垂直距离）
        
        Args:
            point: 目标点
            p1: 线段起点
            p2: 线段终点
            
        Returns:
            float: 最短距离
        """
        # 线段向量
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        
        # 线段长度平方
        seg_len_sq = dx * dx + dy * dy
        
        if seg_len_sq == 0:
            # 两个点重合，退化成点
            return math.sqrt((point.x - p1.x)**2 + (point.y - p1.y)**2)
        
        # 计算投影参数 t (0 <= t <= 1 表示在线段上)
        t = ((point.x - p1.x) * dx + (point.y - p1.y) * dy) / seg_len_sq
        
        # 限制 t 在 [0, 1] 范围内
        t = max(0.0, min(1.0, t))
        
        # 最近点（垂足）坐标
        closest_x = p1.x + t * dx
        closest_y = p1.y + t * dy
        
        # 距离
        dist = math.sqrt((point.x - closest_x)**2 + (point.y - closest_y)**2)
        
        return dist

    def _get_vehicle_corners(
        self,
        ego_pos: Point3D,
        ego_yaw: float
    ) -> List[Point3D]:
        """
        获取车辆四个角的位置
        
        Args:
            ego_pos: 自车中心位置
            ego_yaw: 自车航向
            
        Returns:
            List[Point3D]: 四个角的位置列表
        """
        half_length = self.vehicle_length / 2
        half_width = self.vehicle_width / 2
        
        cos_yaw = math.cos(ego_yaw)
        sin_yaw = math.sin(ego_yaw)
        
        # 四个角在车辆坐标系中的位置
        corners_local = [
            (half_length, half_width),    # 前左
            (half_length, -half_width),   # 前右
            (-half_length, half_width),   # 后左
            (-half_length, -half_width),  # 后右
        ]
        
        # 转换到全局坐标系
        corners = []
        for lx, ly in corners_local:
            gx = ego_pos.x + lx * cos_yaw - ly * sin_yaw
            gy = ego_pos.y + lx * sin_yaw + ly * cos_yaw
            corners.append(Point3D(x=gx, y=gy, z=ego_pos.z))
        
        return corners
    
    def _calculate_distance_to_lane(
        self,
        ego_pos: Point3D,
        centerline_points: List[Point3D]
    ) -> Tuple[float, int, float]:
        """
        计算自车到车道中心线的距离（优化版）
        
        使用点到折线的垂直距离方法，更准确
        
        Args:
            ego_pos: 自车位置
            centerline_points: 车道中心线点集
            
        Returns:
            Tuple[float, int, float]: (最小距离, 最近点索引, 纵向比例)
        """
        if not centerline_points:
            return float('inf'), 0, 0.0
        
        if len(centerline_points) == 1:
            # 只有一个点，直接计算点到点距离
            dist = math.sqrt(
                (ego_pos.x - centerline_points[0].x) ** 2 +
                (ego_pos.y - centerline_points[0].y) ** 2
            )
            return dist, 0, 0.0
        
        # 1. 找到距离最近的中心线点（单峰搜索）
        min_idx = self._find_closest_point_idx(ego_pos, centerline_points)
        
        # 2. 计算到前后两条线段的垂直距离
        min_dist = float('inf')
        
        # 检查前一条线段：centerline_points[min_idx-1] -> centerline_points[min_idx]
        if min_idx > 0:
            dist = self._point_to_segment_distance(
                ego_pos, centerline_points[min_idx - 1], centerline_points[min_idx]
            )
            min_dist = min(min_dist, dist)
        
        # 检查后一条线段：centerline_points[min_idx] -> centerline_points[min_idx+1]
        if min_idx < len(centerline_points) - 1:
            dist = self._point_to_segment_distance(
                ego_pos, centerline_points[min_idx], centerline_points[min_idx + 1]
            )
            min_dist = min(min_dist, dist)
        
        # 如果只有一条线段的情况
        if min_dist == float('inf'):
            # 退化情况：返回点到最近点的距离
            pt = centerline_points[min_idx]
            min_dist = math.sqrt((ego_pos.x - pt.x)**2 + (ego_pos.y - pt.y)**2)
        
        # 计算纵向比例（自车在车道上的相对位置）
        longitudinal_ratio = min_idx / max(len(centerline_points) - 1, 1)
        
        return min_dist, min_idx, longitudinal_ratio

    def _get_lane_heading_at_index(
        self,
        centerline_points: List[Point3D],
        index: int
    ) -> float:
        """
        获取车道在指定点处的航向角
        
        Args:
            centerline_points: 车道中心线点集
            index: 点索引
            
        Returns:
            float: 航向角（弧度）
        """
        if len(centerline_points) < 2:
            return 0.0
        
        # 使用相邻点计算航向
        if index == 0:
            p1 = centerline_points[0]
            p2 = centerline_points[1]
        elif index == len(centerline_points) - 1:
            p1 = centerline_points[-2]
            p2 = centerline_points[-1]
        else:
            p1 = centerline_points[index - 1]
            p2 = centerline_points[index + 1]
        
        return math.atan2(p2.y - p1.y, p2.x - p1.x)
    
    def _normalize_angle(self, angle: float) -> float:
        """
        将角度归一化到 [-pi, pi]
        
        Args:
            angle: 角度（弧度）
            
        Returns:
            float: 归一化后的角度
        """
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
