"""
Vehicle Status Module - 车辆状态读取模块

该模块负责从pkl文件中读取车辆状态数据，为交通规则符合性判定系统提供自车状态信息。

主要类:
    - VehStatusReader: 车辆状态读取器
    - EgoVehicleState: 自车状态数据类

Usage:
    from src.veh_status import VehStatusReader, EgoVehicleState
    
    reader = VehStatusReader(config)
    reader.init()
    states = reader.process()
"""

from .veh_status import (
    EgoVehicleState,
    VehStatusReader,
)

__all__ = [
    'EgoVehicleState',
    'VehStatusReader',
]
