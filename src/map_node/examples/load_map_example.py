"""
示例脚本：演示如何使用MapLoader加载OSM地图
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from map_node.maploader.loader import MapLoader
from map_node.maploader.utils import UtmProjectorWrapper
from map_node.maploader.visualization import MapVisualizer, visualize_map_simple
from map_node.map_common.base import Position

try:
    from lanelet2.io import Origin
    from lanelet2.core import GPSPoint
except ImportError:
    print("错误: Lanelet2未安装。请先安装：")
    print("  sudo apt-get install liblanelet2-dev python3-lanelet2")
    sys.exit(1)

#from lanelet2 import visualization
import lanelet2
print(dir(lanelet2))

def main():
    """主函数"""
    print("=" * 60)
    print("MapLoader 使用示例")
    print("=" * 60)
    
    # 1. 创建地图加载器
    print("\n1. 创建MapLoader...")
    loader = MapLoader()
    print("   ✓ MapLoader创建成功")
    
    # 2. 加载地图
    print("\n2. 加载OSM地图...")
    map_file = Path(__file__).parent.parent.parent.parent / "configs" / "maps" / "Town10HD.osm"
    
    if not map_file.exists():
        print(f"   ✗ 地图文件不存在: {map_file}")
        return
    
    # 使用coordinate_type="local"加载地图（使用local_x/local_y标签）
    # 对于local坐标，loader内部会使用Origin(0,0)来保留原始的local_x/local_y值
    success = loader.load_map(str(map_file), coordinate_type="local")
    
    if not success:
        print("   ✗ 地图加载失败")
        return
    
    print("   ✓ 地图加载成功")
    
    # 3. 获取地图信息
    print("\n3. 获取地图信息...")
    map_info = loader.get_map_info()
    print(f"   地图类型: {map_info.map_type}")
    print(f"   地图文件: {map_info.file_path}")
    print(f"   车道数量: {map_info.num_lanelets}")
    print(f"   坐标系: {map_info.coordinate_system}")
    print(f"   已加载: {map_info.is_loaded}")
    
    # 4. 获取地图数据
    print("\n4. 获取地图数据...")
    map_data = loader.get_map_data()
    lanelet_map = map_data.get('lanelet_map')
    if lanelet_map:
        print("   ✓ 地图数据获取成功")
        print(f"   车道数量: {len(lanelet_map.laneletLayer)}")
    else:
        print("   ✗ 没有地图数据")
    
    # 5. 可视化地图
    print("\n5. 可视化地图...")
    if lanelet_map:
        # 使用简单可视化函数
        print("   正在生成地图可视化...")
        try:
            visualize_map_simple(
                lanelet_map,
                title=f"Town10HD 地图可视化 ({map_info.num_lanelets} 车道)",
                save_path=str(Path(__file__).parent / "map_visualization.png")
            )
            print("   ✓ 地图可视化完成")
        except ImportError as e:
            print(f"   ⚠ 可视化失败: {e}")
            print("   提示: 请安装 matplotlib 以启用可视化功能")
            print("         pip install matplotlib")
        except Exception as e:
            print(f"   ✗ 可视化出错: {e}")
    else:
        print("   ✗ 没有地图数据可供可视化")
    
    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
