import os
import numpy as np
import cv2
import time
from ExifData import getExif, restoreOrientation
from EoData import readEO, convertCoordinateSystem, Rot3D
from Boundary import boundary, export_bbox_to_wkt
from BackprojectionResample import projectedCoord, backProjection, resample, createGeoTiff, create_pnga

if __name__ == '__main__':
    ground_height = 32  # unit: m, Yeosu
    sensor_width = 6.3  # unit: mm, Mavic

    dst = './'
    epsg = 3857

    for root, dirs, files in os.walk('../Data'):
        for file in files:
            early_start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.JPG':
                print('Read the image - ' + file)
                image = cv2.imread(file_path, -1)

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
                print("--- %s seconds ---" % (time.time() - early_start_time))

                read_time = end_time - early_start_time

            else:
                print('Read EOP - ' + file)
                print('Easting | Northing | Height | Omega | Phi | Kappa')
                start_time = time.time()
                eo = readEO(file_path)
                eo = convertCoordinateSystem(eo, epsg)
                print(eo)
                R = Rot3D(eo)

                # 4. Extract a projected boundary of the image
                bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)
                print("--- %s seconds ---" % (time.time() - start_time))


                # 5. Compute GSD & Boundary size
                # GSD
                # gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                gsd = 0.1
                print(gsd)
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
                b, g, r, a = resample(backProj_coords, boundary_rows, boundary_cols, image)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 8. Create PNGA
                print('Save the image in PNGA')
                start_time = time.time()
                # createGeoTiff(b, g, r, a, bbox, gsd, boundary_rows, boundary_cols, epsg, dst + filename)
                # print("--- %s seconds ---" % (time.time() - start_time))
                # start_time = time.time()
                create_pnga(b, g, r, a, bbox, gsd, epsg, dst + filename)
                # print("--- %s seconds ---" % (time.time() - start_time))
                # start_time = time.time()
                export_bbox_to_wkt(bbox, dst + filename)
                print("--- %s seconds ---" % (time.time() - start_time))

                print('*** Processing time per each image')
                print("--- %s seconds ---" % (time.time() - early_start_time))
