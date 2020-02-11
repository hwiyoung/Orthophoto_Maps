import os
import numpy as np
import cv2
import time
from ExifData import *
from EoData import latlon2tmcentral, Rot3D
from Boundary import boundary, ray_tracing
from BackprojectionResample import projectedCoord, backProjection, resample, createGeoTiff
from copy import copy
import trimesh


def rot_2d(theta):
    # Convert the coordinate system not coordinates
    return np.array([[np.cos(theta), np.sin(theta)],
                     [-np.sin(theta), np.cos(theta)]])


def rpy_to_opk(gimbal_rpy):
    roll_pitch = copy(gimbal_rpy[0:2])
    roll_pitch[0] = 90 + gimbal_rpy[1]
    if gimbal_rpy[0] < 0:
        roll_pitch[1] = 0
    else:
        roll_pitch[1] = gimbal_rpy[0]

    omega_phi = np.dot(rot_2d(gimbal_rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
    kappa = -gimbal_rpy[2]
    return np.array([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa])


if __name__ == '__main__':
    ground_height = 0   # unit: m
    sensor_width = 6.3  # unit: mm
    mode = "average_ground"
    # mode = "dem"
    dem = trimesh.load('./tests/models/DEM_Yangpyeong/DEM_Yangpyeong_drone.obj')

    for root, dirs, files in os.walk('./tests/query_images'):
        for file in files:
            image_start_time = time.time()
            start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file
            dst = './' + filename

            if extension == '.JPG':
                print('Read the image - ' + file)
                image = cv2.imread(file_path, -1)

                # 1. Extract EXIF data from a image
                focal_length, orientation = get_focal_orientation(file_path)  # unit: m, _

                # 2. Restore the image based on orientation information
                restored_image = restoreOrientation(image, orientation)

                image_rows = restored_image.shape[0]
                image_cols = restored_image.shape[1]

                pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px
                print("--- %s seconds ---" % (time.time() - start_time))

                print('Read EOP - ' + file)
                start_time = time.time()
                print('Longitude | Latitude | Altitude | Gimbal-Roll | Gimbal-Pitch | Gimbal-Yaw')
                eo = get_pos_ori(file_path)
                eo = latlon2tmcentral(eo)
                opk = rpy_to_opk(eo[3:])
                eo[3:] = opk * np.pi / 180   # degree to radian
                R = Rot3D(eo)

                if mode == "average_ground":
                    # 3. Extract a projected boundary of the image
                    bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)
                    print("--- %s seconds ---" % (time.time() - start_time))

                    # 4. Compute GSD & Boundary size
                    # GSD
                    gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                    # Boundary size
                    boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                    boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)

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
                elif mode == "dem":
                    ## TODO: Have to deal with the problem from the difference of the number of points
                    # 3. Extract ROI on dem of the image
                    bbox, extracted_dem = ray_tracing(restored_image, eo, R, dem, pixel_size, focal_length)
                    print("--- %s seconds ---" % (time.time() - start_time))

                    # 4. Compute GSD & Boundary size
                    # GSD
                    gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                    # Boundary size
                    boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                    boundary_rows = int((bbox[0, 1] - bbox[2, 1]) / gsd)

                    # Image size
                    image_size = np.reshape(restored_image.shape[0:2], (2, 1))

                    # 6. Back-projection into camera coordinate system
                    print('backProjection')
                    start_time = time.time()
                    backProj_coords = backProjection(extracted_dem, R, focal_length, pixel_size, image_size)
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
