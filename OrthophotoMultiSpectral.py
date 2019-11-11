import os
import numpy as np
import cv2
import time
from ExifData import getMetadataExiv2
from EoData import readEOfromMetadata, convertCoordinateSystem, Rot3D
from Boundary import boundary
from BackprojectionResample import projectedCoord, backProjection,\
    resampleThermal, createGeoTiffThermal
from system_calibration import calibrate
import gdal
import subprocess

if __name__ == '__main__':
    ground_height = 0  # unit: m

    R_CB = np.array(
        [[0.990635238726878, 0.135295782209043, 0.0183541578119133],
         [-0.135993334134149, 0.989711806459606, 0.0444561944563446],
         [-0.0121505910810649, -0.0465359159242159, 0.998842716179817]], dtype=float)

        # [[0.992103011532570, -0.0478682839576757, -0.115932057253170],
        #  [0.0636038625107261, 0.988653550290218, 0.136083452970098],
        #  [0.108102558627082, -0.142382530141501, 0.983890772356761]], dtype=float)

    band = "bgrne"  # blue, green, red, nir, redEdge
    bandList_b_in = []
    bandList_g_in = []
    bandList_r_in = []
    bandList_n_in = []
    bandList_e_in = []
    dstPath = '/internalCompany/PM2019007_nifs/DKC/gomso_stacks_orthophoto/'

    # for root, dirs, files in os.walk('./tests/yeosu_stacks'):
    for root, dirs, files in os.walk('/internalCompany/PM2019007_nifs/DKC/gomso_stacks_test'):
        files.sort()
        for file in files:
            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.tiff' or extension == '.tif':
                print('Read the image - ' + file)
                image_start_time = time.time()
                raster = gdal.Open(file_path, gdal.GA_ReadOnly)

                # 1. Extract EXIF data from the file
                focal_length, sensor_width = getMetadataExiv2(file_path)  # unit: m, mm
                # pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = 0.00375  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px

                # For each band
                for i in range(raster.RasterCount):
                    # 2. Extract an array from each band
                    print('Read the band (' + str(i+1) + ') in ' + file)
                    band_start_time = time.time()
                    start_time = time.time()
                    # https://gis.stackexchange.com/questions/32995/fully-load-raster-into-a-numpy-array
                    image = raster.GetRasterBand(i+1).ReadAsArray()

                    image_rows = image.shape[0]
                    image_cols = image.shape[1]

                    end_time = time.time()
                    print("--- %s seconds ---" % (time.time() - start_time))

                    # 3. Extract EOP from metadata of each band
                    print('Read EOP')
                    start_time = time.time()
                    print('Easting | Northing | Altitude | Roll | Pitch | Yaw')
                    eo = readEOfromMetadata(file_path)
                    # eo = [127.7184603, 34.6057025, 164.289,
                    #       -0.004295216134835715, 0.13159595296597484, -1.757874177995705]   # EO of [img_0073.tif]
                    eo = convertCoordinateSystem(eo)
                    print(eo)

                    # System Calibration
                    OPK = calibrate(eo[3], eo[4], eo[5], R_CB)
                    eo[3] = OPK[0]
                    eo[4] = OPK[1]
                    eo[5] = OPK[2]
                    print('Easting | Northing | Altitude | Omega | Phi | Kappa')
                    print(eo)
                    R = Rot3D(eo)

                    # 4. Extract a projected boundary of the image
                    print('boundary')
                    start_time = time.time()
                    bbox = boundary(image, eo, R, ground_height, pixel_size, focal_length)
                    print("--- %s seconds ---" % (time.time() - start_time))

                    # 5. Compute GSD & Boundary size
                    # GSD
                    gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                    # Boundary size
                    boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                    boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)

                    # 6. Compute coordinates of the projected boundary
                    print('projectedCoord')
                    start_time = time.time()
                    proj_coords = projectedCoord(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height)
                    print("--- %s seconds ---" % (time.time() - start_time))

                    # Image size
                    image_size = np.reshape(image.shape[0:2], (2, 1))

                    # 6. Back-projection into camera coordinate system
                    print('backProjection')
                    start_time = time.time()
                    backProj_coords = backProjection(proj_coords, R, focal_length, pixel_size, image_size)
                    print("--- %s seconds ---" % (time.time() - start_time))

                    # 7. Resample the pixels
                    print('resample')
                    start_time = time.time()
                    gray = resampleThermal(backProj_coords, boundary_rows, boundary_cols, image)
                    print("--- %s seconds ---" % (time.time() - start_time))

                    # 8. Create GeoTiff
                    print('Save the image in GeoTiff')
                    start_time = time.time()
                    dst = dstPath + filename + '_' + band[i]
                    createGeoTiffThermal(gray, bbox, gsd, boundary_rows, boundary_cols, dst)
                    print("--- %s seconds ---" % (time.time() - start_time))

                    if i == 0:
                        bandList_b_in.append(dst + '.tif')
                    elif i == 1:
                        bandList_g_in.append(dst + '.tif')
                    elif i == 2:
                        bandList_r_in.append(dst + '.tif')
                    elif i == 3:
                        bandList_n_in.append(dst + '.tif')
                    else:
                        bandList_e_in.append(dst + '.tif')

                    print('*** Processing time per each image')
                    print("--- %s seconds ---" % (time.time() - band_start_time))

                print(filename + ' is processed!\n')

    # Mosaic individual orthophotos
    working_path1 = './OTB-7.0.0-Linux64/'
    working_path2 = './bin/'
    set_env = './otbenv.profile'
    mosaic_execution = './otbcli_Mosaic'

    # change path
    os.chdir(working_path1)
    # https://stackoverflow.com/questions/13702425/source-command-not-found-in-sh-shell/13702876
    subprocess.call(set_env, shell=True)

    os.chdir(working_path2)
    bandList_b_out = dstPath + '/IMG_b.tif'
    bandList_g_out = dstPath + '/IMG_g.tif'
    bandList_r_out = dstPath + '/IMG_r.tif'
    bandList_n_out = dstPath + '/IMG_n.tif'
    bandList_e_out = dstPath + '/IMG_e.tif'
    subprocess.call(mosaic_execution + ' -il ' + ' '.join(bandList_b_in) +
                    ' -out ' + bandList_b_out, shell=True)
    subprocess.call(mosaic_execution + ' -il ' + ' '.join(bandList_g_in) +
                    ' -out ' + bandList_g_out, shell=True)
    subprocess.call(mosaic_execution + ' -il ' + ' '.join(bandList_r_in) +
                    ' -out ' + bandList_r_out, shell=True)
    subprocess.call(mosaic_execution + ' -il ' + ' '.join(bandList_n_in) +
                    ' -out ' + bandList_n_out, shell=True)
    subprocess.call(mosaic_execution + ' -il ' + ' '.join(bandList_e_in) +
                    ' -out ' + bandList_e_out, shell=True)

