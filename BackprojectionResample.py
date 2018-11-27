import numpy as np
from numba import jit, prange

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

@jit(nopython=True)
def backprojection_resample(boundary, gsd, eo, R, ground_height, focal_length, pixel_size, image):
    # Boundary size
    boundary_cols = int((boundary[1, 0] - boundary[0, 0]) / gsd)
    boundary_rows = int((boundary[3, 0] - boundary[2, 0]) / gsd)

    # Image size
    image_rows = image.shape[0]
    image_cols = image.shape[1]

    # Define the orthophoto
    output_b = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    output_g = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    output_r = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    output_a = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)

    coord1 = np.empty(shape=(3, 1))
    coord2 = np.empty(shape=(2, 1))
    for row in prange(boundary_rows):
        for col in prange(boundary_cols):
            coord1[0] = boundary[0] + col * gsd - eo[0]
            coord1[1] = boundary[3] - row * gsd - eo[1]
            coord1[2] = ground_height - eo[2]

            # 3. Backprojection
            backProjection(coord1, R, focal_length, pixel_size, (image_rows, image_cols), coord2)

            # 4. Resampling
            resample(coord2, image, output_b, output_g, output_r, output_a, (row, col))

    return output_b, output_g, output_r, output_a
