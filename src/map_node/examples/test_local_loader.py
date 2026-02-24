"""
Test script for LocalMapLoader - uses local_x/local_y tags directly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from map_node.maploader.loader_local import LocalMapLoader
from map_node.maploader.visualization import MapVisualizer, visualize_map_simple


def main():
    """Main function."""
    print("=" * 60)
    print("LocalMapLoader 测试")
    print("=" * 60)
    
    # 1. Create loader
    print("\n1. 创建LocalMapLoader...")
    loader = LocalMapLoader()
    print("   ✓ LocalMapLoader创建成功")
    
    # 2. Load map
    print("\n2. 加载OSM地图...")
    map_file = Path(__file__).parent.parent.parent.parent / "configs" / "maps" / "Town10HD.osm"
    
    if not map_file.exists():
        print(f"   ✗ 地图文件不存在: {map_file}")
        return
    
    success = loader.load_map(str(map_file))
    
    if not success:
        print("   ✗ 地图加载失败")
        return
    
    print("   ✓ 地图加载成功")
    
    # 3. Get map info
    print("\n3. 获取地图信息...")
    map_info = loader.get_map_info()
    print(f"   地图类型: {map_info.map_type}")
    print(f"   地图文件: {map_info.file_path}")
    print(f"   车道数量: {map_info.num_lanelets}")
    print(f"   坐标系: {map_info.coordinate_system}")
    print(f"   已加载: {map_info.is_loaded}")
    
    # 4. Get map data
    print("\n4. 获取地图数据...")
    map_data = loader.get_map_data()
    lanelet_map = map_data.get('lanelet_map')
    if lanelet_map:
        print("   ✓ 地图数据获取成功")
        print(f"   点数量: {len(lanelet_map.pointLayer)}")
        print(f"   线数量: {len(lanelet_map.lineStringLayer)}")
        print(f"   车道数量: {len(lanelet_map.laneletLayer)}")
    else:
        print("   ✗ 没有地图数据")
    
    # 5. Show first few points
    print("\n5. 显示前5个点...")
    if lanelet_map:
        for i, point in enumerate(list(lanelet_map.pointLayer)[:5]):
            print(f"   Point {point.id}: x={point.x:.2f}, y={point.y:.2f}, z={point.z:.2f}")
    
    # 6. Visualize map
    print("\n6. 可视化地图...")
    if lanelet_map:
        print("   正在生成地图可视化...")
        try:
            visualize_map_simple(
                lanelet_map,
                title=f"Town10HD 地图可视化 (local_x/local_y) - {map_info.num_lanelets} 车道",
                save_path=str(Path(__file__).parent / "map_visualization_local.png")
            )
            print("   ✓ 地图可视化完成")
        except ImportError as e:
            print(f"   ⚠ 可视化失败: {e}")
            print("   提示: 请安装 matplotlib 以启用可视化功能")
            print("         pip install matplotlib")
        except Exception as e:
            print(f"   ✗ 可视化出错: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("   ✗ 没有地图数据可供可视化")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
