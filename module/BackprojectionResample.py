import numpy as np
from numba import jit
from osgeo import gdal, osr

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

def backProjection(coord, R, focal_length, pixel_size, image_size):
    coord_CCS_m = np.dot(R, coord)  # unit: m     3 x (row x col)
    scale = (coord_CCS_m[2]) / (-focal_length)  # 1 x (row x col)
    plane_coord_CCS = coord_CCS_m[0:2] / scale  # 2 x (row x col)

    # Convert CCS to Pixel Coordinate System
    coord_CCS_px = plane_coord_CCS / pixel_size  # unit: px
    coord_CCS_px[1] = -coord_CCS_px[1]

    coord_out = image_size[::-1] / 2 + coord_CCS_px  # 2 x (row x col)

    return coord_out

@jit(nopython=True)
def resample(coord, boundary_rows, boundary_cols, image):
    # Define channels of an orthophoto
    b = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    g = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    r = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    a = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)

    rows = np.reshape(coord[1], (boundary_rows, boundary_cols))
    cols = np.reshape(coord[0], (boundary_rows, boundary_cols))

    rows = rows.astype(np.int16)
    #rows = np.int16(rows)
    cols = cols.astype(np.int16)

    for row in range(boundary_rows):
        for col in range(boundary_cols):
            if cols[row, col] < 0 or cols[row, col] >= image.shape[1]:
                continue
            elif rows[row, col] < 0 or rows[row, col] >= image.shape[0]:
                continue
            else:
                b[row, col] = image[rows[row, col], cols[row, col]][0]
                g[row, col] = image[rows[row, col], cols[row, col]][1]
                r[row, col] = image[rows[row, col], cols[row, col]][2]
                a[row, col] = 255

    return b, g, r, a

def createGeoTiff(b, g, r, a, boundary, gsd, rows, cols, dst):
    # https://stackoverflow.com/questions/33537599/how-do-i-write-create-a-geotiff-rgb-image-file-in-python
    geotransform = (boundary[0], gsd, 0, boundary[3], 0, -gsd)

    # create the 4-band(RGB+Alpha) raster file
    dst_ds = gdal.GetDriverByName('GTiff').Create(dst + '.tif', cols, rows, 4, gdal.GDT_Byte)
    dst_ds.SetGeoTransform(geotransform)  # specify coords

    # Define the TM central coordinate system (EPSG 5186)
    srs = osr.SpatialReference()  # establish encoding
    srs.ImportFromEPSG(5186)

    dst_ds.SetProjection(srs.ExportToWkt())  # export coords to file
    dst_ds.GetRasterBand(1).WriteArray(r)  # write r-band to the raster
    dst_ds.GetRasterBand(2).WriteArray(g)  # write g-band to the raster
    dst_ds.GetRasterBand(3).WriteArray(b)  # write b-band to the raster
    dst_ds.GetRasterBand(4).WriteArray(a)  # write a-band to the raster

    dst_ds.FlushCache()  # write to disk
    dst_ds = None

@jit(nopython=True)
def resampleThermal(coord, boundary_rows, boundary_cols, image):
    # Define channels of an orthophoto
    gray = np.zeros(shape=(boundary_rows, boundary_cols))

    rows = np.reshape(coord[1], (boundary_rows, boundary_cols))
    cols = np.reshape(coord[0], (boundary_rows, boundary_cols))

    rows = rows.astype(np.int16)
    cols = cols.astype(np.int16)

    for row in range(boundary_rows):
        for col in range(boundary_cols):
            if cols[row, col] < 0 or cols[row, col] >= image.shape[1]:
                continue
            elif rows[row, col] < 0 or rows[row, col] >= image.shape[0]:
                continue
            else:
                gray[row, col] = image[rows[row, col], cols[row, col]]

    return gray

def createGeoTiffThermal(grey, boundary, gsd, rows, cols, dst):
    # https://stackoverflow.com/questions/33537599/how-do-i-write-create-a-geotiff-rgb-image-file-in-python
    geotransform = (boundary[0], gsd, 0, boundary[3], 0, -gsd)

    # create the 4-band(RGB+Alpha) raster file
    dst_ds = gdal.GetDriverByName('GTiff').Create(dst + '.tif', cols, rows, 1, gdal.GDT_Float32)
    dst_ds.SetGeoTransform(geotransform)  # specify coords

    # Define the TM central coordinate system (EPSG 5186)
    srs = osr.SpatialReference()  # establish encoding
    srs.ImportFromEPSG(5186)

    dst_ds.SetProjection(srs.ExportToWkt())  # export coords to file
    dst_ds.GetRasterBand(1).WriteArray(grey)  # write gray-band to the raster
    # https://gis.stackexchange.com/questions/220753/how-do-i-create-blank-geotiff-
    # with-same-spatial-properties-as-existing-geotiff
    dst_ds.GetRasterBand(1).SetNoDataValue(0)

    dst_ds.FlushCache()  # write to disk
    dst_ds = None

@jit(nopython=True)
def projectedCoord_test(boundary, boundary_rows, boundary_cols, gsd, eo, dem):
    proj_coords = np.empty(shape=(3, boundary_rows * boundary_cols))
    i = 0
    # idx_z0 = 0
    # res = np.empty(shape=(2, 1739320))
    for row in range(boundary_rows):
        # print(row)
        # idx_z0 = row * boundary_rows
        for col in range(boundary_cols):
            proj_coords[0, i] = boundary[0, 0] + col * gsd - eo[0]
            proj_coords[1, i] = boundary[3, 0] - row * gsd - eo[1]
            idx_z = np.argmin(np.sqrt(np.sum((dem[0:2, :].T - proj_coords[0:2, i]) ** 2, axis=1)))
            proj_coords[2, i] = dem[:, idx_z][2]
            i += 1
    return proj_coords
