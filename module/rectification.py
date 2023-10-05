import numpy as np
from numba import jit, prange
from osgeo import gdal, osr
import cv2


@jit(nopython=True, parallel=True)
def rectify_plane_parallel(image, pixel_size, focal_length, pos, R, ground_height, boundary, gsd):
    # 1. projection
    proj_coords_x = 0.
    proj_coords_y = 0.
    proj_coords_z = 0.

    # 2. back-projection
    coord_CCS_m_x = 0.
    coord_CCS_m_y = 0.
    coord_CCS_m_z = 0.
    plane_coord_CCS_x = 0.
    plane_coord_CCS_y = 0.
    coord_CCS_px_x = 0.
    coord_CCS_px_y = 0.

    # 3. resample
    coord_ICS_col = 0
    coord_ICS_row = 0
    # Define channels of an orthophoto
    boundary_cols = int((boundary[1, 0] - boundary[0, 0]) / gsd)
    boundary_rows = int((boundary[3, 0] - boundary[2, 0]) / gsd)
    b = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    g = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    r = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    a = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)

    for row in prange(boundary_rows):
        for col in range(boundary_cols):
            # 1. projection
            proj_coords_x = boundary[0, 0] + col * gsd - pos[0]
            proj_coords_y = boundary[3, 0] - row * gsd - pos[1]
            proj_coords_z = ground_height - pos[2]

            # 2. back-projection - unit: m
            coord_CCS_m_x = R[0, 0] * proj_coords_x + R[0, 1] * proj_coords_y + R[0, 2] * proj_coords_z
            coord_CCS_m_y = R[1, 0] * proj_coords_x + R[1, 1] * proj_coords_y + R[1, 2] * proj_coords_z
            coord_CCS_m_z = R[2, 0] * proj_coords_x + R[2, 1] * proj_coords_y + R[2, 2] * proj_coords_z

            scale = (coord_CCS_m_z) / (-focal_length)  # scalar
            plane_coord_CCS_x = coord_CCS_m_x / scale
            plane_coord_CCS_y = coord_CCS_m_y / scale

            # Convert CCS to Pixel Coordinate System - unit: px
            coord_CCS_px_x = plane_coord_CCS_x / pixel_size
            coord_CCS_px_y = -plane_coord_CCS_y / pixel_size

            # 3. resample
            # Nearest Neighbor
            coord_ICS_col = int(image.shape[1] / 2 + coord_CCS_px_x)  # column
            coord_ICS_row = int(image.shape[0] / 2 + coord_CCS_px_y)  # row

            if coord_ICS_col < 0 or coord_ICS_col >= image.shape[1]:      # column
                continue
            elif coord_ICS_row < 0 or coord_ICS_row >= image.shape[0]:    # row
                continue
            else:
                b[row, col] = image[coord_ICS_row, coord_ICS_col][0]
                g[row, col] = image[coord_ICS_row, coord_ICS_col][1]
                r[row, col] = image[coord_ICS_row, coord_ICS_col][2]
                a[row, col] = 255

    return b, g, r, a


@jit(nopython=True, parallel=True)
def rectify_dem_parallel(image, pixel_size, focal_length, pos, R, dem_x, dem_y, dem_z):
    # 1. projection
    proj_coords_x = 0.
    proj_coords_y = 0.
    proj_coords_z = 0.

    # 2. back-projection
    coord_CCS_m_x = 0.
    coord_CCS_m_y = 0.
    coord_CCS_m_z = 0.
    plane_coord_CCS_x = 0.
    plane_coord_CCS_y = 0.
    coord_CCS_px_x = 0.
    coord_CCS_px_y = 0.

    # 3. resample
    coord_ICS_col = 0
    coord_ICS_row = 0
    # Define channels of an orthophoto
    boundary_rows = dem_x.shape[0]
    boundary_cols = dem_x.shape[1]
    b = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    g = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    r = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    a = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)

    for row in prange(boundary_rows):
        for col in range(boundary_cols):
            # 1. projection
            proj_coords_x = dem_x[row, col] - pos[0]
            proj_coords_y = dem_y[row, col] - pos[1]
            proj_coords_z = dem_z[row, col] - pos[2]

            # 2. back-projection - unit: m
            coord_CCS_m_x = R[0, 0] * proj_coords_x + R[0, 1] * proj_coords_y + R[0, 2] * proj_coords_z
            coord_CCS_m_y = R[1, 0] * proj_coords_x + R[1, 1] * proj_coords_y + R[1, 2] * proj_coords_z
            coord_CCS_m_z = R[2, 0] * proj_coords_x + R[2, 1] * proj_coords_y + R[2, 2] * proj_coords_z

            scale = (coord_CCS_m_z) / (-focal_length)  # scalar
            plane_coord_CCS_x = coord_CCS_m_x / scale
            plane_coord_CCS_y = coord_CCS_m_y / scale

            # Convert CCS to Pixel Coordinate System - unit: px
            coord_CCS_px_x = plane_coord_CCS_x / pixel_size
            coord_CCS_px_y = -plane_coord_CCS_y / pixel_size

            # 3. resample
            # Nearest Neighbor
            coord_ICS_col = int(image.shape[1] / 2 + coord_CCS_px_x)  # column
            coord_ICS_row = int(image.shape[0] / 2 + coord_CCS_px_y)  # row

            if coord_ICS_col < 0 or coord_ICS_col >= image.shape[1]:      # column
                continue
            elif coord_ICS_row < 0 or coord_ICS_row >= image.shape[0]:    # row
                continue
            else:
                b[row, col] = image[coord_ICS_row, coord_ICS_col][0]
                g[row, col] = image[coord_ICS_row, coord_ICS_col][1]
                r[row, col] = image[coord_ICS_row, coord_ICS_col][2]
                a[row, col] = 255

    return b, g, r, a


def create_pnga_optical(b, g, r, a, boundary, gsd, epsg, dst):
    # https://stackoverflow.com/questions/42314272/imwrite-merged-image-writing-image-after-adding-alpha-channel-to-it-opencv-pyt
    png = cv2.merge((b, g, r, a))

    # https://www.programcreek.com/python/example/71303/ ... example 6
    # print('cv2.imwrite')
    # start_time = time.time()
    # https://docs.opencv.org/master/d4/da8/group__imgcodecs.html#gga292d81be8d76901bff7988d18d2b42acad2548321c69ab9c0582fd51e75ace1d0
    cv2.imwrite(dst + '.png', png, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])   # from 0 to 9, default: 3
    # print("--- %s seconds ---" % (time.time() - start_time))

    world = str(gsd) + "\n" + str(0) + "\n" + str(0) + "\n" + str(-gsd) + "\n" + str(boundary[0]) + "\n" + str(boundary[3])
    f = open(dst + '.pgw', 'w')
    f.write(world)
    f.close()


def create_geotiff_optical(b, g, r, a, boundary, gsd, epsg, dst):
    # https://stackoverflow.com/questions/33537599/how-do-i-write-create-a-geotiff-rgb-image-file-in-python
    geotransform = (boundary[0], gsd, 0, boundary[3], 0, -gsd)

    # create the 4-band(RGB+Alpha) raster file
    boundary_cols = int((boundary[1, 0] - boundary[0, 0]) / gsd)
    boundary_rows = int((boundary[3, 0] - boundary[2, 0]) / gsd)
    dst_ds = gdal.GetDriverByName('GTiff').Create(dst + '.tif', boundary_cols, boundary_rows, 4, gdal.GDT_Byte)
    dst_ds.SetGeoTransform(geotransform)  # specify coords

    # Define the projected coordinate system
    srs = osr.SpatialReference()  # establish encoding
    srs.ImportFromEPSG(epsg)

    dst_ds.SetProjection(srs.ExportToWkt())  # export coords to file
    dst_ds.GetRasterBand(1).WriteArray(r)  # write r-band to the raster
    dst_ds.GetRasterBand(2).WriteArray(g)  # write g-band to the raster
    dst_ds.GetRasterBand(3).WriteArray(b)  # write b-band to the raster
    dst_ds.GetRasterBand(4).WriteArray(a)  # write a-band to the raster

    dst_ds.FlushCache()  # write to disk
    dst_ds = None