import xml.etree.ElementTree as ET
import json
from pyproj import Proj, transform
import math

class CoordConverter:
    """Convert GPS/INS coordinates to xodr local coordinates using pre-calculated offsets"""
    
    def __init__(self, offset=None, proj=None):
        self.offset = offset if offset else {'x': 0.0, 'y': 0.0, 'z': 0.0, 'headingx': 0.0, 'headingy': 0.0, 'headingz': 0.0}
        self.proj = proj
    
    def convert_gps_to_utm(self, latitude, longitude, altitude=0):
        """
        Convert WGS84 GPS coordinates to UTM coordinates
        
        Args:
            latitude: GPS latitude in degrees
            longitude: GPS longitude in degrees
            altitude: GPS altitude in meters
        
        Returns:
            dict: {'x': utm_x, 'y': utm_y, 'z': altitude}
        """
        utm_x, utm_y = self.proj(longitude, latitude)
        return {
            'x': utm_x,
            'y': utm_y,
            'z': altitude
        }
    
    def convert_heading(self, gps_heading):
        """
        Convert GPS heading to xodr coordinate system heading
        
        GPS heading: 0°=North, 90°=East, 180°=South, 270°=West (clockwise)
        xodr heading: 0°=East, 90°=North, 180°=West, 270°=South (counter-clockwise from East)
        
        Args:
            gps_heading: GPS heading in degrees (0-360, North=0, clockwise)
        
        Returns:
            float: heading in xodr coordinate system (degrees, East=0, counter-clockwise)
        """
        # Convert GPS heading (North=0, clockwise) to math angle (East=0, counter-clockwise)
        xodr_heading = 90.0 - gps_heading
        
        # Normalize to [0, 360)
        while xodr_heading < 0:
            xodr_heading += 360
        while xodr_heading >= 360:
            xodr_heading -= 360
        
        return xodr_heading
    
    def apply_offset(self, x, y, z, heading):
        """
        Apply pre-calculated offsets to coordinates
        
        Offset formula: offset = xodr - UTM
        Conversion: xodr = UTM + offset
        
        Args:
            x, y, z: UTM coordinates
            heading: heading angle
        
        Returns:
            dict: coordinates with offsets applied
        """
        return {
            'x': x + self.offset.get('x', 0.0),
            'y': y + self.offset.get('y', 0.0),
            'z': z + self.offset.get('z', 0.0),
            'heading': {
                'x': heading - self.offset.get('headingx', 0.0),
                'y': heading - self.offset.get('headingy', 0.0),
                'z': heading - self.offset.get('headingz', 0.0)
            }
        }
    
    def convert_ins_data(self, ins_data):
        """
        Convert complete INS data to xodr coordinates with offsets
        
        Args:
            ins_data: dict containing GPS/INS data
        
        Returns:
            dict: converted coordinates in xodr system
        """
        # Extract GPS coordinates
        latitude = ins_data.get('latitude', 0)
        longitude = ins_data.get('longitude', 0)
        altitude = ins_data.get('altitude', 0)
        gps_heading = ins_data.get('heading', 0)
        
        # Convert position
        utm_coord = self.convert_gps_to_utm(latitude, longitude, altitude)
        
        # Convert heading
        xodr_heading = self.convert_heading(gps_heading)
        
        # Apply offsets
        result = self.apply_offset(utm_coord['x'], utm_coord['y'], utm_coord['z'], xodr_heading)
        result['original'] = {
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'heading': gps_heading
        }
        
        return result


def process_ins_json(json_file_path, offset=None):
    """
    Process INS data from JSON file and convert to xodr coordinates
    
    Args:
        json_file_path: path to JSON file containing ins_data
        offset: pre-calculated offset dict {'x', 'y', 'z', 'headingx', 'headingy', 'headingz'}
    
    Returns:
        dict: converted coordinates
    """
    # Load JSON data
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    ins_data = data.get('ins_data', data)
    
    # Initialize converter with offsets
    converter = CoordConverter(offset)
    
    # Convert coordinates
    result = converter.convert_ins_data(ins_data)
    
    return result


def process_ins_dict(ins_data, offset=None):
    """
    Process INS data from dict and convert to xodr coordinates
    
    Args:
        ins_data: dict containing GPS/INS data
        offset: pre-calculated offset dict {'x', 'y', 'z', 'headingx', 'headingy', 'headingz'}
    
    Returns:
        dict: converted coordinates
    """
    # Initialize converter with offsets
    converter = CoordConverter(offset)
    
    # Convert coordinates
    result = converter.convert_ins_data(ins_data)
    
    return result


def calculate_offset_from_points():
    """
    Calculate offset using the two matched INS/position points from proj.md
    Returns the offset dict for use in coordinate conversion
    
    Offset formula: offset = xodr - UTM
    Conversion formula: xodr = UTM + offset
    
    Note: Due to GPS measurement errors and potential map distortions,
    the two calibration points may have slightly different offsets.
    The average offset is returned for general use.
    """
    from pyproj import Proj
    
    # UTM projection for zone 51N (Shanghai area)
    proj = Proj(proj='utm', zone=51, ellps='WGS84')
    
    # INS data points from proj.md
    ins_data1 = {
        "latitude": 30.9679435,
        "longitude": 121.8847213,
        "altitude": 19.586
    }
    ins_data2 = {
        "latitude": 30.9500814,
        "longitude": 121.8856283,
        "altitude": 30.048
    }
    
    # Corresponding xodr positions from proj.md
    position1 = {'x': 5444.33, 'y': -6820.50, 'z': 17.89}
    position2 = {'x': 5519.30, 'y': -8700.16, 'z': 29.01}
    
    # Convert GPS to UTM
    utm_x1, utm_y1 = proj(ins_data1['longitude'], ins_data1['latitude'])
    utm_x2, utm_y2 = proj(ins_data2['longitude'], ins_data2['latitude'])
    
    # Calculate offsets: offset = xodr - UTM (so xodr = UTM + offset)
    offset_x1 = position1['x'] - utm_x1
    offset_y1 = position1['y'] - utm_y1
    offset_z1 = position1['z'] - ins_data1['altitude']
    
    offset_x2 = position2['x'] - utm_x2
    offset_y2 = position2['y'] - utm_y2
    offset_z2 = position2['z'] - ins_data2['altitude']
    
    # Average the offsets from both points
    offset = {
        'x': (offset_x1 + offset_x2) / 2,
        'y': (offset_y1 + offset_y2) / 2,
        'z': (offset_z1 + offset_z2) / 2,
        'headingx': 0.0,
        'headingy': 0.0,
        'headingz': 0.0
    }
    
    return offset, proj


def main():
    """Main function for projection calibration"""
    
    # Calculate offset from the two matched points
    offset, proj = calculate_offset_from_points()
    
    # Initialize converter with calculated offsets and projection
    converter = CoordConverter(offset, proj)
    
    # Test data from proj.md
    test_points = [
        {
            "name": "ins_data1 / position1",
            "ins_data": {
                "latitude": 30.9679435,
                "longitude": 121.8847213,
                "altitude": 19.586,
                "heading": 172.353515625
            },
            "expected": {'x': 5444.33, 'y': -6820.50, 'z': 17.89}
        },
        {
            "name": "ins_data2 / position2",
            "ins_data": {
                "latitude": 30.9500814,
                "longitude": 121.8856283,
                "altitude": 30.048,
                "heading": -178.17626953125
            },
            "expected": {'x': 5519.30, 'y': -8700.16, 'z': 29.01}
        }
    ]
    
    print("\n" + "="*60)
    print("COORDINATE OFFSET CALCULATION RESULTS")
    print("="*60)
    print(f"Calculated Offset:")
    print(f"  X Offset: {offset['x']:.4f} m")
    print(f"  Y Offset: {offset['y']:.4f} m")
    print(f"  Z Offset: {offset['z']:.4f} m")
    print(f"  Heading X Offset: {offset['headingx']:.4f} °")
    print(f"  Heading Y Offset: {offset['headingy']:.4f} °")
    print(f"  Heading Z Offset: {offset['headingz']:.4f} °")
    
    # Test conversion with both points
    for i, test_point in enumerate(test_points, 1):
        print("\n" + "="*60)
        print(f"TEST POINT {i}: {test_point['name']}")
        print("="*60)
        
        result = converter.convert_ins_data(test_point['ins_data'])
        expected = test_point['expected']
        
        print(f"Original GPS Coordinates:")
        print(f"  Latitude:  {result['original']['latitude']:.7f} °")
        print(f"  Longitude: {result['original']['longitude']:.7f} °")
        print(f"  Altitude:  {result['original']['altitude']:.3f} m")
        print(f"  Heading:   {result['original']['heading']:.4f} °")
        
        print(f"\nConverted xodr Coordinates:")
        print(f"  X: {result['x']:.4f} m (expected: {expected['x']:.2f} m)")
        print(f"  Y: {result['y']:.4f} m (expected: {expected['y']:.2f} m)")
        print(f"  Z: {result['z']:.4f} m (expected: {expected['z']:.2f} m)")
        
        # Calculate errors
        error_x = abs(result['x'] - expected['x'])
        error_y = abs(result['y'] - expected['y'])
        error_z = abs(result['z'] - expected['z'])
        
        print(f"\nConversion Errors:")
        print(f"  X Error: {error_x:.4f} m")
        print(f"  Y Error: {error_y:.4f} m")
        print(f"  Z Error: {error_z:.4f} m")
        print(f"  Total Error: {(error_x**2 + error_y**2 + error_z**2)**0.5:.4f} m")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()