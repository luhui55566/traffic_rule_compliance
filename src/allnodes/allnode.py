#!/usr/bin/env python3
"""
AllNodes - 交通规则符合性判定系统主调度模块

该模块负责协调各个子模块的初始化和数据处理流程。

当前实现:
    - veh_status模块:读取车辆状态数据
    - map_node模块:加载地图,生成局部地图
    - env_node模块:环境模型融合，统一坐标系

Usage:
    from src.allnodes.allnode import AllNodes
    
    allnodes = AllNodes("configs/traffic_rule_config.yaml")
    allnodes.run()
"""

import sys
import yaml
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# 添加项目根目录和src目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_ROOT = PROJECT_ROOT / 'src'
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_ROOT))

# 导入子模块（SRC_ROOT已添加到sys.path，可以直接导入）
from veh_status import VehStatusReader, EgoVehicleState
from map_node import MapNode
from env_node import EnvNode, EnvironmentModel
from common.local_map.local_map_data import LocalMap, Point3D
from common.local_map.local_map_api import LocalMapAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AllNodes:
    """
    交通规则符合性判定系统主调度器
    
    负责协调各子模块的初始化和数据处理流程。
    """
    
    # 局部地图可视化间隔（每N帧生成一次可视化）
    VISUALIZATION_INTERVAL = 25
    
    # 轨迹可视范围（米）
    TRAJECTORY_RANGE = 300.0
    
    def __init__(self, config_path: str):
        """
        初始化AllNodes
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        # 子模块
        self.veh_status_reader: Optional[VehStatusReader] = None
        self.map_node: Optional[MapNode] = None
        self.env_node: Optional[EnvNode] = None
        
        # 数据
        self.ego_states: List[EgoVehicleState] = []
        self._last_env_model: Optional[EnvironmentModel] = None  # 最后一个环境模型（用于可视化）
        
        # 可视化输出目录
        self.output_dir = PROJECT_ROOT / 'output' / 'local_maps'
        
    def _load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if not self.config_path.exists():
                logger.error(f"配置文件不存在: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return False
    
    def _init_veh_status(self) -> bool:
        """
        初始化车辆状态读取模块
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.veh_status_reader = VehStatusReader(self.config)
            return self.veh_status_reader.init()
        except Exception as e:
            logger.error(f"veh_status模块初始化失败: {e}")
            return False
    
    def _init_map_node(self) -> bool:
        """
        初始化地图节点模块
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.map_node = MapNode(self.config)
            return self.map_node.init()
        except Exception as e:
            logger.error(f"map_node模块初始化失败: {e}")
            return False
    
    def _init_env_node(self) -> bool:
        """
        初始化环境模型节点模块
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.env_node = EnvNode(self.config)
            return self.env_node.init()
        except Exception as e:
            logger.error(f"env_node模块初始化失败: {e}")
            return False
    
    def init(self) -> bool:
        """
        初始化所有模块
        
        Returns:
            bool: 初始化是否成功
        """
        logger.info("开始初始化AllNodes...")
        
        # 加载配置
        if not self._load_config():
            return False
        
        # 初始化veh_status模块
        if not self._init_veh_status():
            return False
        
        # 初始化map_node模块
        if not self._init_map_node():
            return False
        
        # 初始化env_node模块
        if not self._init_env_node():
            return False
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("AllNodes初始化完成")
        return True
    
    def run(self) -> bool:
        """
        运行主处理流程
        
        Returns:
            bool: 处理是否成功
        """
        if not self.init():
            logger.error("AllNodes初始化失败")
            return False
        
        logger.info("开始处理数据...")
        
        # 1. 读取车辆状态数据
        self.ego_states = self.veh_status_reader.process()
        logger.info(f"读取到 {len(self.ego_states)} 帧车辆状态数据")
        
        # 2. 逐帧处理: 生成局部地图并可视化
        self._process_frames()
        
        # 3. TODO: 后续添加其他模块的处理
        # - 环境模型模块: 统一坐标系和时间轴
        # - traffic_rule模块: 判断交通规则符合性
        
        # 打印摘要信息
        self._print_summary()
        
        return True
    
    def _process_frames(self) -> None:
        """
        逐帧处理数据：生成局部地图和环境模型，每隔一定帧数保存可视化
        """
        logger.info("开始逐帧处理...")
        
        success_count = 0
        visualization_count = 0
        env_model_count = 0
        
        # 用于存储最近一次成功生成的局部地图（供env_node使用）
        last_local_map: Optional[LocalMap] = None
        
        for i, ego_state in enumerate(self.ego_states):
            # 每 10 帧生成一次局部地图，提高处理速度
            if (i + 1) % 50 == 0:
                # 生成局部地图
                local_map = self.map_node.process(ego_state)
                if local_map is not None:
                    last_local_map = local_map
                    success_count += 1
            else:
                local_map = last_local_map  # 使用上一次的局部地图
            
            # 使用env_node处理每一帧（即使没有更新局部地图）
            if self.env_node is not None and local_map is not None:
                env_model = self.env_node.process(ego_state, local_map, self.map_node, i)
                self._last_env_model = env_model  # 只保存最后一个环境模型
                env_model_count += 1
                
                # 每隔 VISUALIZATION_INTERVAL 帧生成一次可视化
                # 使用env_model中的local_map和ego_history
                if (i + 1) % self.VISUALIZATION_INTERVAL == 0:
                    self._visualize_env_model(env_model, i + 1)
                    visualization_count += 1
            
            # 每处理 100 帧打印一次进度
            if (i + 1) % 100 == 0:
                logger.info(f"已处理 {i + 1}/{len(self.ego_states)} 帧")
        
        logger.info(f"逐帧处理完成：{success_count}/{len(self.ego_states)} 帧成功生成局部地图")
        logger.info(f"生成环境模型：{env_model_count} 个")
        logger.info(f"生成可视化图片：{visualization_count} 张")
    
    def _get_trajectory_from_env_history(
        self,
        env_model: EnvironmentModel,
        max_range: float = 300.0
    ) -> List[Point3D]:
        """
        从env_model的历史轨迹中获取可视范围内的轨迹点
        
        使用env_node已经计算好的局部坐标，不需要重新计算。
        
        Args:
            env_model: 环境模型
            max_range: 最大可视范围（米）
            
        Returns:
            List[Point3D]: 范围内的轨迹点列表
        """
        trajectory_points = []
        
        if not env_model.ego_history:
            return trajectory_points
        
        # 遍历历史轨迹，使用已计算好的局部坐标
        for hist_state in env_model.ego_history:
            if hist_state.local_state is None:
                continue
            
            pos = hist_state.local_state.position
            distance = math.sqrt(pos.x ** 2 + pos.y ** 2)
            
            # 只保留在可视范围内的点
            if distance <= max_range:
                trajectory_points.append(Point3D(x=pos.x, y=pos.y, z=pos.z))
        
        return trajectory_points
    
    def _visualize_env_model(
        self,
        env_model: EnvironmentModel,
        frame_index: int
    ) -> None:
        """
        可视化环境模型并保存
        
        使用env_model中的local_map和ego_history进行可视化。
        
        Args:
            env_model: 环境模型
            frame_index: 帧索引
        """
        if env_model.local_map is None:
            logger.warning(f"帧 {frame_index} 没有局部地图，跳过可视化")
            return
        
        try:
            # 创建LocalMapAPI用于可视化
            api = LocalMapAPI(env_model.local_map)
            
            # 从env_model的历史轨迹获取轨迹点
            trajectory_points = self._get_trajectory_from_env_history(
                env_model,
                max_range=self.TRAJECTORY_RANGE
            )
            
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"localmap_frame_{frame_index:04d}_{timestamp}.png"
            output_path = self.output_dir / filename
            
            # 获取自车信息用于标题
            ego_state = env_model.ego_state
            if ego_state and ego_state.global_state:
                gps_pos = ego_state.global_state.position
                gps_str = f"GPS: ({gps_pos.latitude:.6f}, {gps_pos.longitude:.6f})"
                if ego_state.global_state.linear_velocity:
                    speed = ego_state.global_state.linear_velocity.magnitude() * 3.6  # m/s to km/h
                    speed_str = f"Speed: {speed:.1f} km/h"
                else:
                    speed_str = "Speed: N/A"
            else:
                gps_str = "GPS: N/A"
                speed_str = "Speed: N/A"
            
            # 获取局部坐标信息
            if ego_state and ego_state.local_state:
                local_pos = ego_state.local_state.position
                local_yaw = ego_state.local_state.orientation.yaw
                local_str = f"Local: ({local_pos.x:.2f}, {local_pos.y:.2f}), Yaw: {math.degrees(local_yaw):.1f} deg"
            else:
                local_str = "Local: N/A"
            
            # 可视化
            api.visualize(
                title=f"Local Map - Frame {frame_index}\n"
                      f"{gps_str}\n"
                      f"{speed_str}\n"
                      f"{local_str}\n"
                      f"Trajectory: {len(trajectory_points)} points",
                show_lanes=True,
                show_centerlines=True,
                show_traffic_elements=True,
                show_ego_position=True,
                show_road_ids=True,
                ego_points=[Point3D(x=0.0, y=0.0, z=0.0)],  # 自车在原点
                trajectory_points=trajectory_points,  # 使用env_node的轨迹
                save_path=str(output_path),
                dpi=150
            )
            
            logger.debug(f"保存可视化: {output_path}")
            
        except Exception as e:
            logger.warning(f"可视化失败 (帧 {frame_index}): {e}")
    
    def _print_summary(self) -> None:
        """打印处理摘要"""
        print("\n" + "=" * 60)
        print("处理摘要")
        print("=" * 60)
        print(f"总帧数: {len(self.ego_states)}")
        
        # 打印地图信息
        if self.map_node:
            map_info = self.map_node.get_map_info()
            print(f"\n地图信息:")
            print(f"  格式: {map_info['format']}")
            print(f"  加载状态: {'已加载' if map_info['loaded'] else '未加载'}")
            print(f"  局部地图范围: {map_info['map_range']}m")
        
        # 打印env_node信息
        if self.env_node:
            print(f"\n环境模型节点:")
            print(f"  历史轨迹长度: {self.env_node.get_history_length()}")
        
        # 打印输出目录
        print(f"\n可视化输出目录: {self.output_dir}")
        
        if self.ego_states:
            first = self.ego_states[0]
            last = self.ego_states[-1]
            
            print(f"\n起始帧:")
            print(f"  文件名: {first.frame_name}")
            print(f"  时间戳: {first.timestamp}")
            print(f"  位置: ({first.latitude:.6f}, {first.longitude:.6f})")
            print(f"  速度: {first.speed_kmh:.2f} km/h")
            
            # 打印投影后的地图坐标
            if self.map_node:
                map_x, map_y = self.map_node.project_gps(first.latitude, first.longitude)
                print(f"  地图坐标: ({map_x:.2f}, {map_y:.2f})")
            
            print(f"\n结束帧:")
            print(f"  文件名: {last.frame_name}")
            print(f"  时间戳: {last.timestamp}")
            print(f"  位置: ({last.latitude:.6f}, {last.longitude:.6f})")
            print(f"  速度: {last.speed_kmh:.2f} km/h")
            
            # 打印投影后的地图坐标
            if self.map_node:
                map_x, map_y = self.map_node.project_gps(last.latitude, last.longitude)
                print(f"  地图坐标: ({map_x:.2f}, {map_y:.2f})")
        
        # 打印最后一个环境模型的信息
        if self._last_env_model:
            last_env = self._last_env_model
            print(f"\n最后环境模型:")
            print(f"  帧索引: {last_env.frame_index}")
            print(f"  时间戳: {last_env.timestamp:.2f}")
            if last_env.ego_state and last_env.ego_state.local_state:
                pos = last_env.ego_state.local_state.position
                yaw = last_env.ego_state.local_state.orientation.yaw
                print(f"  局部坐标: ({pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f})")
                print(f"  局部航向: {yaw:.4f} rad ({math.degrees(yaw):.2f} deg)")
        
        print("=" * 60)
    
    def get_ego_states(self) -> List[EgoVehicleState]:
        """
        获取车辆状态列表
        
        Returns:
            List[EgoVehicleState]: 车辆状态列表
        """
        return self.ego_states
    
    def get_map_node(self) -> Optional[MapNode]:
        """
        获取地图节点
        
        Returns:
            MapNode: 地图节点实例
        """
        return self.map_node
    
    def get_env_node(self) -> Optional[EnvNode]:
        """
        获取环境模型节点
        
        Returns:
            EnvNode: 环境模型节点实例
        """
        return self.env_node
    
    def get_last_env_model(self) -> Optional[EnvironmentModel]:
        """
        获取最后一个环境模型
        
        Returns:
            Optional[EnvironmentModel]: 最后一个环境模型
        """
        return self._last_env_model


def main():
    """主函数"""
    import sys
    
    # 默认配置文件路径
    config_path = "configs/traffic_rule_config.yaml"
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # 创建并运行AllNodes
    allnodes = AllNodes(config_path)
    success = allnodes.run()
    
    if not success:
        sys.exit(1)
    
    return allnodes


if __name__ == "__main__":
    main()
