import os
import numpy as np
import cv2
import time
from module.ExifData import *
from module.EoData import *
from module.Boundary import boundary, ray_tracing
from module.BackprojectionResample import *
from tabulate import tabulate
import platform


if __name__ == '__main__':
    ground_height = 0   # unit: m
    sensor_width = 6.3  # unit: mm
    os_name = platform.system()

    for root, dirs, files in os.walk('./tests/query_images'):
        for file in files:
            image_start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file
            dst = './' + filename

            if extension == '.JPG':
                print('Read the image - ' + file)
                start_time = time.time()
                image = cv2.imread(file_path, -1)

                # 1. Extract metadata from a image
                focal_length, orientation, eo = get_metadata(file_path, os_name)  # unit: m, _, ndarray
                print(tabulate([['Longitude', eo[0]], ['Latitude', eo[1]], ['Altitude', eo[2]],
                                ['Gimbal-Roll', eo[3]], ['Gimbal-Pitch', eo[4]], ['Gimbal-Yaw', eo[5]]],
                               headers=["Field", "Value(deg)"],
                               tablefmt='orgtbl',
                               numalign="right"))

                # 2. Restore the image based on orientation information
                restored_image = restoreOrientation(image, orientation)

                image_rows = restored_image.shape[0]
                image_cols = restored_image.shape[1]

                pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px
                print("--- %s seconds ---" % (time.time() - start_time))

                print('Construct EOP')
                start_time = time.time()
                eo = latlon2tmcentral(eo)
                opk = rpy_to_opk(eo[3:])
                eo[3:] = opk * np.pi / 180   # degree to radian
                R = Rot3D(eo)
                print("--- %s seconds ---" % (time.time() - start_time))

                print('boundary & GSD')
                start_time = time.time()
                # 3. Extract a projected boundary of the image
                bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)

                # 4. Compute GSD & Boundary size
                # GSD
                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                # Boundary size
                boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 5. Compute coordinates of the projected boundary(Generate a virtual DEM)
                print('projectedCoord')
                start_time = time.time()
                proj_coords = projectedCoord(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height)
                print("--- %s seconds ---" % (time.time() - start_time))

                # Image size
                image_size = np.reshape(restored_image.shape[0:2], (2, 1))

                # 6. Back-projection into camera coordinate system
                print('backProjection')
                start_time = time.time()
                backProj_coords = backProjection(proj_coords, R, focal_length, pixel_size, image_size)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 7. Resample the pixels
                print('resample')
                start_time = time.time()
                b, g, r, a = resample(backProj_coords, boundary_rows, boundary_cols, image)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 8. Create GeoTiff
                print('Save the image in GeoTiff')
                start_time = time.time()
                createGeoTiff(b, g, r, a, bbox, gsd, boundary_rows, boundary_cols, dst)
                print("--- %s seconds ---" % (time.time() - start_time))

                print('*** Processing time per each image')
                print("--- %s seconds ---" % (time.time() - image_start_time))
