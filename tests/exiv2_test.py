from pyexiv2 import metadata
import os
from tabulate import tabulate

def convert_fractions_to_float(fraction):
    return fraction.numerator / fraction.denominator


def convert_dms_to_deg(dms):
    d = convert_fractions_to_float(dms[0])
    m = convert_fractions_to_float(dms[1]) / 60
    s = convert_fractions_to_float(dms[2]) / 3600
    deg = d + m + s
    return deg

for root, dirs, files in os.walk('./query_images'):
    for file in files:
        file_path = root + '/' + file
        print("*******", file, "*******")
        meta = metadata.ImageMetadata(file_path)
        meta.read()

        print(meta.exif_keys)
        print(meta.xmp_keys)

        longitude = meta["Exif.GPSInfo.GPSLongitude"].value
        latitude = meta["Exif.GPSInfo.GPSLatitude"].value

        if meta["Exif.Image.Make"].raw_value == "DJI":
            altitude = float(meta['Xmp.drone-dji.RelativeAltitude'].value)
            roll = float(meta['Xmp.drone-dji.GimbalRollDegree'].value)
            pitch = float(meta['Xmp.drone-dji.GimbalPitchDegree'].value)
            yaw = float(meta['Xmp.drone-dji.GimbalYawDegree'].value)
        else:
            altitude = 0
            roll = 0
            pitch = 0
            yaw = 0

        latitude = convert_dms_to_deg(latitude)
        longitude = convert_dms_to_deg(longitude)

        print(tabulate([['Longitude', longitude], ['Latitude', latitude], ['Altitude', altitude],
                        ['Gimbal-Roll', roll], ['Gimbal-Pitch', pitch], ['Gimbal-Yaw', yaw]],
                       headers=["Field", "Value(deg)"],
                       tablefmt='orgtbl',
                       numalign="right"))
        print()

