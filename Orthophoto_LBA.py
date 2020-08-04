import time
from module.ExifData import *
from module.EoData import *
from module.Boundary import boundary
from module.BackprojectionResample import *
from tabulate import tabulate
from module.LocalBA import *
import glob
from copy import copy
from collections import deque


if __name__ == '__main__':
    ground_height = 0   # unit: m
    # sensor_width = 6.3  # unit: mm, Mavic
    # sensor_width = 13.2  # unit: mm, P4RTK
    sensor_width = 17.3  # unit: mm, Inspire
    epsg = 5186     # editable
    # ref_eo = []
    # https://stackoverflow.com/questions/1931589/python-datatype-for-a-fixed-length-fifo
    ref_eo = deque([], 5)

    image_path = '../00_data/sample_dji'
    images = glob.glob(image_path + "/*.JPG")
    images.sort()
    first_start_time = time.time()
    for i in range(len(images)):
        each_start_time = time.time()
        image_name = images[i].split("\\")[1].split(".")[0]
        dst = './' + image_name

        image = cv2.imread(images[i], -1)
        read_time = time.time() - each_start_time

        print("=================================================================="
              "================================================================")
        metadata_start = time.time()
        # 1. Extract metadata from a image
        focal_length, orientation, eo, maker = get_metadata(images[i])  # unit: m, _, ndarray

        # 2. Restore the image based on orientation information
        restored_image = restoreOrientation(image, orientation)

        image_rows = restored_image.shape[0]
        image_cols = restored_image.shape[1]

        pixel_size = sensor_width / image_cols  # unit: mm/px
        pixel_size = pixel_size / 1000  # unit: m/px
        metadata_time = time.time() - metadata_start

        georef_start = time.time()
        if i < 4:
            ref_eo.append(copy(eo))
            eo = geographic2plane(eo, epsg)
            opk = rpy_to_opk(eo[3:], maker)
            print(tabulate([[image_name, eo[0], eo[1], eo[2], opk[0], opk[1], opk[2]]],
                           headers=["Name", "X(m)", "Y(m)", "Z(m)", "Omega(deg)", "Phi(deg)", "Kappa(deg)"],
                           tablefmt='psql', floatfmt=".4f"))
            eo[3:] = opk * np.pi / 180  # degree to radian
            R = Rot3D(eo)
            georef_time = time.time() - georef_start
        elif i == 4:
            ref_eo.append(copy(eo))
            images_to_process = images[i-4:i+1]   # not include last number
            eo, opk = solve_local_AT2(images_to_process, "photoscan", np.array(ref_eo).astype(str), i)
            ref_eo.append(copy(eo[4]))
            ref_eo.append(copy(eo[3]))
            ref_eo.append(copy(eo[2]))
            ref_eo.append(copy(eo[1]))
            ref_eo.append(copy(eo[0]))
            eo = geographic2plane(eo[0], epsg)
            print(tabulate([[image_name, eo[0], eo[1], eo[2], opk[0], opk[1], opk[2]]],
                           headers=["Name", "X(m)", "Y(m)", "Z(m)", "Omega(deg)", "Phi(deg)", "Kappa(deg)"],
                           tablefmt='psql', floatfmt=".4f"))
            eo[3:] = opk * np.pi / 180  # degree to radian
            R = Rot3D(eo)
            georef_time = time.time() - georef_start
        else:
            eo[4] = eo[4] + 90
            ref_eo.append(copy(eo))
            images_to_process = images[i-4:i+1]   # not include last number
            # eo = solve_local_AT(images_to_process, "photoscan")
            eo, opk = solve_local_AT3(images_to_process, "photoscan", np.array(ref_eo).astype(str), i)
            ref_eo[-1] = copy(eo)
            eo = geographic2plane(eo, epsg)
            print(tabulate([[image_name, eo[0], eo[1], eo[2], opk[0], opk[1], opk[2]]],
                           headers=["Name", "X(m)", "Y(m)", "Z(m)", "Omega(deg)", "Phi(deg)", "Kappa(deg)"],
                           tablefmt='psql', floatfmt=".4f"))
            eo[3:] = opk * np.pi / 180  # degree to radian
            R = Rot3D(eo)
            georef_time = time.time() - georef_start

        boundary_start = time.time()
        # 3. Extract a projected boundary of the image
        bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)

        # 4. Compute GSD & Boundary size
        # GSD
        gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
        # Boundary size
        boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
        boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)
        boundary_time = time.time() - boundary_start

        projection_start = time.time()
        # 5. Compute coordinates of the projected boundary(Generate a virtual DEM)
        proj_coords = projectedCoord(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height)

        # Image size
        image_size = np.reshape(restored_image.shape[0:2], (2, 1))
        projection_time = time.time() - projection_start

        backproj_start = time.time()
        # 6. Back-projection into camera coordinate system
        backProj_coords = backProjection(proj_coords, R, focal_length, pixel_size, image_size)
        backproj_time = time.time() - backproj_start

        resample_start = time.time()
        # 7. Resample the pixels
        b, g, r, a = resample(backProj_coords, boundary_rows, boundary_cols, image)
        resample_time = time.time() - resample_start

        save_start = time.time()
        # 8. Create GeoTiff
        createGeoTiff(b, g, r, a, bbox, gsd, boundary_rows, boundary_cols, dst)
        # create_pnga_optical(b, g, r, a, bbox, gsd, epsg, dst)   # for test
        save_time = time.time() - save_start
        total_time = time.time() - each_start_time

        print(tabulate([[read_time, metadata_time, georef_time, boundary_time, projection_time,
                         backproj_time, resample_time, save_time, total_time]],
                       headers=["Read", "Metadata", "Georeferencing", "Boundary", "Projection",
                                "Back-proj.", "Resample", "Save", "Total"],
                       tablefmt='psql', floatfmt=".4f"))
