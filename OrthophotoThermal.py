import os
import numpy as np
import cv2
import os
import numpy as np
import cv2
import time
from module.ExifData import *
from module.EoData import *
from module.Boundary import boundary, ray_tracing
from module.BackprojectionResample import *
from tabulate import tabulate

if __name__ == '__main__':
    ground_height = 65  # unit: m
    sensor_width = 10.88  # unit: mm
    epsg = 5186  # editable

    for root, dirs, files in os.walk('./tests/thermal_images'):
        files.sort()
        for file in files:
            image_start_time = time.time()
            start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.tiff' or extension == '.tif' or extension == ".TIFF":
                print('Read the image - ' + file)
                image = cv2.imread(file_path, -1)

                focal_length = 9 / 1000   # unit : mm -> m

                # # 1. Extract EXIF data from a image
                # focal_length, orientation = getExif(file_path) # unit: m
                #
                # # 2. Restore the image based on orientation information
                # restored_image = restoreOrientation(image, 3)
                restored_image = image

                # 3. Convert pixel values into temperature
                converted_image = restored_image * 0.04 - 273.15
                # converted_image = restored_image

                image_rows = restored_image.shape[0]
                image_cols = restored_image.shape[1]

                pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px

                end_time = time.time()
                print("--- %s seconds ---" % (time.time() - start_time))

                read_time = end_time - start_time

            else:
                print('Read EOP - ' + file)
                eo = readEO(file_path)
                print(tabulate([[eo[0], eo[1], eo[2], eo[3], eo[4], eo[5]]],
                               headers=["Longitude(deg)", "Latitude(deg)", "Altitude(deg)",
                                        "Roll(deg)", "Pitch(deg)", "Yaw(deg)"],
                               tablefmt='psql'))
                eo = geographic2plane(eo, epsg)
                R = Rot3D(eo)

                # 4. Extract a projected boundary of the image
                bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)
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
                image_size = np.reshape(restored_image.shape[0:2], (2, 1))

                # 6. Back-projection into camera coordinate system
                print('backProjection')
                start_time = time.time()
                backProj_coords = backProjection(proj_coords, R, focal_length, pixel_size, image_size)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 7. Resample the pixels
                print('resample')
                start_time = time.time()
                gray, a = resampleThermal(backProj_coords, boundary_rows, boundary_cols, converted_image)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 8. Create GeoTiff
                print('Save the image in GeoTiff')
                start_time = time.time()
                dst = './' + filename
                createGeoTiffThermal(gray, bbox, gsd, boundary_rows, boundary_cols, dst)
                print("--- %s seconds ---" % (time.time() - start_time))

                # # 8. Create pnga
                # print('Save the image in pnga')
                # start_time = time.time()
                # dst = './' + filename
                # create_pnga_thermal(gray, a, bbox, gsd, epsg, dst)
                # print("--- %s seconds ---" % (time.time() - start_time))

                print('*** Processing time per each image')
                print("--- %s seconds ---" % (time.time() - image_start_time + read_time))
