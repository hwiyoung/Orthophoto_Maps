import argparse
import platform
import subprocess
import numpy as np


def solve_local_AT(image_path, method):
    if platform.system() == "Windows" and method == "photoscan":
        command = "C:/Program Files/Agisoft/PhotoScan Pro/photoscan.exe"
        # ret_bytes = subprocess.check_output([command, "-r", "./module/lba_photoscan_run.py", "--image-path", ' '.join(image_path)])
        ret_bytes = subprocess.check_output(
            [command, "-r", "./module/lba_photoscan_run.py", "--image-path",
             image_path[0], image_path[1], image_path[2], image_path[3], image_path[4]])
        ret_str = ret_bytes.decode()
        longitude = float(ret_str.split("\n")[-7])
        latitude = float(ret_str.split("\n")[-6])
        altitude = float(ret_str.split("\n")[-5])
        omega = float(ret_str.split("\n")[-4])
        phi = float(ret_str.split("\n")[-3])
        kappa = float(ret_str.split("\n")[-2])
        eo = np.array([longitude, latitude, altitude, omega, phi, kappa])
        return eo
    elif platform.system() == "Linux" and method == "photoscan":
        # command = "~/PhotoScan/photoscan-pro/photoscan.sh"
        command = "/home/innopam-ldm/PhotoScan/photoscan-pro/photoscan.sh"
        subprocess.call([command, "-r", "lba_photoscan_run.py", "--image-path", image_path])
        # os.system("/home/innopam-ldm/PhotoScan/photoscan-pro/photoscan.sh -r lba_photoscan_run.py --image-path" + image_path)
    else:
        print("None")
