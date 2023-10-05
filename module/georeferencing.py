import time
import cv2
from .exif import get_metadata
from .exif import restore_orientation
from .eo import geographic2plane
from .eo import rpy_to_opk
from .eo import rot_3d
import numpy as np
from rich.console import Console

import subprocess
import os
import shutil
from .colmap.read_write_model import read_model, write_model, qvec2rotmat, rotmat2qvec
import pandas as pd

console = Console()


def query_points(reconstruction, tracks, target_image):
    """
    Query point cloud by track_id of a target image
    recontruction: path of reconstruction.json
    tracks: path of tracks.csv
    """
    df_reconstruction = pd.read_json(reconstruction)    
    points = df_reconstruction["points"][0]
    print(f" * [Before] no. of points: {len(points)}")

    df_tracks = pd.read_csv(tracks, skiprows=1, sep='\t+', header=None)
    df_tracks.columns = ["image", "track_id", "feature_id", "feature_x", "feature_y", "feature_s", 
                         "r", "g", "b", "segmentation", "instance"]

    # extract track_id
    print(f" * {target_image} is selected")
    tracks_id = df_tracks.loc[df_tracks['image'] == target_image]["track_id"]
    
    # query points
    tmp = []
    for key in tracks_id:
        row = points.get(str(key))
        if row is None:
            continue
        color, coordinates = row["color"], row["coordinates"]
        # id, r, g, b, x, y, z
        tmp.append([key, coordinates[0], coordinates[1], coordinates[2], 
                    color[0], color[1], color[2]])
    new_points = np.array(tmp)

    unwanted = set(points) - set(new_points[:, 0].astype(int).astype(str))
    for unwanted_key in unwanted:
        del points[unwanted_key]
    print(f" * [After] no. of points: {len(points)}")

    df_reconstruction.to_json(reconstruction, orient='records')


def eo_from_opensfm_colmap(path):
    # position
    with open(os.path.join(path, "image_geocoords.tsv"), "r") as f:
        eos = []
        while True:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            elems = line.split("\t")
            if len(elems) > 0 and elems[0] != "Image":                
                image_name = elems[0]
                X, Y, Z = map(float, elems[1:])
                eos.append([image_name, X, Y, Z])
    eos.sort()    
    
    # orientation - rotation matrix
    _, images, _ = read_model(os.path.join(path, "colmap_export"), ext=".txt")
    for img in images.values():
        if img.name == eos[-1][0]:
            R = qvec2rotmat(img.qvec)
            R[:, 1] = -R[:, 1]
            R[:, 2] = -R[:, 2]
            R = R.T   
    
    print(eos[-1][1:], R)

    return eos[-1][1:], R


def direct_georeferencing(image_path, sensor_width, epsg):
    print('Georeferencing - ' + image_path)
    image = cv2.imread(image_path, -1)

    # 1. Extract metadata from a image
    focal_length, orientation, eo, maker = get_metadata(image_path)  # unit: m, _, ndarray

    # 2. Restore the image based on orientation information
    restored_image = restore_orientation(image, orientation)

    image_rows = restored_image.shape[0]
    image_cols = restored_image.shape[1]

    pixel_size = sensor_width / image_cols  # unit: mm/px
    pixel_size = pixel_size / 1000  # unit: m/px

    eo = geographic2plane(eo, epsg)
    opk = rpy_to_opk(eo[3:], maker)
    eo[3:] = opk * np.pi / 180   # degree to radian
    R = rot_3d(eo)

    EO, IO = {}, {}
    EO["eo"] = eo
    EO["rotation_matrix"] = R
    IO["pixel_size"] = pixel_size
    IO["focal_length"] = focal_length

    console.print(
        f"EOP: {eo[0]:.2f} | {eo[1]:.2f} | {eo[2]:.2f} | {eo[3]:.2f} | {eo[4]:.2f} | {eo[5]:.2f}\n"
        f"Focal Length: {focal_length * 1000:.2f} mm, Maker: {maker}",
        style="blink bold red underline")

    return restored_image, EO, IO


def lba_opensfm(images_path, target_image_path, sensor_width, epsg):
    root = '/source/OpenSfM'
    exec = os.path.join(root, 'bin/opensfm')

    image = cv2.imread(target_image_path, -1)

    # from pyproj import CRS
    # crs = CRS.from_epsg(5186)
    # proj = crs.to_proj4()
    proj = '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m +no_defs'

    # 1. extract_metadata
    print(f"\n\n********************\n* extract_metadata *\n********************")
    subprocess.run([exec, 'extract_metadata', images_path])
    # 2. detect_features
    print(f"\n\n*******************\n* detect_features *\n*******************")
    subprocess.run([exec, 'detect_features', images_path])
    # 3. match_features
    print(f"\n\n******************\n* match_features *\n******************")
    subprocess.run([exec, 'match_features', images_path])
    # 4. create_tracks
    print(f"\n\n*****************\n* create_tracks *\n*****************")
    subprocess.run([exec, 'create_tracks', images_path])
    # 5. reconstruct
    print(f"\n\n***************\n* reconstruct *\n***************")
    subprocess.run([exec, 'reconstruct', images_path])
    
    # Query points by track_id in target_image
    query_points(os.path.join(images_path, "reconstruction.json"), 
                os.path.join(images_path, "tracks.csv"), os.path.basename(target_image_path))

    # 6. export_geocoords
    # --transformation: geocoords_transformation.txt
    # --image-positions: image_geocoords.tsv
    # --reconstruction: reconstruction.geocoords.json
    print(f"\n\n********************\n* export_geocoords - EOP *\n********************")
    subprocess.run([exec, 'export_geocoords', '--proj', proj, '--image-positions', images_path])  # position
    subprocess.run([exec, 'export_colmap', images_path])  # orientation    

    print(f"\n\n********************\n* export_geocoords - GP *\n********************")
    subprocess.run([exec, 'export_geocoords', '--proj', proj, '--reconstruction', images_path])
    shutil.move(os.path.join(images_path, 'reconstruction.geocoords.json'), 
                os.path.join(images_path, 'reconstruction.json'))
    print(f"\n\n********************\n* export_ply *\n********************")
    subprocess.run([exec, 'export_ply', '--no-cameras', images_path])

    # 7. TODO: Override exif - exif_overrides.json in images_path
    # example:
    # {
    #     "image_name.jpg": {
    #         "gps": {
    #             "latitude": 52.51891,
    #             "longitude": 13.40029,
    #             "altitude": 27.0,
    #             "dop": 5.0
    #         }
    #     }
    # }
    # should replace data["image_name.jpg"]["gps"]["latitude"] to computed latitude

    focal_length, orientation, _, _ = get_metadata(target_image_path)  # unit: m, _, ndarray
    image_rows, image_cols, _ = image.shape
    pixel_size = sensor_width / image_cols / 1000  # unit: m/px
    
    pos, R = eo_from_opensfm_colmap(images_path)

    EO, IO = {}, {}
    EO["eo"] = pos
    EO["rotation_matrix"] = R
    IO["pixel_size"] = pixel_size
    IO["focal_length"] = focal_length

    return image, EO, IO


if __name__ == "__main__":
    lba_opensfm(images_path='data/yangpyeong', sensor_width=6.3)
    eo_from_opensfm_colmap("data/yangpyeong")