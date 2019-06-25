import os
import numpy as np
import cv2
import time
from ExifData import getExif, restoreOrientation
from EoData import readEO, convertCoordinateSystem, Rot3D
from Boundary import boundary
from BackprojectionResample import projectedCoord, backProjection, resample, createGeoTiff

if __name__ == '__main__':
    ground_height = 65  # unit: m
    sensor_width = 6.3  # unit: mm

    for root, dirs, files in os.walk('./Data'):
        for file in files:
            image_start_time = time.time()
            start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.JPG':
                print('Read the image - ' + file)
                image = cv2.imread(file_path)

                # 1. Extract EXIF data from a image
                focal_length, orientation = getExif(file_path) # unit: m

                # 2. Restore the image based on orientation information
                restored_image = restoreOrientation(image, orientation)

                # 3. Convert pixel values into temperature

                image_rows = restored_image.shape[0]
                image_cols = restored_image.shape[1]

                pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px

                end_time = time.time()
                print("--- %s seconds ---" % (time.time() - start_time))

                read_time = end_time - start_time

            else:
                print('Read EOP - ' + file)
                print('Latitude | Longitude | Height | Omega | Phi | Kappa')
                eo = readEO(file_path)
                eo = convertCoordinateSystem(eo)
                R = Rot3D(eo)

                # 4. Extract a projected boundary of the image
                bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)
                print("--- %s seconds ---" % (time.time() - start_time))

                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px

                # Boundary size
                boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)

                # 5.
                print('projectedCoord')
                start_time = time.time()
                proj_coords = projectedCoord(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height)
                print("--- %s seconds ---" % (time.time() - start_time))

                # Image size
                image_size = np.reshape(restored_image.shape[0:2], (2, 1))

                # 6.
                print('backProjection')
                start_time = time.time()
                backProj_coords = backProjection(proj_coords, R, focal_length, pixel_size, image_size)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 7.
                print('resample')
                start_time = time.time()
                b, g, r, a = resample(backProj_coords, boundary_rows, boundary_cols, image)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 8.
                print('Save the image in GeoTiff')
                start_time = time.time()
                dst = './' + filename
                createGeoTiff(b, g, r, a, bbox, gsd, boundary_rows, boundary_cols, dst)
                print("--- %s seconds ---" % (time.time() - start_time))

                print('*** Processing time per each image')
                print("--- %s seconds ---" % (time.time() - image_start_time + read_time))
