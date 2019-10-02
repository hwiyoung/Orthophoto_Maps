import os
import numpy as np
import cv2
import time
from ExifData import getExif_multiSepctral
from EoData import readEO_multiSpectral, convertCoordinateSystem, Rot3D
from Boundary import boundary
from BackprojectionResample import projectedCoord, backProjection,\
    resampleThermal, createGeoTiffThermal
from system_calibration import calibrate

if __name__ == '__main__':
    ground_height = 0  # unit: m

    R_CB = np.array(
        [[0.992103011532570, -0.0478682839576757, -0.115932057253170],
         [0.0636038625107261, 0.988653550290218, 0.136083452970098],
         [0.108102558627082, -0.142382530141501, 0.983890772356761]], dtype=float)

    for root, dirs, files in os.walk('/home/innopam-ldm/hdd/dbrain/190829_Yeosu_Raw'):
        files.sort()
        for file in files:
            image_start_time = time.time()
            start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.tiff' or extension == '.tif':
                print('Read the image - ' + file)
                image = cv2.imread(file_path, -1)

                # 1. Extract EXIF data from a image
                focal_length, sensor_width = getExif_multiSepctral(file_path)   # unit: m, mm

                image_rows = image.shape[0]
                image_cols = image.shape[1]

                # pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = 0.00375    # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px

                end_time = time.time()
                print("--- %s seconds ---" % (time.time() - start_time))

                read_time = end_time - start_time

                print('Read EOP - ' + file)
                print('Easting | Northing | Altitude | Roll | Pitch | Yaw')
                eo = readEO_multiSpectral(file_path)
                eo = convertCoordinateSystem(eo)
                print(eo)

                # System Calibration
                OPK = calibrate(eo[3], eo[4], eo[5], R_CB)
                eo[3] = OPK[0], eo[4] = OPK[1], eo[5] = OPK[2]
                print('Easting | Northing | Altitude | Omega | Phi | Kappa')
                print(eo)
                R = Rot3D(eo)

                # 4. Extract a projected boundary of the image
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
                dst = './' + filename
                createGeoTiffThermal(gray, bbox, gsd, boundary_rows, boundary_cols, dst)
                print("--- %s seconds ---" % (time.time() - start_time))

                print('*** Processing time per each image')
                print("--- %s seconds ---" % (time.time() - image_start_time + read_time))
