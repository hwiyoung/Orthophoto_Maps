import numpy as np
from numba import jit

@jit(nopython=True)
def projectedCoord(boundary, boundary_rows, boundary_cols, gsd, eo, ground_height):
    proj_coords = np.empty(shape=(3, boundary_rows * boundary_cols))
    i = 0
    for row in range(boundary_rows):
        for col in range(boundary_cols):
            proj_coords[0, i] = boundary[0, 0] + col * gsd - eo[0]
            proj_coords[1, i] = boundary[3, 0] - row * gsd - eo[1]
            i += 1
    proj_coords[2, :] = ground_height - eo[2]
    return proj_coords

#@profile
@jit(nopython=True)
def backProjection(coord, R, focal_length, pixel_size, image_size, coord_out):
    coord_CCS_m = np.dot(R, coord)  # unit: m
    scale = (coord_CCS_m[2]) / (-focal_length)
    plane_coord_CCS = coord_CCS_m[0:2] / scale

    # Convert CCS to Pixel Coordinate System
    coord_CCS_px = plane_coord_CCS / pixel_size  # unit: px

    coord_out[0] = image_size[1] / 2 + coord_CCS_px[0]
    coord_out[1] = image_size[0] / 2 - coord_CCS_px[1]

#@profile
@jit(nopython=True)
def resample(coord, image, b, g, r, a, row_col):
    # row_col: row, column in for loop
    proj_col = int(coord[0, 0])  # projected column
    proj_row = int(coord[1, 0])  # projected row

    if proj_col < 0 or proj_col >= image.shape[1]:
        return
    elif proj_row < 0 or proj_row >= image.shape[0]:
        return
    else:
        b[row_col[0], row_col[1]], g[row_col[0], row_col[1]], r[row_col[0], row_col[1]], a[row_col[0], row_col[1]] = \
            image[proj_row, proj_col][0], image[proj_row, proj_col][1], image[proj_row, proj_col][2], 255
