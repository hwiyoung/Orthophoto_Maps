from module.georeferencing import direct_georeferencing
from module.georeferencing import lba_opensfm
from module.dem import boundary
from module.dem import generate_dem_pdal
from module.rectification import rectify_plane_parallel
from module.rectification import rectify_dem_parallel
from module.rectification import create_pnga_optical

import argparse
import os
import time
import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()

sensor_width = 6.3  # unit: mm, Mavic
# sensor_width = 13.2  # unit: mm, P4RTK
# sensor_width = 17.3  # unit: mm, Inspire

def orthophoto_direct(args, image_path):
    # 1. Georeferencing
    # 1-1. Direct
    georef_start = time.time()
    image, EO, IO = direct_georeferencing(image_path=image_path, 
                                          sensor_width=sensor_width,
                                          epsg=args.epsg_out)
    georef_time = time.time() - georef_start
    console.print(f"Georeferencing time: {georef_time:.2f} sec", style="blink bold red underline")

    # 2. Generate DEM
    ### 2. Extract boundary
    dem_start = time.time()
    #TODO: Compute the GSD
    bbox = boundary(image, IO, EO, args.ground_height)
    dem_time = time.time() - dem_start
    console.print(f"DEM time: {dem_time:.2f} sec", style="blink bold red underline")

    # 3. Rectify
    ### 3. Geodata generation
    rectify_start = time.time()
    pixel_size, focal_length = IO["pixel_size"], IO["focal_length"]
    pos, rotation_matrix = EO["eo"], EO["rotation_matrix"]
    b, g, r, a = rectify_plane_parallel(image, pixel_size, focal_length, pos, rotation_matrix, 
                                        args.ground_height, bbox, args.gsd)
    bbox = bbox.ravel()  # for generating orthophoto
    rectify_time = time.time() - rectify_start
    console.print(f"Rectify time: {rectify_time:.2f} sec", style="blink bold red underline")

    times = np.array([georef_time, dem_time, rectify_time])

    return b, g, r, a, bbox


def orthophoto_lba(args, image_path):
    # 1. Georeferencing
    # 1-2. Indirect - Local Bundle Adjustment
    georef_start = time.time()
    image, EO, IO = lba_opensfm(images_path=args.input_project, target_image_path=image_path,
                                sensor_width=sensor_width, epsg=args.epsg_out)
    georef_time = time.time() - georef_start
    console.print(f"Georeferencing time: {georef_time:.2f} sec", style="blink bold red underline")

    # 2. Generate DEM
    ### 2. DEM processing
    dem_start = time.time()
    #TODO: Compute the GSD
    dem_x, dem_y, dem_z, bbox = generate_dem_pdal(os.path.join(args.input_project, "reconstruction.ply"), args.dem, args.gsd)
    dem_time = time.time() - dem_start
    console.print(f"DEM time: {dem_time:.2f} sec", style="blink bold red underline")

    # 3. Rectify
    rectify_start = time.time()
    # b, g, r, a = rectify_dem_parallel(dem_x, dem_y, dem_z, boundary_rows, boundary_cols,
    #                                   eo, R, focal_length, pixel_size, image)
    pixel_size, focal_length = IO["pixel_size"], IO["focal_length"]
    pos, rotation_matrix = EO["eo"], EO["rotation_matrix"]
    b, g, r, a = rectify_dem_parallel(image, pixel_size, focal_length, pos, rotation_matrix, 
                                      dem_x, dem_y, dem_z)
    rectify_time = time.time() - rectify_start
    console.print(f"Rectify time: {rectify_time:.2f} sec", style="blink bold red underline")

    times = np.array([georef_time, dem_time, rectify_time])

    return b, g, r, a, bbox


def main():
    parser = argparse.ArgumentParser(description="Run Orthophoto_Maps")
    parser.add_argument("--input_project", help="path to the input project folder", 
                        default="data/yangpyeong")
    parser.add_argument("--metadata_in_image", help="images have metadata?", default=True)    
    parser.add_argument("--output_path", help="path to output folder", default="output/")
    parser.add_argument("--no_image_process", help="the number of images to process at once", 
                        default=5)
    parser.add_argument("--sys_cal", choices=["DJI", "samsung"],
                        help="types of a system calibration", default="DJI")

    parser.add_argument("--epsg_out", help="EPSG of output data", default=5186)
    parser.add_argument("--gsd", help="target ground sampling distance in m. set to 0 to disable", 
                        default=0.1)
    parser.add_argument("--dem", choices=["dsm", "dtm", "plane"],
                        help="types of projection plane", default="plane")
    parser.add_argument("--ground_height", 
                        help="target ground height in m", default=0)
    args = parser.parse_args()

    images = os.path.join(args.input_project, "images")
    for idx, image in enumerate(sorted(os.listdir(images))):
        try:
            if idx < args.no_image_process - 1:
                b, g, r, a, bbox = orthophoto_direct(args, os.path.join(images, image))
            else:
                b, g, r, a, bbox = orthophoto_lba(args, os.path.join(images, image))
                #TODO: Modify images folder
        except Exception as e:
            print(e)
            b, g, r, a, bbox = orthophoto_direct(args, os.path.join(images, image))        

        ### 4. Write the Orthophoto
        write_start = time.time()
        if not os.path.isdir(args.output_path):
            os.mkdir(args.output_path)
        dst_path = os.path.join(args.output_path, os.path.splitext(image)[0])
        create_pnga_optical(b, g, r, a, bbox, args.gsd, args.epsg_out, dst_path)
        # create_geotiff_optical(b, g, r, a, bbox, args.gsd, args.epsg_out, args.dst)
        write_time = time.time() - write_start
        console.print(f"Write time: {write_time:.2f} sec", style="blink bold red underline")

    print("Done")


if __name__ == '__main__':
    main()