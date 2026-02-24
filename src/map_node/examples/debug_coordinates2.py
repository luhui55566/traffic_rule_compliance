"""
Debug script to understand how Lanelet2 loads coordinates from OSM file.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    import lanelet2
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
    print("Lanelet2坐标加载调试")
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
    
    # 2. Load map WITH origin (0,0) to see what Lanelet2 does
    print("\n2. 使用Lanelet2加载地图（使用原点0,0）...")
    
    # Load with origin at (0,0)
    gps_point_zero = GPSPoint(lat=0.0, lon=0.0)
    origin_zero = Origin(gps_point_zero)
    lanelet_map = lanelet2.io.load(str(map_file), origin_zero)
    
    if lanelet_map is None:
        print("   ✗ 地图加载失败")
        return
    
    print("   ✓ 地图加载成功")
    print(f"   地图中的点数量: {len(lanelet_map.pointLayer)}")
    
    # 3. Compare coordinates
    print("\n3. 比较坐标（无投影器）...")
    
    # Create a dictionary of lanelet points by ID
    lanelet_points = {str(point.id): point for point in lanelet_map.pointLayer}
    
    # Compare first 5 points from OSM file
    print("\n   比较OSM文件中的前5个节点:")
    for i, (node_id, osm_coord) in enumerate(list(osm_coords.items())[:5]):
        print(f"   Node {node_id}:")
        print(f"     OSM local_x={osm_coord['local_x']:.2f}, local_y={osm_coord['local_y']:.2f}")
        
        if node_id in lanelet_points:
            point = lanelet_points[node_id]
            print(f"     Lanelet2 x={point.x:.2f}, y={point.y:.2f}")
            print(f"     差异: dx={point.x - osm_coord['local_x']:.2f}, dy={point.y - osm_coord['local_y']:.2f}")
        else:
            print(f"     Lanelet2中未找到此点")
    
    # 4. Load map WITH projector (Beijing Tiananmen)
    print("\n4. 使用Lanelet2加载地图（使用北京天安门原点）...")
    
    # Create origin (using Beijing Tiananmen as example)
    gps_point = GPSPoint(lat=39.9042, lon=116.4074)
    origin = Origin(gps_point)
    
    lanelet_map2 = lanelet2.io.load(str(map_file), origin)
    
    if lanelet_map2 is None:
        print("   ✗ 地图加载失败")
        return
    
    print("   ✓ 地图加载成功")
    print(f"   地图中的点数量: {len(lanelet_map2.pointLayer)}")
    
    # 5. Compare coordinates with projector
    print("\n5. 比较坐标（有投影器）...")
    
    # Create a dictionary of lanelet points by ID
    lanelet_points2 = {str(point.id): point for point in lanelet_map2.pointLayer}
    
    # Compare first 5 points from OSM file
    print("\n   比较OSM文件中的前5个节点:")
    for i, (node_id, osm_coord) in enumerate(list(osm_coords.items())[:5]):
        print(f"   Node {node_id}:")
        print(f"     OSM local_x={osm_coord['local_x']:.2f}, local_y={osm_coord['local_y']:.2f}")
        
        if node_id in lanelet_points2:
            point = lanelet_points2[node_id]
            print(f"     Lanelet2 x={point.x:.2f}, y={point.y:.2f}")
            print(f"     差异: dx={point.x - osm_coord['local_x']:.2f}, dy={point.y - osm_coord['local_y']:.2f}")
        else:
            print(f"     Lanelet2中未找到此点")
    
    # 6. Check if lat/lon are actually GPS or relative
    print("\n6. 分析lat/lon的性质...")
    print("   OSM文件中的lat/lon值非常小（例如 lat=0.00008444, lon=0.00097084）")
    print("   这些不是GPS坐标，而是相对于某个原点的偏移量")
    print("   Lanelet2将它们当作GPS坐标处理，导致坐标转换错误")
    print("   正确的做法是直接使用local_x/local_y标签中的值")
    
    # 7. Summary
    print("\n7. 总结...")
    print("   问题根源：")
    print("   - OSM文件中的lat/lon不是真实的GPS坐标")
    print("   - Lanelet2使用lat/lon进行UTM投影转换")
    print("   - 这导致加载后的坐标与local_x/local_y不一致")
    print("   ")
    print("   解决方案：")
    print("   - 需要修改加载逻辑，直接使用local_x/local_y标签")
    print("   - 或者修改OSM文件，将local_x/local_y作为lat/lon")
    
    print("\n" + "=" * 60)
    print("调试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
