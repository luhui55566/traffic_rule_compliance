1. 建立unittest测试，对localmap进行模块单元测试.测试文件存储在/src/map_node/localmap/xodrconvert/test内， 模块的总体运行逻辑参考/home/rldev/mapws/lanelet_test/src/map_node/localmap/xodrconvert/test/test_lane_point_conversion.py
2. 测试点选择：在road和juction上随机选择10个合理的测试点，road和junction各占一半,对每个选择的点最终生成一个可视化的图片，参考/home/rldev/mapws/lanelet_test/src/map_node/localmap/xodrconvert/test/test_lane_point_conversion.py
3. 检查新生成的LocalMap中数据合理性，校验所有lane的连接关系，校验lane中的前后继的节点的中心线首位衔接点间距需要在阈值内；依据Lane中的original_lane_id，original_road_id，original_junction_id查询与原始Lane的连接关系是否一致
4. 测试结果可视化：将测试结果可视化，参考/home/rldev/mapws/lanelet_test/src/map_node/localmap/xodrconvert/test/test_lane_point_conversion.py
5. 测试经纬度"latitude": 30.968457,"longitude": 121.8846405,"altitude": 19.561,对应得局部地图，并保存可视化图片