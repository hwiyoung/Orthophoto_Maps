from pyexiv2 import metadata
import os
import numpy as np
from copy import copy

def rot_2d(theta):
    # Convert the coordinate system not coordinates
    return np.array([[np.cos(theta), np.sin(theta)],
                     [-np.sin(theta), np.cos(theta)]])

def rpy_to_opk_test(smartphone_rpy):
    roll_pitch = copy(smartphone_rpy[0:2])

    roll_pitch[0] = -smartphone_rpy[1]
    roll_pitch[1] = -smartphone_rpy[0]

    omega_phi = np.dot(rot_2d(smartphone_rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
    kappa = -smartphone_rpy[2]-90
    return np.array([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa])

# f = open('../../Smartphone_Image_opk/rpy.txt', "w")
for root, dirs, files in os.walk('../../Smartphone_Image_opk'):
    files.sort()
    for file in files:
        file_path = root + '/' + file
        print("*******", file, "*******")
        meta = metadata.ImageMetadata(file_path)
        meta.read()

        # print(meta.exif_keys)
        # print(meta.xmp_keys)

        roll = float(meta['Xmp.DLS.Roll'].value) * 180 / np.pi
        pitch = float(meta['Xmp.DLS.Pitch'].value) * 180 / np.pi
        yaw = float(meta['Xmp.DLS.Yaw'].value) * 180 / np.pi
        print(roll, pitch, yaw)
        data = file + "\t" + str(roll) + "\t" + str(pitch) + "\t" + str(yaw) + "\n"
        # f.write(data)

        opk = rpy_to_opk_test(np.array([roll, pitch, yaw]))

        print()

# f.close()
