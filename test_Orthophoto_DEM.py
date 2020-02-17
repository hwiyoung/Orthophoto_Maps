import os
import numpy as np
import cv2
import time
from module.ExifData import *
from module.EoData import latlon2tmcentral, Rot3D
from module.Boundary import boundary, ray_tracing
from module.BackprojectionResample import *
from copy import copy
from tabulate import tabulate
import trimesh
from scipy.interpolate import Rbf, griddata, interp2d, RectBivariateSpline


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
    dem = trimesh.load('../DEM_Yangpyeong/dem2point_crop2_15_2 - Cloud.obj')
    dem_gsd = 0.152  # unit: m

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
                eo = get_pos_ori(file_path)
                print(tabulate([['Longitude', eo[0]], ['Latitude', eo[1]], ['Altitude', eo[2]],
                                ['Gimbal-Roll', eo[3]], ['Gimbal-Pitch', eo[4]], ['Gimbal-Yaw', eo[5]]],
                               headers=["Field", "Value(deg)"],
                               tablefmt='orgtbl',
                               numalign="right"))
                eo = latlon2tmcentral(eo)
                opk = rpy_to_opk(eo[3:])
                eo[3:] = opk * np.pi / 180   # degree to radian
                R = Rot3D(eo)

                # 3. Extract ROI on dem of the image
                bbox, extracted_dem = ray_tracing(restored_image, eo, R, dem, pixel_size, focal_length)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 4. Compute GSD & Boundary size
                # GSD
                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                # Boundary size
                boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)

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
                # Boundary size
                # dem_cols = int((bbox[1, 0] - bbox[0, 0]) / dem_gsd)
                # dem_rows = int((bbox[0, 1] - bbox[2, 1]) / dem_gsd)
                dem_cols = 1298
                dem_rows = 1340
                # TODO: Check the dimension of output(b, g, r, a)
                # Resampling for generating source data
                b, g, r, a, backproj_rows, backproj_cols = resample_src(backProj_coords, dem_rows, dem_cols, image)

                # ti_col = np.linspace(start=0, stop=boundary_cols-1, num=boundary_cols)
                # ti_row = np.linspace(start=0, stop=boundary_rows-1, num=boundary_rows)
                # XI, YI = np.meshgrid(ti_col, ti_row)

                # interp_spline = RectBivariateSpline(np.ravel(backproj_rows), np.ravel(backproj_cols), np.ravel(b))
                # Z2 = interp_spline(XI, YI)
                #
                # f = interp2d(backproj_rows, backproj_cols, b, kind='cubic')
                # # use RBF
                # rbf = Rbf(backproj_rows, backproj_cols, b, epsilon=2)
                # ZI = rbf(XI, YI)

                # # Interpolation
                # ti_col = np.linspace(start=0, stop=dem_cols - 1, num=dem_cols)
                # ti_row = np.linspace(start=0, stop=dem_rows - 1, num=dem_rows)
                # XI, YI = np.meshgrid(ti_col, ti_row)
                # points = np.vstack((np.ravel(YI), np.ravel(XI)))
                #
                # grid_x, grid_y = np.mgrid[0:1:(boundary_rows * 1j), 0:1:(boundary_cols * 1j)]
                # grid_b = griddata(points.T, np.ravel(b), (grid_x, grid_y), method='cubic')
                # grid_g = griddata(points.T, np.ravel(g), (grid_x, grid_y), method='cubic')
                # grid_r = griddata(points.T, np.ravel(r), (grid_x, grid_y), method='cubic')
                # grid_a = griddata(points.T, np.ravel(a), (grid_x, grid_y), method='cubic')
                print("--- %s seconds ---" % (time.time() - start_time))

                # 8. Create GeoTiff
                print('Save the image in GeoTiff')
                start_time = time.time()
                createGeoTiff(b, g, r, a, bbox, dem_gsd, dem_rows, dem_cols, dst)
                # createGeoTiff(grid_b, grid_g, grid_r, grid_a, bbox, gsd, boundary_rows, boundary_cols, dst)
                print("--- %s seconds ---" % (time.time() - start_time))

                print('*** Processing time per each image')
                print("--- %s seconds ---" % (time.time() - image_start_time))
