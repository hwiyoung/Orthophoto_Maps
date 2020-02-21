from pyexiv2 import metadata
import os
import numpy as np

f = open('../../Smartphone_Image_opk/rpy.txt', "w")
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
        f.write(data)

        print()

f.close()