import xml.etree.ElementTree as ET
import numpy as np
from pyproj import Proj, transform
import json

# Direct coordinate input (xodr local coordinates and GPS WGS84 coordinates)
# Data from proj.md - manually matched points
xodr_points = [
    {'x': 5444.33, 'y': -6820.50, 'z': 17.89},   # position1
    {'x': 5519.30, 'y': -8700.16, 'z': 29.01}    # position2
]

gps_points = [
    {'latitude': 30.9679435, 'longitude': 121.8847213, 'altitude': 19.586},  # ins_data1
    {'latitude': 30.9500814, 'longitude': 121.8856283, 'altitude': 30.048}   # ins_data2
]

class XodrParser:
    """Parse OpenDRIVE (.xodr) file and extract geographic information"""
    
    def __init__(self, xodr_path):
        self.xodr_path = xodr_path
        self.tree = ET.parse(xodr_path)
        self.root = self.tree.getroot()
        self.geo_reference = None
        self.roads = []
        
    def parse_geo_reference(self):
        """Extract geoReference projection information"""
        geo_ref_elem = self.root.find('.//geoReference')
        if geo_ref_elem is not None and geo_ref_elem.text:
            self.geo_reference = geo_ref_elem.text.strip()
        return self.geo_reference
    
    def parse_header(self):
        """Extract header information including bounding box"""
        header = self.root.find('header')
        if header is not None:
            return {
                'revMajor': header.get('revMajor'),
                'revMinor': header.get('revMinor'),
                'name': header.get('name'),
                'version': header.get('version'),
                'date': header.get('date'),
                'north': float(header.get('north', 0)),
                'south': float(header.get('south', 0)),
                'east': float(header.get('east', 0)),
                'west': float(header.get('west', 0))
            }
        return None
    
    def parse_roads(self):
        """Extract all road geometry information"""
        self.roads = []
        for road in self.root.findall('.//road'):
            road_info = {
                'id': road.get('id'),
                'name': road.get('name'),
                'length': float(road.get('length', 0)),
                'junction': road.get('junction'),
                'geometry': [],
                'elevation': [],
                'lanes': []
            }
            
            # Parse planView geometry
            plan_view = road.find('planView')
            if plan_view is not None:
                for geom in plan_view.findall('geometry'):
                    geom_info = {
                        's': float(geom.get('s', 0)),
                        'x': float(geom.get('x', 0)),
                        'y': float(geom.get('y', 0)),
                        'hdg': float(geom.get('hdg', 0)),
                        'length': float(geom.get('length', 0))
                    }
                    road_info['geometry'].append(geom_info)
            
            # Parse elevationProfile
            elevation_profile = road.find('elevationProfile')
            if elevation_profile is not None:
                for elev in elevation_profile.findall('elevation'):
                    elev_info = {
                        's': float(elev.get('s', 0)),
                        'a': float(elev.get('a', 0)),
                        'b': float(elev.get('b', 0)),
                        'c': float(elev.get('c', 0)),
                        'd': float(elev.get('d', 0))
                    }
                    road_info['elevation'].append(elev_info)
            
            self.roads.append(road_info)
        
        return self.roads
    
    def get_utm_projection(self):
        """Get UTM projection from geoReference"""
        if self.geo_reference:
            # Parse +proj=utm +zone=51 +ellps=WGS84 +datum=WGS84 +units=m +no_defs
            proj = Proj(self.geo_reference)
            return proj
        return None


class ShiftCalculator:
    """Calculate coordinate offset between xodr data and GPS data"""
    
    def __init__(self, xodr_path):
        self.parser = XodrParser(xodr_path)
        self.xodr_points = []
        self.gps_points = []
        # Support offset calculation for X, Y, Z axes and three-axis heading
        self.offset = {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0,
            'headingx': 0.0,
            'headingy': 0.0,
            'headingz': 0.0
        }
    
    def set_xodr_coordinates(self, points):
        """Set xodr coordinates directly"""
        self.xodr_points = points
        return self.xodr_points
    
    def set_gps_coordinates(self, points):
        """Set GPS coordinates directly and convert to UTM"""
        self.gps_points = []
        proj = self.parser.get_utm_projection()
        if proj is None:
            raise ValueError("Cannot get UTM projection from xodr file")
        
        for pt in points:
            # Convert WGS84 lat/lon to UTM
            utm_x, utm_y = proj(pt['longitude'], pt['latitude'])
            self.gps_points.append({
                'x': utm_x,
                'y': utm_y,
                'z': pt.get('altitude', 0)
            })
        
        return self.gps_points
    
    def load_gps_data(self, gps_file_path):
        """Load GPS data from file (support json/csv format)"""
        self.gps_points = []
        
        if gps_file_path.endswith('.json'):
            with open(gps_file_path, 'r') as f:
                data = json.load(f)
                for point in data:
                    self.gps_points.append({
                        'lon': point.get('longitude', point.get('lon', 0)),
                        'lat': point.get('latitude', point.get('lat', 0)),
                        'x': point.get('x', 0),
                        'y': point.get('y', 0),
                        's': point.get('s', 0)
                    })
        elif gps_file_path.endswith('.csv'):
            import csv
            with open(gps_file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.gps_points.append({
                        'lon': float(row.get('longitude', row.get('lon', 0))),
                        'lat': float(row.get('latitude', row.get('lat', 0))),
                        'x': float(row.get('x', 0)),
                        'y': float(row.get('y', 0)),
                        's': float(row.get('s', 0))
                    })
        
        return self.gps_points
    
    def calculate_offset(self, method='least_squares'):
        """
        Calculate coordinate offset between xodr and GPS data
        Note: All three axes (X, Y, Z) can have offsets
        Note: heading is a single angle (yaw around Z-axis), headingx/headingy are set to 0
        
        Args:
            method: 'least_squares' or 'average'
        
        Returns:
            dict: {'x': offset_x, 'y': offset_y, 'z': offset_z, 'headingx': 0.0, 'headingy': 0.0, 'headingz': offset_heading}
        """
        if len(self.xodr_points) == 0 or len(self.gps_points) == 0:
            raise ValueError("No data points available for offset calculation")
        
        if len(self.xodr_points) != len(self.gps_points):
            raise ValueError("Number of xodr points must match GPS points")
        
        # Match points by index (assumed to be corresponding pairs)
        matched_pairs = []
        for i in range(len(self.xodr_points)):
            matched_pairs.append({
                'xodr_x': self.xodr_points[i]['x'],
                'xodr_y': self.xodr_points[i]['y'],
                'xodr_z': self.xodr_points[i].get('z', 0),
                'gps_x': self.gps_points[i]['x'],
                'gps_y': self.gps_points[i]['y'],
                'gps_z': self.gps_points[i].get('z', 0)
            })
        
        if len(matched_pairs) < 2:
            raise ValueError("Not enough matched points for offset calculation")
        
        if method == 'average':
            # Simple average method
            x_diffs = [pair['xodr_x'] - pair['gps_x'] for pair in matched_pairs]
            y_diffs = [pair['xodr_y'] - pair['gps_y'] for pair in matched_pairs]
            z_diffs = [pair['xodr_z'] - pair['gps_z'] for pair in matched_pairs]
            heading_offset = self._calculate_heading_offset(matched_pairs)
            self.offset = {
                'x': np.mean(x_diffs),
                'y': np.mean(y_diffs),
                'z': np.mean(z_diffs),
                'headingx': 0.0,  # Roll offset - not calculated from 2D points
                'headingy': 0.0,  # Pitch offset - not calculated from 2D points
                'headingz': heading_offset  # Yaw/Heading offset - valid for planar coordinates
            }
        elif method == 'least_squares':
            # Least squares method for better accuracy
            x_diffs = [pair['xodr_x'] - pair['gps_x'] for pair in matched_pairs]
            y_diffs = [pair['xodr_y'] - pair['gps_y'] for pair in matched_pairs]
            z_diffs = [pair['xodr_z'] - pair['gps_z'] for pair in matched_pairs]
            
            # Remove outliers using 3-sigma rule
            x_diffs = self._remove_outliers(x_diffs)
            y_diffs = self._remove_outliers(y_diffs)
            z_diffs = self._remove_outliers(z_diffs)
            
            heading_offset = self._calculate_heading_offset(matched_pairs)
            self.offset = {
                'x': np.mean(x_diffs) if len(x_diffs) > 0 else 0.0,
                'y': np.mean(y_diffs) if len(y_diffs) > 0 else 0.0,
                'z': np.mean(z_diffs) if len(z_diffs) > 0 else 0.0,
                'headingx': 0.0,  # Roll offset - not calculated from 2D points
                'headingy': 0.0,  # Pitch offset - not calculated from 2D points
                'headingz': heading_offset  # Yaw/Heading offset - valid for planar coordinates
            }
        
        return self.offset
    
    def _calculate_heading_offset(self, matched_pairs):
        """
        Calculate heading offset between xodr and GPS coordinate systems
        
        Returns:
            float: heading offset in degrees
        """
        if len(matched_pairs) < 2:
            return 0.0
        
        # Calculate bearing angles for both coordinate systems
        xodr_headings = []
        gps_headings = []
        
        for i in range(len(matched_pairs) - 1):
            # Xodr heading (from point i to i+1)
            dx_xodr = matched_pairs[i+1]['xodr_x'] - matched_pairs[i]['xodr_x']
            dy_xodr = matched_pairs[i+1]['xodr_y'] - matched_pairs[i]['xodr_y']
            xodr_heading = np.degrees(np.arctan2(dy_xodr, dx_xodr))
            xodr_headings.append(xodr_heading)
            
            # GPS heading (from point i to i+1)
            dx_gps = matched_pairs[i+1]['gps_x'] - matched_pairs[i]['gps_x']
            dy_gps = matched_pairs[i+1]['gps_y'] - matched_pairs[i]['gps_y']
            gps_heading = np.degrees(np.arctan2(dy_gps, dx_gps))
            gps_headings.append(gps_heading)
        
        # Calculate heading differences
        heading_diffs = []
        for i in range(len(xodr_headings)):
            diff = xodr_headings[i] - gps_headings[i]
            # Normalize to [-180, 180]
            while diff > 180:
                diff -= 360
            while diff < -180:
                diff += 360
            heading_diffs.append(diff)
        
        return np.mean(heading_diffs) if heading_diffs else 0.0
    
    def _remove_outliers(self, data, sigma=3.0):
        """Remove outliers using 3-sigma rule"""
        if len(data) < 3:
            return data
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return data
        
        filtered = [x for x in data if abs(x - mean) < sigma * std]
        return filtered if len(filtered) > 0 else data
    
    def apply_offset(self, x, y, z=0):
        """
        Apply calculated offset to coordinates
        All three axes (X, Y, Z) are adjusted
        """
        return x - self.offset['x'], y - self.offset['y'], z - self.offset['z']

def main():
    """Main function for shift calibration"""
    xodr_path = r'c:\ws\data\gpsview\shift\lgdd.xodr'
    
    # Initialize calculator
    calculator = ShiftCalculator(xodr_path)
    
    # Parse geoReference from xodr
    print("Parsing xodr file for geoReference...")
    geo_ref = calculator.parser.parse_geo_reference()
    print(f"GeoReference: {geo_ref}")
    
    # Set xodr coordinates directly
    print("Setting xodr coordinates...")
    calculator.set_xodr_coordinates(xodr_points)
    print(f"Loaded {len(calculator.xodr_points)} xodr points")
    
    # Set GPS coordinates directly (will be converted to UTM)
    print("Loading GPS data and converting to UTM...")
    calculator.set_gps_coordinates(gps_points)
    print(f"Loaded {len(calculator.gps_points)} GPS points (converted to UTM)")
    
    # Calculate offset
    print("\n" + "="*50)
    print("CALIBRATION OFFSET RESULTS")
    print("="*50)
    offset = calculator.calculate_offset(method='average')
    print(f"X Offset: {offset['x']:.4f} m")
    print(f"Y Offset: {offset['y']:.4f} m")
    print(f"Z Offset: {offset['z']:.4f} m  # Vertical/Altitude offset")
    print(f"Heading X Offset: {offset['headingx']:.4f} degrees")
    print(f"Heading Y Offset: {offset['headingy']:.4f} degrees")
    print(f"Heading Z Offset: {offset['headingz']:.4f} degrees")
    print("="*50)
    print("\nNote: All three axes (X, Y, Z) support offset calculation.")
    print("Note: Original xodr file is NOT modified.")


if __name__ == '__main__':
    main()