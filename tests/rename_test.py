from pyexiv2 import metadata
import os
import shutil

for root, dirs, files in os.walk('../../Smartphone_Image_test'):
    files.sort()
    for file in files:
        file_path = root + '/' + file
        print("*******", file, "*******")
        meta = metadata.ImageMetadata(file_path)
        meta.read()

        print(meta.exif_keys)
        print(meta.xmp_keys)

        datetime = meta["Exif.Image.DateTime"].value
        if datetime.month < 10:
            month = str("0") + str(datetime.month)
        else:
            month = str(datetime.month)
        if datetime.second < 10:
            second = str("0") + str(datetime.second)
        else:
            second = str(datetime.second)
        name = str(datetime.year) + "_" + month + "_" + str(datetime.day)\
               + "_" + str(datetime.hour) + "_" + str(datetime.minute) + "_" + second

        shutil.copy(file_path, "../../Smartphone_Image_opk/0225/" + name + ".jpg")

        # roll = float(meta['Xmp.DLS.Roll'].value) * 180 / np.pi
        # pitch = float(meta['Xmp.DLS.Pitch'].value) * 180 / np.pi
        # yaw = float(meta['Xmp.DLS.Yaw'].value) * 180 / np.pi
        # print(roll, pitch, yaw)
        # data = file + "\t" + str(roll) + "\t" + str(pitch) + "\t" + str(yaw) + "\n"

        print()
