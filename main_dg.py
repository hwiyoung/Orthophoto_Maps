import os
import time
import numpy as np
#from module.ExifData import *
from module.ExifData import get_exif, restoreOrientation
from module.EoData import rpy_to_opk, Rot3D
from module.Boundary import boundary
from module.BackprojectionResample import rectify_plane_parallel, createGeoTiff
from pyproj import Transformer
from rich.table import Table
from rich.console import Console
import cv2

console = Console()

INPUT_FOLDER = 'Data'
GROUND_HEIGHT = 0   # unit: m
gsd = 0.1   # unit: m
AUTO_GSD = True  # True to compute automatically gsd per image


# Modify next line with local epsg of your data
# Find your local EPSG (https://epsg.io/)
EPSG_OUT = 5186  # Korea 2000 / Central Belt 2010

# Most of the time data location is GPS based with WGS-84
ESPSG_IN = 4326  # WGS-84 [dd.mm.sssd]

if __name__ == '__main__':
    for root, dirs, files in os.walk(INPUT_FOLDER):
        files.sort()
        for file in files:
            image_start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file
            dst = './' + filename

            if extension in ['.JPG', '.jpg']  :
                print('Georeferencing - ' + file)
                start_time = time.time()
                image = cv2.imread(file_path, -1)

                # 1. Extract metadata from a image
                Camera = get_exif(file_path)
                print(f"[Camera['Roll'] {Camera['Roll']} Camera['Pitch'] {Camera['Pitch']} Camera['Yaw'] {Camera['Yaw']}")

                # 2. Restore the image based on orientation information
                restored_image = restoreOrientation(image, Camera['Orientation'])
                image_rows, image_cols, _ = restored_image.shape

                pixel_size = Camera['Size'][0] / image_cols  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px

                # Get Local coordinates
                coordonates_transformer = Transformer.from_crs(f'epsg:{ESPSG_IN}', f'epsg:{EPSG_OUT}')

                Camera['X'], Camera['Y'] = coordonates_transformer.transform(Camera['Lat'], Camera['Lon'], errcheck=True)
                # OPK from RPY
                Camera['Omega'], Camera['Phi'], Camera['Kappa'] = rpy_to_opk(Camera)

                # already converted to math.radians in rpy_to_opk
                # eo[3:] = opk * np.pi / 180   # degree to radian
                eo = np.array([Camera['X'], Camera['Y'], Camera['RelAltitude'],
                              Camera['Omega'], Camera['Phi'], Camera['Kappa']])

                R = Rot3D(eo)

                console.print(
                    f"EOP: Longitude {eo[0]:.2f} | Latitude {eo[1]:.2f} | Altitude {eo[2]:.2f} | Omega {eo[3]:.2f} | Phi {eo[4]:.2f} | Kappa {eo[5]:.2f}\n"
                    f"Focal Length: {Camera['Focalength'] * 1000:.2f} mm",
                    style="blink bold red underline")
                georef_time = time.time() - start_time
                console.print(
                    f"Georeferencing time: {georef_time:.2f} sec", style="blink bold red underline")

                print('DEM & GSD')
                start_time = time.time()
                # 3. Extract a projected boundary of the image
                GROUND_HEIGHT = Camera['AbsAltitude']
                bbox = boundary(restored_image, eo, R, GROUND_HEIGHT,
                                pixel_size, Camera['Focalength'])

                # 4. Compute GSD & Boundary size
                # GSD
                if AUTO_GSD:
                    gsd = (pixel_size * (Camera['RelAltitude'] - Camera['AbsAltitude'] )) / Camera['Focalength']  # unit: m/px

                # Boundary size
                boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)

                console.print(f"GSD: {gsd * 100:.2f} cm/px",style="blink bold red underline")
                dem_time = time.time() - start_time
                console.print(f"DEM time: {dem_time:.2f} sec", style="blink bold red underline")

                print('Rectify & Resampling')
                start_time = time.time()
                b, g, r, a = rectify_plane_parallel(bbox, boundary_rows, boundary_cols, gsd, eo, GROUND_HEIGHT,
                                                    R, Camera['Focalength'], pixel_size, image)
                rectify_time = time.time() - start_time
                console.print(f"Rectify time: {rectify_time:.2f} sec", style="blink bold red underline")

                # 8. Create GeoTiff
                print('Save the image in GeoTiff')
                start_time = time.time()
                createGeoTiff(b, g, r, a, bbox, gsd, EPSG_OUT,
                              boundary_rows, boundary_cols, dst)
                # create_pnga_optical(b, g, r, a, bbox, gsd, epsg, dst)   # for test
                write_time = time.time() - start_time
                console.print(
                    f"Write time: {write_time:.2f} sec", style="blink bold red underline")

                processing_time = time.time() - image_start_time
                console.print(
                    f"Process time: {processing_time:.2f} sec", style="blink bold red underline")

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Image", style="dim")
                table.add_column("Georeferencing", justify="right")
                table.add_column("DEM", justify="right")
                table.add_column("Rectify", justify="right")
                table.add_column("Write", justify="right")
                table.add_column("Processing", justify="right")
                table.add_row(
                    filename, str(round(georef_time, 5)), str(
                        round(dem_time, 5)), str(round(rectify_time, 5)),
                    str(round(write_time, 5)), str(round(processing_time, 5))
                )
                console.print(table)
