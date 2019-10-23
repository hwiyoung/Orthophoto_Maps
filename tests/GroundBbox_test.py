import numpy as np
from EoData import readEO, Rot3D, latlon2tmcentral, tmcentral2latlon
from Boundary import pcs2ccs, projection

bbox_px = np.array([[79, 159, 159, 79],
                    [2719, 2719, 2639, 2639]])

eo_path = '../Data/DJI_0386.txt'
rows = 3000
cols = 4000
sensor_width = 6.3  # unit: mm
pixel_size = sensor_width / cols    # mm/px
focal_length = 4.7  # mm
ground_height = 65  # unit: m

eo = readEO(eo_path)
eo = latlon2tmcentral(eo)
R_GC = Rot3D(eo)
R_CG = R_GC.transpose()

# Convert pixel coordinate system to camera coordinate system
bbox_camera = pcs2ccs(bbox_px, rows, cols,
                      pixel_size, focal_length)    # shape: 3 x bbox_point

# Project camera coordinates to ground coordinates
proj_coordinates = projection(bbox_camera, eo, R_CG, ground_height)

bbox_ground1 = tmcentral2latlon(proj_coordinates[:, 0])
bbox_ground2 = tmcentral2latlon(proj_coordinates[:, 1])
bbox_ground3 = tmcentral2latlon(proj_coordinates[:, 2])
bbox_ground4 = tmcentral2latlon(proj_coordinates[:, 3])
print(bbox_ground1, '\n', bbox_ground2, '\n', bbox_ground3, '\n', bbox_ground4)

print('Hello')
