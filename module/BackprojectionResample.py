import numpy as np
from numba import jit
from osgeo import gdal, osr
import cv2

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

def create_pnga_optical(b, g, r, a, boundary, gsd, epsg, dst):
    ## TODO: An option for generating an world file
    # https://stackoverflow.com/questions/42314272/imwrite-merged-image-writing-image-after-adding-alpha-channel-to-it-opencv-pyt
    # print('cv2.merge')
    # start_time = time.time()
    png = cv2.merge((b, g, r, a))
    # print("--- %s seconds ---" % (time.time() - start_time))

    # https://www.programcreek.com/python/example/71303/ ... example 6
    # print('cv2.imwrite')
    # start_time = time.time()
    # https://docs.opencv.org/master/d4/da8/group__imgcodecs.html#gga292d81be8d76901bff7988d18d2b42acad2548321c69ab9c0582fd51e75ace1d0
    cv2.imwrite(dst + '.png', png, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])   # from 0 to 9, default: 3
    # print("--- %s seconds ---" % (time.time() - start_time))

    ## TODO: A function for generating an world file based on epsg
    # xml = '<PAMDataset> ' \
    #       '<SRS dataAxisToSRSAxisMapping="1,2">PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs"],AUTHORITY["EPSG","3857"]]</SRS> ' \
    #       '<GeoTransform>  ' + str(boundary[0, 0]) + ',  ' + str(gsd) + ',  0.0000000000000000e+00,  ' + str(boundary[3, 0]) + ',  0.0000000000000000e+00, ' + str(-gsd) + '</GeoTransform> ' \
    #       '<Metadata domain="IMAGE_STRUCTURE"> ' \
    #       '<MDI key="INTERLEAVE">PIXEL</MDI> ' \
    #       '</Metadata> ' \
    #       '<Metadata> ' \
    #       '<MDI key="AREA_OR_POINT">Area</MDI> ' \
    #       '</Metadata> ' \
    #       '</PAMDataset>'
    #
    # f = open(dst + '.png.aux.xml', 'w')
    # f.write(xml)
    # f.close()

@jit(nopython=True)
def resampleThermal(coord, boundary_rows, boundary_cols, image):
    # Define channels of an orthophoto
    gray = np.zeros(shape=(boundary_rows, boundary_cols))
    a = np.zeros(shape=(boundary_rows, boundary_cols))

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
                a[row, col] = 255

    return gray, a

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

def create_pnga_thermal(gray, a, boundary, gsd, epsg, dst):
    # https://stackoverflow.com/questions/42314272/imwrite-merged-image-writing-image-after-adding-alpha-channel-to-it-opencv-pyt
    # png = cv2.merge((gray, a))  #cv2.error: OpenCV(4.1.2) /io/opencv/modules/imgcodecs/src/loadsave.cpp:668: error: (-215:Assertion failed) image.channels() == 1 || image.channels() == 3 || image.channels() == 4 in function 'imwrite_'
    png = gray

    # https://www.programcreek.com/python/example/71303/ ... example 6
    # https://docs.opencv.org/master/d4/da8/group__imgcodecs.html#gga292d81be8d76901bff7988d18d2b42acad2548321c69ab9c0582fd51e75ace1d0
    cv2.imwrite(dst + '.png', png, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])   # from 0 to 9, default: 3

    # xml = '<PAMDataset> ' \
    #       '<SRS dataAxisToSRSAxisMapping="1,2">PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs"],AUTHORITY["EPSG","3857"]]</SRS> ' \
    #       '<GeoTransform>  ' + str(boundary[0, 0]) + ',  ' + str(gsd) + ',  0.0000000000000000e+00,  ' + str(boundary[3, 0]) + ',  0.0000000000000000e+00, ' + str(-gsd) + '</GeoTransform> ' \
    #       '<Metadata domain="IMAGE_STRUCTURE"> ' \
    #       '<MDI key="INTERLEAVE">PIXEL</MDI> ' \
    #       '</Metadata> ' \
    #       '<Metadata> ' \
    #       '<MDI key="AREA_OR_POINT">Area</MDI> ' \
    #       '</Metadata> ' \
    #       '</PAMDataset>'
    #
    # f = open(dst + '.png.aux.xml', 'w')
    # f.write(xml)
    # f.close()
