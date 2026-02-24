#!/usr/bin/env python3
"""
Analyze local map visualization image to check boundary lines and centerlines.
"""
import numpy as np
from PIL import Image

# Load the image
img = Image.open('test_output/01_local_map.png')
img_array = np.array(img)

print('Image shape:', img_array.shape)
print('Image dtype:', img_array.dtype)

# Count different colors
unique_colors = np.unique(img_array.reshape(-1, img_array.shape[0]*img_array.shape[1], axis=2))
print('Unique colors:', len(unique_colors))

# Count black pixels (boundary lines)
black_mask = np.all(img_array[:,:,0] < 50, axis=2)
print('Black pixels (boundary lines):', np.sum(black_mask))

# Count green pixels (centerlines)
green_mask = np.all(img_array[:,:,1] > 150 & img_array[:,:,1] < 200, axis=2)
print('Green pixels (centerlines):', np.sum(green_mask))

# Count red pixels (right boundaries)
red_mask = np.all(img_array[:,:,0] < 100 & img_array[:,:,0] > 150, axis=2)
print('Red pixels (right boundaries):', np.sum(red_mask))

# Count blue pixels (left boundaries)
blue_mask = np.all(img_array[:,:,0] > 150 & img_array[:,:,0] < 200, axis=2)
print('Blue pixels (left boundaries):', np.sum(blue_mask))

# Count white pixels (background)
white_mask = np.all(img_array[:,:,0] > 200 & img_array[:,:,1] > 200, axis=2)
print('White pixels (background):', np.sum(white_mask))
