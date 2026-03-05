1. 获取pkl数据序列的gps数据，并转换成局部地图坐标系。
2. pkl数据目录在 datas/pkl
3. 地图数据在 configs/maps/lgdd.xodr
4. 地图数据做了偏移，需要拟合坐标偏移的值，x,y,z,headingz
5. test_integration_main.py 里面有初步的拟合计算，但是有一点偏差，
6. 手动选择了两个点，大概可以配上，但手动测量偏差可能会非常大
GPS_CALIBRATION_POINTS = [
    {
        "ins_data": {
            "latitude": 30.9679435,
            "longitude": 121.8847213,
            "altitude": 19.586,
        },
        "expected_xodr": {'x': 5444.33, 'y': -6820.50, 'z': 17.89}
    },
    {
        "ins_data": {
            "latitude": 30.9500814,
            "longitude": 121.8856283,
            "altitude": 30.048,
        },
        "expected_xodr": {'x': 5519.30, 'y': -8700.16, 'z': 29.01}
    }
]
7. 已知条件是这段pkl数据的第一帧是在road 1034或road769最右侧车道范围内，最后一帧是在road530最左侧车道范围内，中间500帧左右大部分时间在道路的最右侧车道稳定行驶。
8. 请依据这些条件拟合出来偏移值。
