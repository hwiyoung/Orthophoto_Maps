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
    else:
        print("None")

def solve_local_AT2(image_path, method, ref_eo_np, seq):
    if platform.system() == "Windows" and method == "photoscan":
        command = "C:/Program Files/Agisoft/PhotoScan Pro/photoscan.exe"
        ret_bytes = subprocess.check_output(
            [command, "-r", "./module/lba_photoscan_run2.py",
             "--image-path", image_path[0], image_path[1], image_path[2], image_path[3], image_path[4],
             "--reference", ref_eo_np[0, 0], ref_eo_np[0, 1], ref_eo_np[0, 2], ref_eo_np[0, 3], ref_eo_np[0, 4],
             ref_eo_np[0, 5],
             ref_eo_np[1, 0], ref_eo_np[1, 1], ref_eo_np[1, 2], ref_eo_np[1, 3], ref_eo_np[1, 4], ref_eo_np[1, 5],
             ref_eo_np[2, 0], ref_eo_np[2, 1], ref_eo_np[2, 2], ref_eo_np[2, 3], ref_eo_np[2, 4], ref_eo_np[2, 5],
             ref_eo_np[3, 0], ref_eo_np[3, 1], ref_eo_np[3, 2], ref_eo_np[3, 3], ref_eo_np[3, 4], ref_eo_np[3, 5],
             ref_eo_np[4, 0], ref_eo_np[4, 1], ref_eo_np[4, 2], ref_eo_np[4, 3], ref_eo_np[4, 4], ref_eo_np[4, 5],
             "--sequence", str(seq)])
        ret_str = ret_bytes.decode()
        eo = np.empty(shape=(5, 6))
        for i in range(5):
            longitude = float(ret_str.split("\n")[-10-i*9])
            latitude = float(ret_str.split("\n")[-9-i*9])
            altitude = float(ret_str.split("\n")[-8-i*9])
            yaw = float(ret_str.split("\n")[-7-i*9])
            pitch = float(ret_str.split("\n")[-6-i*9])
            roll = float(ret_str.split("\n")[-5-i*9])
            eo[i] = np.array([longitude, latitude, altitude, roll, pitch, yaw])
        omega = float(ret_str.split("\n")[-4])
        phi = float(ret_str.split("\n")[-3])
        kappa = float(ret_str.split("\n")[-2])
        return eo, np.array([omega, phi, kappa])
    elif platform.system() == "Linux" and method == "photoscan":
        # command = "~/PhotoScan/photoscan-pro/photoscan.sh"
        command = "/home/innopam-ldm/PhotoScan/photoscan-pro/photoscan.sh"
        subprocess.call([command, "-r", "lba_photoscan_run2.py", "--image-path", image_path])
    else:
        print("None")

def solve_local_AT3(image_path, method, ref_eo_np, seq):
    if platform.system() == "Windows" and method == "photoscan":
        command = "C:/Program Files/Agisoft/PhotoScan Pro/photoscan.exe"
        ret_bytes = subprocess.check_output(
            [command, "-r", "./module/lba_photoscan_run3.py",
             "--image-path", image_path[0], image_path[1], image_path[2], image_path[3], image_path[4],
             "--reference", ref_eo_np[0, 0], ref_eo_np[0, 1], ref_eo_np[0, 2], ref_eo_np[0, 3], ref_eo_np[0, 4],
             ref_eo_np[0, 5],
             ref_eo_np[1, 0], ref_eo_np[1, 1], ref_eo_np[1, 2], ref_eo_np[1, 3], ref_eo_np[1, 4], ref_eo_np[1, 5],
             ref_eo_np[2, 0], ref_eo_np[2, 1], ref_eo_np[2, 2], ref_eo_np[2, 3], ref_eo_np[2, 4], ref_eo_np[2, 5],
             ref_eo_np[3, 0], ref_eo_np[3, 1], ref_eo_np[3, 2], ref_eo_np[3, 3], ref_eo_np[3, 4], ref_eo_np[3, 5],
             ref_eo_np[4, 0], ref_eo_np[4, 1], ref_eo_np[4, 2], ref_eo_np[4, 3], ref_eo_np[4, 4], ref_eo_np[4, 5],
             "--sequence", str(seq)])
        ret_str = ret_bytes.decode()
        longitude = float(ret_str.split("\n")[-10])
        latitude = float(ret_str.split("\n")[-9])
        altitude = float(ret_str.split("\n")[-8])
        yaw = float(ret_str.split("\n")[-7])
        pitch = float(ret_str.split("\n")[-6])
        roll = float(ret_str.split("\n")[-5])
        omega = float(ret_str.split("\n")[-4])
        phi = float(ret_str.split("\n")[-3])
        kappa = float(ret_str.split("\n")[-2])
        eo = np.array([longitude, latitude, altitude, roll, pitch, yaw])
        return eo, np.array([omega, phi, kappa])
    elif platform.system() == "Linux" and method == "photoscan":
        # command = "~/PhotoScan/photoscan-pro/photoscan.sh"
        command = "/home/innopam-ldm/PhotoScan/photoscan-pro/photoscan.sh"
        subprocess.call([command, "-r", "lba_photoscan_run3.py", "--image-path", image_path])
    else:
        print("None")