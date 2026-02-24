"""
Debug script to compare OSM file coordinates with loaded map coordinates.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from map_node.maploader.loader import MapLoader
from map_node.maploader.utils import UtmProjectorWrapper

try:
    from lanelet2.io import Origin
    from lanelet2.core import GPSPoint
except ImportError:
    print("错误: Lanelet2未安装。请先安装：")
    print("  sudo apt-get install liblanelet2-dev python3-lanelet2")
    sys.exit(1)

import xml.etree.ElementTree as ET


def parse_osm_local_coords(osm_file: str):
    """Parse local_x and local_y from OSM file."""
    tree = ET.parse(osm_file)
    root = tree.getroot()
    
    local_coords = {}
    for node in root.findall('node'):
        node_id = node.get('id')
        local_x = None
        local_y = None
        lat = None
        lon = None
        
        for tag in node.findall('tag'):
            k = tag.get('k')
            v = tag.get('v')
            if k == 'local_x':
                local_x = float(v)
            elif k == 'local_y':
                local_y = float(v)
        
        lat = float(node.get('lat'))
        lon = float(node.get('lon'))
        
        if local_x is not None and local_y is not None:
            local_coords[node_id] = {
                'local_x': local_x,
                'local_y': local_y,
                'lat': lat,
                'lon': lon
            }
    
    return local_coords


def main():
    """Main function."""
    print("=" * 60)
    print("坐标调试脚本")
    print("=" * 60)
    
    # 1. Parse OSM file directly
    print("\n1. 解析OSM文件中的坐标...")
    map_file = Path(__file__).parent.parent.parent.parent / "configs" / "maps" / "Town10HD.osm"
    
    if not map_file.exists():
        print(f"   ✗ 地图文件不存在: {map_file}")
        return
    
    osm_coords = parse_osm_local_coords(str(map_file))
    print(f"   ✓ 找到 {len(osm_coords)} 个带有local_x/local_y的节点")
    
    # Show first few nodes
    print("\n   OSM文件中的前5个节点:")
    for i, (node_id, coords) in enumerate(list(osm_coords.items())[:5]):
        print(f"   Node {node_id}: local_x={coords['local_x']:.2f}, local_y={coords['local_y']:.2f}, lat={coords['lat']:.8f}, lon={coords['lon']:.8f}")
    
    # 2. Load map using Lanelet2
    print("\n2. 使用Lanelet2加载地图...")
    loader = MapLoader()
    
    # Load with coordinate_type="local" (uses local_x/local_y tags)
    success = loader.load_map(str(map_file), coordinate_type="local")
    
    if not success:
        print("   ✗ 地图加载失败")
        return
    
    print("   ✓ 地图加载成功")
    
    # 3. Compare coordinates
    print("\n3. 比较坐标...")
    lanelet_map = loader.get_map_data()['lanelet_map']
    
    print(f"   地图中的点数量: {len(lanelet_map.pointLayer)}")
    
    # Get first few points from lanelet map
    print("\n   Lanelet2地图中的前5个点:")
    for i, point in enumerate(list(lanelet_map.pointLayer)[:5]):
        print(f"   Point {point.id}: x={point.x:.2f}, y={point.y:.2f}")
        
        # Check if this point exists in OSM coords
        if str(point.id) in osm_coords:
            osm_coord = osm_coords[str(point.id)]
            print(f"     OSM local_x={osm_coord['local_x']:.2f}, local_y={osm_coord['local_y']:.2f}")
            print(f"     差异: dx={point.x - osm_coord['local_x']:.2f}, dy={point.y - osm_coord['local_y']:.2f}")
    
    # 4. Test coordinate transformation
    print("\n4. 测试坐标转换...")
    if osm_coords:
        first_node_id = list(osm_coords.keys())[0]
        osm_coord = osm_coords[first_node_id]
        
        # Convert lat/lon to map coordinates using projector
        from map_node.map_common.base import Position
        gps_pos = Position(latitude=osm_coord['lat'], longitude=osm_coord['lon'])
        map_point = projector.forward(gps_pos)
        
        print(f"   节点 {first_node_id}:")
        print(f"     OSM lat/lon: ({osm_coord['lat']:.8f}, {osm_coord['lon']:.8f})")
        print(f"     OSM local_x/local_y: ({osm_coord['local_x']:.2f}, {osm_coord['local_y']:.2f})")
        print(f"     投影器转换结果: ({map_point.x:.2f}, {map_point.y:.2f})")
        print(f"     Lanelet2加载结果: 需要查找对应点")
    
    print("\n" + "=" * 60)
    print("调试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
