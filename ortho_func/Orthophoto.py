import numpy as np
import time
from .EoData import Rot3D
from .Boundary import boundary, export_bbox_to_wkt2
from .BackprojectionResample import projectedCoord, backProjection, resample, create_pnga

def rectify(data_store, project_path, img, rectified_fname, eo, ground_height, sensor_width, focal_length, gsd='auto'):
    """
    In order to generate an individual orthophoto, this function rectifies a given drone image on a reference plane.
    :param data_store       :
    :param project_path     : A path for saving orthophotos(e.g.: './')
    :param img              : Input image in numpy array
    :param rectified_fname  : A name of the orthophoto(e.g. Rectified_1)
    :param eo               : eo in numpy array
    :param ground_height    : Ground height in m
    :param sensor_width     : Width of the sensor in mm
    :param focal_length     : Focal length in mm
    :param gsd              : GSD in m. If not specified, it will automatically determine gsd.
    :return File name of a rectified image(.png), boundary polygon in WKT(.txt)
    """

    ealry_strat_time = time.time()
    rectified_full_fname = data_store + project_path + rectified_fname
    epsg = 3857

    image_rows = img.shape[0]
    image_cols = img.shape[1]

    pixel_size = sensor_width / image_cols  # unit: mm/px
    pixel_size = pixel_size / 1000  # unit: m/px

    focal_length = focal_length / 1000  # unit: m

    # 2. Extract a projected boundary of the image
    R = Rot3D(eo)
    bbox = boundary(img, eo, R, ground_height, pixel_size, focal_length)
    # GSD
    gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
    gsd = 0.15
    # Boundary size
    boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
    boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)
    # print("--- %s seconds ---" % (time.time() - ealry_strat_time))

    # 3. Compute coordinates of the projected boundary
    # print('projectedCoord')
    # start_time = time.time()
    proj_coords = projectedCoord(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height)
    # print("--- %s seconds ---" % (time.time() - start_time))

    # 6. Back-projection into camera coordinate system
    # print('backProjection')
    # start_time = time.time()
    # Image size
    image_size = np.reshape(img.shape[0:2], (2, 1))
    backProj_coords = backProjection(proj_coords, R, focal_length, pixel_size, image_size)
    # print("--- %s seconds ---" % (time.time() - start_time))

    # 7. Resample the pixels
    # print('resample')
    # start_time = time.time()
    b, g, r, a = resample(backProj_coords, boundary_rows, boundary_cols, img)
    # print("--- %s seconds ---" % (time.time() - start_time))

    # 8. Create PNGA
    # print('Save the image in PNGA')
    # start_time = time.time()
    create_pnga(b, g, r, a, bbox, gsd, epsg, rectified_full_fname)
    bbox_wkt = export_bbox_to_wkt2(bbox, rectified_full_fname)
    # print("--- %s seconds ---" % (time.time() - start_time))

    print('*** Processing time per each image')
    print("--- %s seconds ---" % (time.time() - ealry_strat_time))

    return project_path + rectified_fname + '.png', bbox_wkt
