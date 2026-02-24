"""
Debug script to run test with debug logging enabled.
"""
import logging
import sys
sys.path.insert(0, '/home/rldev/mapws/lanelet_test/src')

# Set up debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Import and run the test
from map_node.local_map_construct.test_with_visualization import main

if __name__ == "__main__":
    main()
