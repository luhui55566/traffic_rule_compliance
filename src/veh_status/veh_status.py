#!/usr/bin/env python3
"""
Vehicle Status Module - 车辆状态读取模块

该模块负责从pkl文件中读取车辆状态数据，包括GPS数据、姿态数据、IMU数据等，
为交通规则符合性判定系统提供自车状态信息。

Usage:
    from src.veh_status import VehStatusReader
    
    reader = VehStatusReader(config)
    reader.init()
    ego_states = reader.process()
    
    # 迭代器模式（内存友好）
    for state in reader.get_iterator():
        process_frame(state)
"""

import pickle
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator
from dataclasses import dataclass
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EgoVehicleState:
    """
    自车状态数据类
    
    包含车辆的所有状态信息，包括GPS位置、速度、姿态、IMU数据等。
    """
    # 时间信息
    timestamp: int = 0
    gps_week: int = 0
    gps_time: float = 0.0
    
    # GPS位置
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    
    # 姿态角
    heading: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    
    # 速度（东北天坐标系）
    velocity_east: float = 0.0   # Ve
    velocity_north: float = 0.0  # Vn
    velocity_up: float = 0.0     # Vu
    
    # 角速度
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    
    # 加速度
    acc_x: float = 0.0
    acc_y: float = 0.0
    acc_z: float = 0.0
    
    # 状态
    status: int = 0
    
    # 位姿矩阵
    pose: Optional[np.ndarray] = None
    
    # 帧信息
    frame_name: str = ""
    
    @classmethod
    def from_pkl_data(cls, data: Dict[str, Any], frame_name: str = "") -> 'EgoVehicleState':
        """
        从pkl文件数据创建EgoVehicleState实例
        
        Args:
            data: pkl文件中的完整数据字典
            frame_name: 帧文件名
            
        Returns:
            EgoVehicleState实例
        """
        ins_data = data.get('ins_data', {})
        
        return cls(
            timestamp=ins_data.get('timestamp', 0),
            gps_week=ins_data.get('gps_week', 0),
            gps_time=ins_data.get('gps_time', 0.0),
            latitude=ins_data.get('latitude', 0.0),
            longitude=ins_data.get('longitude', 0.0),
            altitude=ins_data.get('altitude', 0.0),
            heading=ins_data.get('heading', 0.0),
            pitch=ins_data.get('pitch', 0.0),
            roll=ins_data.get('roll', 0.0),
            velocity_east=ins_data.get('Ve', 0.0),
            velocity_north=ins_data.get('Vn', 0.0),
            velocity_up=ins_data.get('Vu', 0.0),
            gyro_x=ins_data.get('gyro_x', 0.0),
            gyro_y=ins_data.get('gyro_y', 0.0),
            gyro_z=ins_data.get('gyro_z', 0.0),
            acc_x=ins_data.get('acc_x', 0.0),
            acc_y=ins_data.get('acc_y', 0.0),
            acc_z=ins_data.get('acc_z', 0.0),
            status=ins_data.get('Status', 0),
            pose=ins_data.get('pose', None),
            frame_name=frame_name
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp,
            'gps_week': self.gps_week,
            'gps_time': self.gps_time,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'heading': self.heading,
            'pitch': self.pitch,
            'roll': self.roll,
            'velocity_east': self.velocity_east,
            'velocity_north': self.velocity_north,
            'velocity_up': self.velocity_up,
            'gyro_x': self.gyro_x,
            'gyro_y': self.gyro_y,
            'gyro_z': self.gyro_z,
            'acc_x': self.acc_x,
            'acc_y': self.acc_y,
            'acc_z': self.acc_z,
            'status': self.status,
            'pose': self.pose,
            'frame_name': self.frame_name
        }
    
    @property
    def speed(self) -> float:
        """计算水平速度标量（m/s）"""
        return np.sqrt(self.velocity_east**2 + self.velocity_north**2)
    
    @property
    def speed_kmh(self) -> float:
        """计算水平速度标量（km/h）"""
        return self.speed * 3.6
    
    def get_position(self) -> tuple:
        """获取GPS位置元组"""
        return (self.latitude, self.longitude, self.altitude)


class VehStatusReader:
    """
    车辆状态读取器
    
    负责从pkl文件目录读取车辆状态数据，提供初始化、处理和迭代接口。
    
    Example:
        >>> reader = VehStatusReader(config)
        >>> reader.init()
        >>> states = reader.process()
        >>> print(f"共读取 {len(states)} 帧数据")
        
        >>> # 迭代器模式
        >>> for state in reader.get_iterator():
        ...     print(f"位置: {state.latitude}, {state.longitude}")
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化车辆状态读取器
        
        Args:
            config: 配置字典，应包含 vehicle.pkl_directory 字段
        """
        self.config = config
        self._pkl_path: Optional[Path] = None
        self._pkl_files: Optional[List[Path]] = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._initialized: bool = False
        
    def init(self) -> bool:
        """
        初始化模块，验证pkl目录有效性
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 从配置获取pkl目录
            vehicle_config = self.config.get('vehicle', {})
            pkl_directory = vehicle_config.get('pkl_directory', 'datas/pkl')
            
            # 构建完整路径
            project_root = Path(__file__).parent.parent.parent
            self._pkl_path = project_root / pkl_directory
            
            if not self._pkl_path.exists():
                logger.error(f"PKL目录不存在: {self._pkl_path}")
                return False
            
            # 获取pkl文件列表
            self._pkl_files = sorted(self._pkl_path.glob("*.pkl"))
            
            if len(self._pkl_files) == 0:
                logger.warning(f"PKL目录中没有找到pkl文件: {self._pkl_path}")
                return False
            
            self._initialized = True
            logger.info(f"VehStatusReader初始化成功，找到 {len(self._pkl_files)} 个pkl文件")
            return True
            
        except Exception as e:
            logger.error(f"VehStatusReader初始化失败: {e}")
            return False
    
    def _load_pkl_file(self, pkl_path: Path) -> Dict[str, Any]:
        """
        加载pkl文件（带缓存）
        
        Args:
            pkl_path: pkl文件路径
            
        Returns:
            pkl文件内容字典
        """
        path_str = str(pkl_path)
        if path_str not in self._cache:
            try:
                with open(pkl_path, 'rb') as f:
                    self._cache[path_str] = pickle.load(f)
            except Exception as e:
                logger.warning(f"加载pkl文件失败 {pkl_path}: {e}")
                return {}
        return self._cache[path_str]
    
    def process(self) -> List[EgoVehicleState]:
        """
        处理所有pkl文件，返回自车状态列表
        
        Returns:
            List[EgoVehicleState]: 自车状态列表，按文件名排序
        """
        if not self._initialized:
            raise RuntimeError("VehStatusReader未初始化，请先调用init()")
        
        states = []
        for pkl_file in self._pkl_files:
            try:
                data = self._load_pkl_file(pkl_file)
                if data:
                    state = EgoVehicleState.from_pkl_data(data, pkl_file.name)
                    states.append(state)
            except Exception as e:
                logger.warning(f"处理pkl文件失败 {pkl_file}: {e}")
                continue
        
        logger.info(f"成功处理 {len(states)} 帧车辆状态数据")
        return states
    
    def get_frame_count(self) -> int:
        """
        获取总帧数
        
        Returns:
            int: pkl文件总数
        """
        if not self._initialized:
            raise RuntimeError("VehStatusReader未初始化，请先调用init()")
        return len(self._pkl_files)
    
    def get_frame_by_index(self, index: int) -> Optional[EgoVehicleState]:
        """
        按索引获取单帧状态
        
        Args:
            index: 帧索引（0-based）
            
        Returns:
            Optional[EgoVehicleState]: 单帧状态，索引无效时返回None
        """
        if not self._initialized:
            raise RuntimeError("VehStatusReader未初始化，请先调用init()")
        
        if 0 <= index < len(self._pkl_files):
            pkl_file = self._pkl_files[index]
            try:
                data = self._load_pkl_file(pkl_file)
                if data:
                    return EgoVehicleState.from_pkl_data(data, pkl_file.name)
            except Exception as e:
                logger.warning(f"获取帧失败 {pkl_file}: {e}")
        return None
    
    def get_iterator(self) -> Iterator[EgoVehicleState]:
        """
        获取状态迭代器，支持逐帧处理（内存友好）
        
        Yields:
            EgoVehicleState: 单帧车辆状态
        """
        if not self._initialized:
            raise RuntimeError("VehStatusReader未初始化，请先调用init()")
        
        for pkl_file in self._pkl_files:
            try:
                data = self._load_pkl_file(pkl_file)
                if data:
                    yield EgoVehicleState.from_pkl_data(data, pkl_file.name)
            except Exception as e:
                logger.warning(f"迭代处理pkl文件失败 {pkl_file}: {e}")
                continue
    
    def get_first_last(self) -> tuple:
        """
        获取第一帧和最后一帧状态
        
        Returns:
            tuple: (first_state, last_state)，如果为空则返回(None, None)
        """
        if not self._initialized or len(self._pkl_files) == 0:
            return None, None
        
        first = self.get_frame_by_index(0)
        last = self.get_frame_by_index(len(self._pkl_files) - 1)
        return first, last
    
    def clear_cache(self) -> None:
        """清除内部缓存"""
        self._cache.clear()
        logger.debug("缓存已清除")


def main():
    """主函数 - 演示模块使用"""
    import yaml
    
    # 尝试从配置文件加载
    config_path = Path(__file__).parent.parent.parent / "configs" / "traffic_rule_config.yaml"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # 使用API
        reader = VehStatusReader(config)
        if reader.init():
            states = reader.process()
            print(f"\n使用VehStatusReader API:")
            print(f"共读取 {len(states)} 帧数据")
            
            if states:
                print(f"\n第一帧:")
                first = states[0]
                print(f"  文件名: {first.frame_name}")
                print(f"  位置: ({first.latitude}, {first.longitude})")
                print(f"  速度: {first.speed_kmh:.2f} km/h")
                
                print(f"\n最后一帧:")
                last = states[-1]
                print(f"  文件名: {last.frame_name}")
                print(f"  位置: ({last.latitude}, {last.longitude})")
                print(f"  速度: {last.speed_kmh:.2f} km/h")
    else:
        print(f"配置文件不存在: {config_path}")
    
    return locals().get('states', [])


if __name__ == "__main__":
    main()
