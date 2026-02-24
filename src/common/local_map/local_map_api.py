"""
LocalMap API接口
LocalMap API Interface

提供对LocalMap数据的统一访问接口
Provides unified access interface to LocalMap data
"""

from typing import List, Optional, Tuple, Dict, Any
import math
from datetime import datetime

try:
    from .local_map_data import (
        LocalMap, Lane, LaneBoundarySegment, SpeedLimitSegment,
        TrafficLight, TrafficSign, RoadMarking, Crosswalk, StopLine, Intersection,
        Point3D, Point2D, Pose, LaneType, LaneDirection, TrafficLightColor, TrafficSignType
    )
except ImportError:
    from common.local_map.local_map_data import (
        LocalMap, Lane, LaneBoundarySegment, SpeedLimitSegment,
        TrafficLight, TrafficSign, RoadMarking, Crosswalk, StopLine, Intersection,
        Point3D, Point2D, Pose, LaneType, LaneDirection, TrafficLightColor, TrafficSignType
    )


class LocalMapAPI:
    """
    LocalMap API类
    LocalMap API Class
    
    提供对LocalMap数据的统一访问接口，支持map_node和traffic_rule模块使用
    Provides unified access interface to LocalMap data, supporting map_node and traffic_rule modules
    """
    
    def __init__(self, local_map: LocalMap):
        """
        初始化LocalMap API
        Initialize LocalMap API
        
        Args:
            local_map: 局部地图对象 / Local map object
        """
        self._local_map = local_map
        self._lane_id_cache = {}  # 车道ID缓存 / Lane ID cache
        self._boundary_segment_id_cache = {}  # 边界分段ID缓存 / Boundary segment ID cache
        self._traffic_light_id_cache = {}  # 信号灯ID缓存 / Traffic light ID cache
        self._traffic_sign_id_cache = {}  # 交通标志ID缓存 / Traffic sign ID cache
        self._road_marking_id_cache = {}  # 道路标线ID缓存 / Road marking ID cache
        self._crosswalk_id_cache = {}  # 人行横道ID缓存 / Crosswalk ID cache
        self._stop_line_id_cache = {}  # 停止线ID缓存 / Stop line ID cache
        self._intersection_id_cache = {}  # 交叉口ID缓存 / Intersection ID cache
        
        # 构建缓存
        self._build_caches()
    
    def _build_caches(self):
        """构建ID缓存 / Build ID caches"""
        # 构建车道缓存
        for lane in self._local_map.lanes:
            self._lane_id_cache[lane.lane_id] = lane
        
        # 构建边界分段缓存
        for segment in self._local_map.boundary_segments:
            self._boundary_segment_id_cache[segment.segment_id] = segment
        
        # 构建信号灯缓存
        for light in self._local_map.traffic_lights:
            self._traffic_light_id_cache[light.traffic_light_id] = light
        
        # 构建交通标志缓存
        for sign in self._local_map.traffic_signs:
            self._traffic_sign_id_cache[sign.traffic_sign_id] = sign
        
        # 构建道路标线缓存
        for marking in self._local_map.road_markings:
            self._road_marking_id_cache[marking.road_marking_id] = marking
        
        # 构建人行横道缓存
        for crosswalk in self._local_map.crosswalks:
            self._crosswalk_id_cache[crosswalk.crosswalk_id] = crosswalk
        
        # 构建停止线缓存
        for stop_line in self._local_map.stop_lines:
            self._stop_line_id_cache[stop_line.stop_line_id] = stop_line
        
        # 构建交叉口缓存
        for intersection in self._local_map.intersections:
            self._intersection_id_cache[intersection.intersection_id] = intersection
    
    def get_local_map(self) -> LocalMap:
        """
        获取局部地图对象
        Get local map object
        
        Returns:
            LocalMap: 局部地图对象 / Local map object
        """
        return self._local_map
    
    def update_local_map(self, local_map: LocalMap):
        """
        更新局部地图对象
        Update local map object
        
        Args:
            local_map: 新的局部地图对象 / New local map object
        """
        self._local_map = local_map
        self._build_caches()
    
    # ============================================================================
    # 车道相关API / Lane-related APIs
    # ============================================================================
    
    def get_lane_by_id(self, lane_id: int) -> Optional[Lane]:
        """
        根据车道ID获取车道对象
        Get lane object by lane ID
        
        Args:
            lane_id: 车道ID / Lane ID
        
        Returns:
            Optional[Lane]: 车道对象，如果不存在则返回None / Lane object, None if not found
        """
        return self._lane_id_cache.get(lane_id)
    
    def get_lanes_by_type(self, lane_type: LaneType) -> List[Lane]:
        """
        根据车道类型获取车道列表
        Get lanes by lane type
        
        Args:
            lane_type: 车道类型 / Lane type
        
        Returns:
            List[Lane]: 车道列表 / Lane list
        """
        return [lane for lane in self._local_map.lanes if lane.lane_type == lane_type]
    
    def get_lanes_by_direction(self, direction: LaneDirection) -> List[Lane]:
        """
        根据车道方向获取车道列表
        Get lanes by lane direction
        
        Args:
            direction: 车道方向 / Lane direction
        
        Returns:
            List[Lane]: 车道列表 / Lane list
        """
        return [lane for lane in self._local_map.lanes if lane.lane_direction == direction]
    
    def get_lanes_in_range(self, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> List[Lane]:
        """
        获取指定范围内的车道
        Get lanes within specified range
        
        Args:
            x_range: X轴范围 (min_x, max_x) / X-axis range (min_x, max_x)
            y_range: Y轴范围 (min_y, max_y) / Y-axis range (min_y, max_y)
        
        Returns:
            List[Lane]: 指定范围内的车道列表 / List of lanes within specified range
        """
        min_x, max_x = x_range
        min_y, max_y = y_range
        
        result = []
        for lane in self._local_map.lanes:
            # 检查车道中心线点是否在范围内
            for point in lane.centerline_points:
                if min_x <= point.x <= max_x and min_y <= point.y <= max_y:
                    result.append(lane)
                    break
        
        return result
    
    def get_lanes_within_distance(self, reference_point: Point3D, distance: float) -> List[Lane]:
        """
        获取指定距离内的车道
        Get lanes within specified distance
        
        Args:
            reference_point: 参考点 / Reference point
            distance: 距离（米）/ Distance (meters)
        
        Returns:
            List[Lane]: 指定距离内的车道列表 / List of lanes within specified distance
        """
        result = []
        distance_sq = distance * distance
        
        for lane in self._local_map.lanes:
            # 检查车道中心线点是否在距离内
            for point in lane.centerline_points:
                dx = point.x - reference_point.x
                dy = point.y - reference_point.y
                dz = point.z - reference_point.z
                
                if dx*dx + dy*dy + dz*dz <= distance_sq:
                    result.append(lane)
                    break
        
        return result
    
    def get_adjacent_lanes(self, lane_id: int) -> Tuple[Optional[Lane], Optional[Lane]]:
        """
        获取相邻车道
        Get adjacent lanes
        
        Args:
            lane_id: 车道ID / Lane ID
        
        Returns:
            Tuple[Optional[Lane], Optional[Lane]]: (左侧车道, 右侧车道) / (Left lane, Right lane)
        """
        lane = self.get_lane_by_id(lane_id)
        if not lane:
            return None, None
        
        left_lane = None
        right_lane = None
        
        if lane.left_adjacent_lane_id is not None:
            left_lane = self.get_lane_by_id(lane.left_adjacent_lane_id)
        
        if lane.right_adjacent_lane_id is not None:
            right_lane = self.get_lane_by_id(lane.right_adjacent_lane_id)
        
        return left_lane, right_lane
    
    def get_connected_lanes(self, lane_id: int) -> Tuple[List[Lane], List[Lane]]:
        """
        获取连接车道
        Get connected lanes
        
        Args:
            lane_id: 车道ID / Lane ID
        
        Returns:
            Tuple[List[Lane], List[Lane]]: (前继车道列表, 后继车道列表) / (Predecessor lanes, Successor lanes)
        """
        lane = self.get_lane_by_id(lane_id)
        if not lane:
            return [], []
        
        predecessor_lanes = []
        successor_lanes = []
        
        for pred_id in lane.predecessor_lane_ids:
            pred_lane = self.get_lane_by_id(pred_id)
            if pred_lane:
                predecessor_lanes.append(pred_lane)
        
        for succ_id in lane.successor_lane_ids:
            succ_lane = self.get_lane_by_id(succ_id)
            if succ_lane:
                successor_lanes.append(succ_lane)
        
        return predecessor_lanes, successor_lanes
    
    def get_lane_speed_limit(self, lane_id: int, position: Point3D) -> Optional[float]:
        """
        获取指定位置的限速
        Get speed limit at specified position
        
        Args:
            lane_id: 车道ID / Lane ID
            position: 位置点 / Position point
        
        Returns:
            Optional[float]: 限速值（米/秒），如果不存在则返回None / Speed limit (m/s), None if not found
        """
        lane = self.get_lane_by_id(lane_id)
        if not lane or not lane.speed_limits:
            return None
        
        # 找到包含该位置的限速分段
        for speed_limit in lane.speed_limits:
            if self._is_point_in_segment(position, speed_limit.start_position, speed_limit.end_position):
                return speed_limit.speed_limit
        
        return None
    
    def _is_point_in_segment(self, point: Point3D, start: Point3D, end: Point3D, tolerance: float = 1.0) -> bool:
        """
        检查点是否在线段内
        Check if point is within line segment
        
        Args:
            point: 检查点 / Point to check
            start: 线段起点 / Segment start point
            end: 线段终点 / Segment end point
            tolerance: 容差（米）/ Tolerance (meters)
        
        Returns:
            bool: 是否在线段内 / Whether within segment
        """
        # 计算点到线段的距离
        segment_length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
        if segment_length < 1e-6:
            return math.sqrt((point.x - start.x)**2 + (point.y - start.y)**2) <= tolerance
        
        # 计算投影参数
        t = max(0, min(1, ((point.x - start.x) * (end.x - start.x) +
                           (point.y - start.y) * (end.y - start.y)) / (segment_length * segment_length)))
        
        # 计算投影点
        projection = Point3D(
            x=start.x + t * (end.x - start.x),
            y=start.y + t * (end.y - start.y),
            z=start.z + t * (end.z - start.z)
        )
        
        # 计算距离
        distance = math.sqrt((point.x - projection.x)**2 + (point.y - projection.y)**2 + (point.z - projection.z)**2)
        
        return distance <= tolerance
    
    # ============================================================================
    # 边界相关API / Boundary-related APIs
    # ============================================================================
    
    def get_boundary_segment_by_id(self, segment_id: int) -> Optional[LaneBoundarySegment]:
        """
        根据边界分段ID获取边界分段对象
        Get boundary segment object by segment ID
        
        Args:
            segment_id: 边界分段ID / Boundary segment ID
        
        Returns:
            Optional[LaneBoundarySegment]: 边界分段对象，如果不存在则返回None / Boundary segment object, None if not found
        """
        return self._boundary_segment_id_cache.get(segment_id)
    
    def get_lane_boundaries(self, lane_id: int) -> Tuple[List[LaneBoundarySegment], List[LaneBoundarySegment]]:
        """
        获取车道边界
        Get lane boundaries
        
        Args:
            lane_id: 车道ID / Lane ID
        
        Returns:
            Tuple[List[LaneBoundarySegment], List[LaneBoundarySegment]]: (左边界列表, 右边界列表) / (Left boundaries, Right boundaries)
        """
        lane = self.get_lane_by_id(lane_id)
        if not lane:
            return [], []
        
        left_boundaries = []
        right_boundaries = []
        
        for idx in lane.left_boundary_segment_indices:
            if 0 <= idx < len(self._local_map.boundary_segments):
                left_boundaries.append(self._local_map.boundary_segments[idx])
        
        for idx in lane.right_boundary_segment_indices:
            if 0 <= idx < len(self._local_map.boundary_segments):
                right_boundaries.append(self._local_map.boundary_segments[idx])
        
        return left_boundaries, right_boundaries
    
    # ============================================================================
    # 交通信号灯相关API / Traffic Light-related APIs
    # ============================================================================
    
    def get_traffic_light_by_id(self, traffic_light_id: int) -> Optional[TrafficLight]:
        """
        根据信号灯ID获取交通信号灯对象
        Get traffic light object by traffic light ID
        
        Args:
            traffic_light_id: 信号灯ID / Traffic light ID
        
        Returns:
            Optional[TrafficLight]: 交通信号灯对象，如果不存在则返回None / Traffic light object, None if not found
        """
        return self._traffic_light_id_cache.get(traffic_light_id)
    
    def get_traffic_lights_by_color(self, color: TrafficLightColor) -> List[TrafficLight]:
        """
        根据颜色获取交通信号灯列表
        Get traffic lights by color
        
        Args:
            color: 信号灯颜色 / Traffic light color
        
        Returns:
            List[TrafficLight]: 交通信号灯列表 / Traffic light list
        """
        return [light for light in self._local_map.traffic_lights if light.current_state.color == color]
    
    def get_traffic_lights_in_range(self, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> List[TrafficLight]:
        """
        获取指定范围内的交通信号灯
        Get traffic lights within specified range
        
        Args:
            x_range: X轴范围 (min_x, max_x) / X-axis range (min_x, max_x)
            y_range: Y轴范围 (min_y, max_y) / Y-axis range (min_y, max_y)
        
        Returns:
            List[TrafficLight]: 指定范围内的交通信号灯列表 / List of traffic lights within specified range
        """
        min_x, max_x = x_range
        min_y, max_y = y_range
        
        result = []
        for light in self._local_map.traffic_lights:
            if min_x <= light.position.x <= max_x and min_y <= light.position.y <= max_y:
                result.append(light)
        
        return result
    
    def get_traffic_lights_within_distance(self, reference_point: Point3D, distance: float) -> List[TrafficLight]:
        """
        获取指定距离内的交通信号灯
        Get traffic lights within specified distance
        
        Args:
            reference_point: 参考点 / Reference point
            distance: 距离（米）/ Distance (meters)
        
        Returns:
            List[TrafficLight]: 指定距离内的交通信号灯列表 / List of traffic lights within specified distance
        """
        result = []
        distance_sq = distance * distance
        
        for light in self._local_map.traffic_lights:
            dx = light.position.x - reference_point.x
            dy = light.position.y - reference_point.y
            dz = light.position.z - reference_point.z
            
            if dx*dx + dy*dy + dz*dz <= distance_sq:
                result.append(light)
        
        return result
    
    # ============================================================================
    # 交通标志相关API / Traffic Sign-related APIs
    # ============================================================================
    
    def get_traffic_sign_by_id(self, traffic_sign_id: int) -> Optional[TrafficSign]:
        """
        根据交通标志ID获取交通标志对象
        Get traffic sign object by traffic sign ID
        
        Args:
            traffic_sign_id: 交通标志ID / Traffic sign ID
        
        Returns:
            Optional[TrafficSign]: 交通标志对象，如果不存在则返回None / Traffic sign object, None if not found
        """
        return self._traffic_sign_id_cache.get(traffic_sign_id)
    
    def get_traffic_signs_by_type(self, sign_type: TrafficSignType) -> List[TrafficSign]:
        """
        根据类型获取交通标志列表
        Get traffic signs by type
        
        Args:
            sign_type: 交通标志类型 / Traffic sign type
        
        Returns:
            List[TrafficSign]: 交通标志列表 / Traffic sign list
        """
        return [sign for sign in self._local_map.traffic_signs if sign.sign_type == sign_type]
    
    def get_speed_limit_signs(self) -> List[TrafficSign]:
        """
        获取所有限速标志
        Get all speed limit signs
        
        Returns:
            List[TrafficSign]: 限速标志列表 / Speed limit signs list
        """
        speed_limit_types = [
            TrafficSignType.SPEED_LIMIT,
            TrafficSignType.SPEED_LIMIT_END,
            TrafficSignType.MINIMUM_SPEED,
            TrafficSignType.SPEED_LIMIT_ZONE_START,
            TrafficSignType.SPEED_LIMIT_ZONE_END,
            TrafficSignType.TEMPORARY_SPEED_LIMIT
        ]
        
        return [sign for sign in self._local_map.traffic_signs if sign.sign_type in speed_limit_types]
    
    def get_traffic_signs_in_range(self, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> List[TrafficSign]:
        """
        获取指定范围内的交通标志
        Get traffic signs within specified range
        
        Args:
            x_range: X轴范围 (min_x, max_x) / X-axis range (min_x, max_x)
            y_range: Y轴范围 (min_y, max_y) / Y-axis range (min_y, max_y)
        
        Returns:
            List[TrafficSign]: 指定范围内的交通标志列表 / List of traffic signs within specified range
        """
        min_x, max_x = x_range
        min_y, max_y = y_range
        
        result = []
        for sign in self._local_map.traffic_signs:
            if min_x <= sign.position.x <= max_x and min_y <= sign.position.y <= max_y:
                result.append(sign)
        
        return result
    
    def get_traffic_signs_within_distance(self, reference_point: Point3D, distance: float) -> List[TrafficSign]:
        """
        获取指定距离内的交通标志
        Get traffic signs within specified distance
        
        Args:
            reference_point: 参考点 / Reference point
            distance: 距离（米）/ Distance (meters)
        
        Returns:
            List[TrafficSign]: 指定距离内的交通标志列表 / List of traffic signs within specified distance
        """
        result = []
        distance_sq = distance * distance
        
        for sign in self._local_map.traffic_signs:
            dx = sign.position.x - reference_point.x
            dy = sign.position.y - reference_point.y
            dz = sign.position.z - reference_point.z
            
            if dx*dx + dy*dy + dz*dz <= distance_sq:
                result.append(sign)
        
        return result
    
    # ============================================================================
    # 道路标线相关API / Road Marking-related APIs
    # ============================================================================
    
    def get_road_marking_by_id(self, road_marking_id: int) -> Optional[RoadMarking]:
        """
        根据道路标线ID获取道路标线对象
        Get road marking object by road marking ID
        
        Args:
            road_marking_id: 道路标线ID / Road marking ID
        
        Returns:
            Optional[RoadMarking]: 道路标线对象，如果不存在则返回None / Road marking object, None if not found
        """
        return self._road_marking_id_cache.get(road_marking_id)
    
    def get_road_markings_by_type(self, marking_type: Any) -> List[RoadMarking]:
        """
        根据类型获取道路标线列表
        Get road markings by type
        
        Args:
            marking_type: 道路标线类型 / Road marking type
        
        Returns:
            List[RoadMarking]: 道路标线列表 / Road marking list
        """
        return [marking for marking in self._local_map.road_markings if marking.marking_type == marking_type]
    
    def get_stop_lines(self) -> List[RoadMarking]:
        """
        获取所有停止线
        Get all stop lines
        
        Returns:
            List[RoadMarking]: 停止线列表 / Stop lines list
        """
        return [marking for marking in self._local_map.road_markings if marking.marking_type.value == 1]  # STOP_LINE = 1
    
    def get_crosswalk_markings(self) -> List[RoadMarking]:
        """
        获取所有人行横道标线
        Get all crosswalk markings
        
        Returns:
            List[RoadMarking]: 人行横道标线列表 / Crosswalk markings list
        """
        return [marking for marking in self._local_map.road_markings if marking.marking_type.value in [2, 3]]  # CROSSWALK = 2, ZEBRA_CROSSING = 3
    
    # ============================================================================
    # 人行横道相关API / Crosswalk-related APIs
    # ============================================================================
    
    def get_crosswalk_by_id(self, crosswalk_id: int) -> Optional[Crosswalk]:
        """
        根据人行横道ID获取人行横道对象
        Get crosswalk object by crosswalk ID
        
        Args:
            crosswalk_id: 人行横道ID / Crosswalk ID
        
        Returns:
            Optional[Crosswalk]: 人行横道对象，如果不存在则返回None / Crosswalk object, None if not found
        """
        return self._crosswalk_id_cache.get(crosswalk_id)
    
    def get_crosswalks_in_range(self, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> List[Crosswalk]:
        """
        获取指定范围内的人行横道
        Get crosswalks within specified range
        
        Args:
            x_range: X轴范围 (min_x, max_x) / X-axis range (min_x, max_x)
            y_range: Y轴范围 (min_y, max_y) / Y-axis range (min_y, max_y)
        
        Returns:
            List[Crosswalk]: 指定范围内的人行横道列表 / List of crosswalks within specified range
        """
        min_x, max_x = x_range
        min_y, max_y = y_range
        
        result = []
        for crosswalk in self._local_map.crosswalks:
            # 检查人行横道多边形顶点是否在范围内
            for point in crosswalk.polygon_points:
                if min_x <= point.x <= max_x and min_y <= point.y <= max_y:
                    result.append(crosswalk)
                    break
        
        return result
    
    def get_crosswalks_within_distance(self, reference_point: Point3D, distance: float) -> List[Crosswalk]:
        """
        获取指定距离内的人行横道
        Get crosswalks within specified distance
        
        Args:
            reference_point: 参考点 / Reference point
            distance: 距离（米）/ Distance (meters)
        
        Returns:
            List[Crosswalk]: 指定距离内的人行横道列表 / List of crosswalks within specified distance
        """
        result = []
        distance_sq = distance * distance
        
        for crosswalk in self._local_map.crosswalks:
            # 计算人行横道中心点
            if crosswalk.polygon_points:
                center_x = sum(p.x for p in crosswalk.polygon_points) / len(crosswalk.polygon_points)
                center_y = sum(p.y for p in crosswalk.polygon_points) / len(crosswalk.polygon_points)
                center_z = sum(p.z for p in crosswalk.polygon_points) / len(crosswalk.polygon_points)
                
                dx = center_x - reference_point.x
                dy = center_y - reference_point.y
                dz = center_z - reference_point.z
                
                if dx*dx + dy*dy + dz*dz <= distance_sq:
                    result.append(crosswalk)
        
        return result
    
    # ============================================================================
    # 停止线相关API / Stop Line-related APIs
    # ============================================================================
    
    def get_stop_line_by_id(self, stop_line_id: int) -> Optional[StopLine]:
        """
        根据停止线ID获取停止线对象
        Get stop line object by stop line ID
        
        Args:
            stop_line_id: 停止线ID / Stop line ID
        
        Returns:
            Optional[StopLine]: 停止线对象，如果不存在则返回None / Stop line object, None if not found
        """
        return self._stop_line_id_cache.get(stop_line_id)
    
    def get_stop_lines_in_range(self, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> List[StopLine]:
        """
        获取指定范围内的停止线
        Get stop lines within specified range
        
        Args:
            x_range: X轴范围 (min_x, max_x) / X-axis range (min_x, max_x)
            y_range: Y轴范围 (min_y, max_y) / Y-axis range (min_y, max_y)
        
        Returns:
            List[StopLine]: 指定范围内的停止线列表 / List of stop lines within specified range
        """
        min_x, max_x = x_range
        min_y, max_y = y_range
        
        result = []
        for stop_line in self._local_map.stop_lines:
            # 检查停止线点是否在范围内
            for point in stop_line.line_points:
                if min_x <= point.x <= max_x and min_y <= point.y <= max_y:
                    result.append(stop_line)
                    break
        
        return result
    
    # ============================================================================
    # 交叉口相关API / Intersection-related APIs
    # ============================================================================
    
    def get_intersection_by_id(self, intersection_id: int) -> Optional[Intersection]:
        """
        根据交叉口ID获取交叉口对象
        Get intersection object by intersection ID
        
        Args:
            intersection_id: 交叉口ID / Intersection ID
        
        Returns:
            Optional[Intersection]: 交叉口对象，如果不存在则返回None / Intersection object, None if not found
        """
        return self._intersection_id_cache.get(intersection_id)
    
    def get_intersections_in_range(self, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> List[Intersection]:
        """
        获取指定范围内的交叉口
        Get intersections within specified range
        
        Args:
            x_range: X轴范围 (min_x, max_x) / X-axis range (min_x, max_x)
            y_range: Y轴范围 (min_y, max_y) / Y-axis range (min_y, max_y)
        
        Returns:
            List[Intersection]: 指定范围内的交叉口列表 / List of intersections within specified range
        """
        min_x, max_x = x_range
        min_y, max_y = y_range
        
        result = []
        for intersection in self._local_map.intersections:
            # 检查交叉口多边形顶点是否在范围内
            for point in intersection.polygon_points:
                if min_x <= point.x <= max_x and min_y <= point.y <= max_y:
                    result.append(intersection)
                    break
        
        return result
    
    # ============================================================================
    # 查询和统计API / Query and Statistics APIs
    # ============================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取局部地图统计信息
        Get local map statistics
        
        Returns:
            Dict[str, Any]: 统计信息字典 / Statistics dictionary
        """
        stats = {
            'timestamp': self._local_map.header.timestamp.isoformat(),
            'map_range': {
                'x': self._local_map.metadata.map_range_x,
                'y': self._local_map.metadata.map_range_y,
                'z': self._local_map.metadata.map_range_z
            },
            'ego_vehicle': {
                'x': self._local_map.metadata.ego_vehicle_x,
                'y': self._local_map.metadata.ego_vehicle_y,
                'heading': self._local_map.metadata.ego_vehicle_heading,
                'velocity': self._local_map.metadata.ego_vehicle_velocity
            },
            'counts': {
                'lanes': len(self._local_map.lanes),
                'boundary_segments': len(self._local_map.boundary_segments),
                'traffic_lights': len(self._local_map.traffic_lights),
                'traffic_signs': len(self._local_map.traffic_signs),
                'road_markings': len(self._local_map.road_markings),
                'crosswalks': len(self._local_map.crosswalks),
                'stop_lines': len(self._local_map.stop_lines),
                'intersections': len(self._local_map.intersections)
            }
        }
        
        # 车道类型统计
        lane_type_counts = {}
        for lane in self._local_map.lanes:
            lane_type = lane.lane_type.name if hasattr(lane.lane_type, 'name') else str(lane.lane_type)
            lane_type_counts[lane_type] = lane_type_counts.get(lane_type, 0) + 1
        stats['lane_type_counts'] = lane_type_counts
        
        # 交通信号灯颜色统计
        traffic_light_color_counts = {}
        for light in self._local_map.traffic_lights:
            color = light.current_state.color.name if hasattr(light.current_state.color, 'name') else str(light.current_state.color)
            traffic_light_color_counts[color] = traffic_light_color_counts.get(color, 0) + 1
        stats['traffic_light_color_counts'] = traffic_light_color_counts
        
        # 交通标志类型统计
        traffic_sign_type_counts = {}
        for sign in self._local_map.traffic_signs:
            sign_type = sign.sign_type.name if hasattr(sign.sign_type, 'name') else str(sign.sign_type)
            traffic_sign_type_counts[sign_type] = traffic_sign_type_counts.get(sign_type, 0) + 1
        stats['traffic_sign_type_counts'] = traffic_sign_type_counts
        
        return stats
    
    def validate_data(self) -> List[str]:
        """
        验证局部地图数据的有效性
        Validate local map data
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过 / List of validation errors, empty list means validation passed
        """
        errors = []
        
        # 检查边界分段引用是否有效
        for lane in self._local_map.lanes:
            for segment_idx in lane.left_boundary_segment_indices:
                if segment_idx < 0 or segment_idx >= len(self._local_map.boundary_segments):
                    errors.append(f"Lane {lane.lane_id} references invalid left boundary segment index {segment_idx}")
            
            for segment_idx in lane.right_boundary_segment_indices:
                if segment_idx < 0 or segment_idx >= len(self._local_map.boundary_segments):
                    errors.append(f"Lane {lane.lane_id} references invalid right boundary segment index {segment_idx}")
        
        # 检查关联元素ID是否有效
        for lane in self._local_map.lanes:
            for light_id in lane.associated_traffic_light_ids:
                if self.get_traffic_light_by_id(light_id) is None:
                    errors.append(f"Lane {lane.lane_id} references invalid traffic light ID {light_id}")
            
            for sign_id in lane.associated_traffic_sign_ids:
                if self.get_traffic_sign_by_id(sign_id) is None:
                    errors.append(f"Lane {lane.lane_id} references invalid traffic sign ID {sign_id}")
        
        # 检查相邻车道引用是否有效
        for lane in self._local_map.lanes:
            if lane.left_adjacent_lane_id is not None:
                if self.get_lane_by_id(lane.left_adjacent_lane_id) is None:
                    errors.append(f"Lane {lane.lane_id} references invalid left adjacent lane ID {lane.left_adjacent_lane_id}")
            
            if lane.right_adjacent_lane_id is not None:
                if self.get_lane_by_id(lane.right_adjacent_lane_id) is None:
                    errors.append(f"Lane {lane.lane_id} references invalid right adjacent lane ID {lane.right_adjacent_lane_id}")
        
        # 检查连接车道引用是否有效
        for lane in self._local_map.lanes:
            for pred_id in lane.predecessor_lane_ids:
                if self.get_lane_by_id(pred_id) is None:
                    errors.append(f"Lane {lane.lane_id} references invalid predecessor lane ID {pred_id}")
            
            for succ_id in lane.successor_lane_ids:
                if self.get_lane_by_id(succ_id) is None:
                    errors.append(f"Lane {lane.lane_id} references invalid successor lane ID {succ_id}")
        
        return errors
    
    # ============================================================================
    # 几何计算API / Geometry Calculation APIs
    # ============================================================================
    
    def calculate_distance_to_lane(self, point: Point3D, lane_id: int) -> Optional[float]:
        """
        计算点到车道的距离
        Calculate distance from point to lane
        
        Args:
            point: 点坐标 / Point coordinates
            lane_id: 车道ID / Lane ID
        
        Returns:
            Optional[float]: 距离（米），如果车道不存在则返回None / Distance (meters), None if lane not found
        """
        lane = self.get_lane_by_id(lane_id)
        if not lane or not lane.centerline_points:
            return None
        
        min_distance = float('inf')
        
        for i in range(len(lane.centerline_points) - 1):
            p1 = lane.centerline_points[i]
            p2 = lane.centerline_points[i + 1]
            
            # 计算点到线段的距离
            distance = self._point_to_line_segment_distance(point, p1, p2)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _point_to_line_segment_distance(self, point: Point3D, line_start: Point3D, line_end: Point3D) -> float:
        """
        计算点到线段的距离
        Calculate distance from point to line segment
        
        Args:
            point: 点坐标 / Point coordinates
            line_start: 线段起点 / Line segment start
            line_end: 线段终点 / Line segment end
        
        Returns:
            float: 距离 / Distance
        """
        # 向量计算
        line_vec = Point3D(
            x=line_end.x - line_start.x,
            y=line_end.y - line_start.y,
            z=line_end.z - line_start.z
        )
        
        point_vec = Point3D(
            x=point.x - line_start.x,
            y=point.y - line_start.y,
            z=point.z - line_start.z
        )
        
        line_length_sq = line_vec.x * line_vec.x + line_vec.y * line_vec.y + line_vec.z * line_vec.z
        
        if line_length_sq < 1e-6:
            # 线段长度为0，返回点到起点的距离
            return math.sqrt(point_vec.x * point_vec.x + point_vec.y * point_vec.y + point_vec.z * point_vec.z)
        
        # 计算投影参数
        t = max(0, min(1, (point_vec.x * line_vec.x + point_vec.y * line_vec.y + point_vec.z * line_vec.z) / line_length_sq))
        
        # 计算投影点
        projection = Point3D(
            x=line_start.x + t * line_vec.x,
            y=line_start.y + t * line_vec.y,
            z=line_start.z + t * line_vec.z
        )
        
        # 计算距离
        diff = Point3D(
            x=point.x - projection.x,
            y=point.y - projection.y,
            z=point.z - projection.z
        )
        
        return math.sqrt(diff.x * diff.x + diff.y * diff.y + diff.z * diff.z)
    
    def find_nearest_lane(self, point: Point3D, max_distance: float = 50.0) -> Optional[Tuple[Lane, float]]:
        """
        查找最近的车道
        Find nearest lane
        
        Args:
            point: 点坐标 / Point coordinates
            max_distance: 最大搜索距离（米）/ Maximum search distance (meters)
        
        Returns:
            Optional[Tuple[Lane, float]]: (最近车道, 距离)，如果没有车道在范围内则返回None / (Nearest lane, distance), None if no lane in range
        """
        nearest_lane = None
        min_distance = float('inf')
        
        for lane in self._local_map.lanes:
            if not lane.centerline_points:
                continue
            
            distance = self.calculate_distance_to_lane(point, lane.lane_id)
            if distance is not None and distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_lane = lane
        
        if nearest_lane:
            return nearest_lane, min_distance
        
        return None
    
    def is_point_in_lane(self, point: Point3D, lane_id: int, tolerance: float = 1.0) -> bool:
        """
        检查点是否在车道内
        Check if point is within lane
        
        Args:
            point: 点坐标 / Point coordinates
            lane_id: 车道ID / Lane ID
            tolerance: 容差（米）/ Tolerance (meters)
        
        Returns:
            bool: 是否在车道内 / Whether within lane
        """
        distance = self.calculate_distance_to_lane(point, lane_id)
        return distance is not None and distance <= tolerance
    
    # ============================================================================
    # 可视化API / Visualization API
    # ============================================================================
    
    def visualize(
        self,
        title: str = "Local Map Visualization",
        show_lanes: bool = True,
        show_centerlines: bool = True,
        show_traffic_elements: bool = True,
        show_ego_position: bool = True,
        ego_points: Optional[List[Point3D]] = None,
        save_path: Optional[str] = None,
        dpi: int = 100
    ) -> None:
        """
        可视化局部地图
        Visualize local map
        
        Args:
            title: 图表标题 / Plot title
            show_lanes: 是否显示车道边界 / Whether to show lane boundaries
            show_centerlines: 是否显示车道中心线 / Whether to show lane centerlines
            show_traffic_elements: 是否显示交通元素 / Whether to show traffic elements
            show_ego_position: 是否显示自车位置 / Whether to show ego vehicle position
            ego_points: 自车测试点列表 / List of ego test points to mark
            save_path: 保存路径 / Path to save figure (optional)
            dpi: 保存图片的DPI / DPI for saved figure
        """
        try:
            from .visualization import LocalMapVisualizer
        except ImportError:
            try:
                from common.local_map.visualization import LocalMapVisualizer
            except ImportError:
                raise ImportError(
                    "Visualization module not available. Please install matplotlib:\n"
                    "  pip install matplotlib"
                )
        
        visualizer = LocalMapVisualizer()
        visualizer.visualize_local_map(
            local_map=self._local_map,
            title=title,
            show_lanes=show_lanes,
            show_centerlines=show_centerlines,
            show_traffic_elements=show_traffic_elements,
            show_ego_position=show_ego_position,
            ego_points=ego_points,
            save_path=save_path,
            dpi=dpi
        )