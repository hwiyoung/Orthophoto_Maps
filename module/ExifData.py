import cv2
import numpy as np
from PIL import Image
import subprocess
import platform
from pyexiv2 import metadata

def getExif(path):
    src_image = Image.open(path)
    info = src_image._getexif()

    # Focal Length
    focalLength = info[37386]
    focal_length = focalLength[0] / focalLength[1] # unit: mm
    focal_length = focal_length * pow(10, -3) # unit: m

    # Orientation
    try:
        orientation = info[274]
    except:
        orientation = 0

    return focal_length, orientation

def restoreOrientation(image, orientation):
    if orientation == 8:
        restored_image = rotate(image, -90)
    elif orientation == 6:
        restored_image = rotate(image, 90)
    elif orientation == 3:
        restored_image = rotate(image, 180)
    else:
        restored_image = image

    return restored_image

def rotate(image, angle):
    # https://www.pyimagesearch.com/2017/01/02/rotate-images-correctly-with-opencv-and-python/

    height = image.shape[0]
    width = image.shape[1]
    center = (width/2, height/2)

    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    rotation_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    abs_cos = abs(rotation_mat[0, 0])
    abs_sin = abs(rotation_mat[0, 1])

    # compute the new bounding dimensions of the image
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    # adjust the rotation matrix to take into account translation
    rotation_mat[0, 2] += bound_w / 2 - center[0]
    rotation_mat[1, 2] += bound_h / 2 - center[1]

    # perform the actual rotation and return the image
    rotated_mat = cv2.warpAffine(image, rotation_mat, (bound_w, bound_h))
    return rotated_mat

def get_metadata(input_file, os_name):
    if os_name == "Linux":
        meta = metadata.ImageMetadata(input_file)
        meta.read()

        focal_length = convert_fractions_to_float(meta['Exif.Photo.FocalLength'].value) / 1000
        orientation = meta['Exif.Image.Orientation'].value
        maker = meta["Exif.Image.Make"].value

        longitude = convert_dms_to_deg(meta["Exif.GPSInfo.GPSLongitude"].value)
        latitude = convert_dms_to_deg(meta["Exif.GPSInfo.GPSLatitude"].value)

        if meta["Exif.Image.Make"].raw_value == "DJI":
            altitude = float(meta['Xmp.drone-dji.RelativeAltitude'].value)
            roll = float(meta['Xmp.drone-dji.GimbalRollDegree'].value)
            pitch = float(meta['Xmp.drone-dji.GimbalPitchDegree'].value)
            yaw = float(meta['Xmp.drone-dji.GimbalYawDegree'].value)
        elif meta["Exif.Image.Make"].raw_value == "samsung":
            altitude = convert_fractions_to_float(meta['Exif.GPSInfo.GPSAltitude'].value)
            roll = float(meta['Xmp.DLS.Roll'].value) * 180 / np.pi
            pitch = float(meta['Xmp.DLS.Pitch'].value) * 180 / np.pi
            yaw = float(meta['Xmp.DLS.Yaw'].value) * 180 / np.pi
        else:
            altitude = 0
            roll = 0
            pitch = 0
            yaw = 0

        eo = np.array([longitude, latitude, altitude, roll, pitch, yaw])
    else:
        exe = "exiftool.exe"

        process = subprocess.Popen([exe, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        meta = process.stdout.read().decode()
        focal_length_field = meta.find("Focal Length")
        orientation_field = meta.find("Orientation")

        focal_length_value = float(meta[focal_length_field + 34:focal_length_field + 34 + 6].split(" ")[0])  # mm
        focal_length = focal_length_value / 1000  # m

        try:
            orientation_value = meta[orientation_field + 34:orientation_field + 34 + 20].split(" ")[0]
            if orientation_value == "Horizontal":
                orientation = 0
        except:
            orientation = 0

        """ GPS Longitude """
        longitude_field = "-gpslongitude"
        process = subprocess.Popen([exe, longitude_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        meta = process.stdout.read().decode()

        start = meta.find(":")
        deg = meta.find("deg")
        min = meta.find("'")
        sec = meta.find("\"")

        lon_deg_value = float(meta[start + 2:deg - 1])
        lon_min_value = float(meta[deg + 4:min])
        lon_sec_value = float(meta[min + 2:sec])
        lon_value = lon_deg_value + lon_min_value / 60 + lon_sec_value / 3600

        """ GPS Latitude """
        latitude_field = "-gpslatitude"
        process = subprocess.Popen([exe, latitude_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        meta = process.stdout.read().decode()

        start = meta.find(":")
        deg = meta.find("deg")
        min = meta.find("'")
        sec = meta.find("\"")

        lat_deg_value = float(meta[start + 2:deg - 1])
        lat_min_value = float(meta[deg + 4:min])
        lat_sec_value = float(meta[min + 2:sec])
        lat_value = lat_deg_value + lat_min_value / 60 + lat_sec_value / 3600

        """" GPS Altitude """
        altitude_field = "-relativealtitude"
        process = subprocess.Popen([exe, altitude_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        meta = process.stdout.read().decode()

        start = meta.find(":")
        end = meta.find("\r")

        alt_value = float(meta[start + 2:end])

        """" Gimbal Roll Degree """
        roll_field = "-gimbalrolldegree"
        process = subprocess.Popen([exe, roll_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        meta = process.stdout.read().decode()

        start = meta.find(":")
        end = meta.find("\r")

        roll_value = float(meta[start + 2:end])

        """" Gimbal Pitch Degree """
        pitch_field = "-gimbalpitchdegree"
        process = subprocess.Popen([exe, pitch_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        meta = process.stdout.read().decode()

        start = meta.find(":")
        end = meta.find("\r")

        pitch_value = float(meta[start + 2:end])

        """" Gimbal Yaw Degree """
        yaw_field = "-gimbalyawdegree"
        process = subprocess.Popen([exe, yaw_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        meta = process.stdout.read().decode()

        start = meta.find(":")
        end = meta.find("\r")

        yaw_value = float(meta[start + 2:end])

        eo = np.array([lon_value, lat_value, alt_value, roll_value, pitch_value, yaw_value])

        """" Make """
        make_field = "-make"
        process = subprocess.Popen([exe, make_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        meta = process.stdout.read().decode()

        start = meta.find(":")
        end = meta.find("\r")

        maker = meta[start + 2:end]

    return focal_length, orientation, eo, maker

def convert_fractions_to_float(fraction):
    return fraction.numerator / fraction.denominator

def convert_dms_to_deg(dms):
    d = convert_fractions_to_float(dms[0])
    m = convert_fractions_to_float(dms[1]) / 60
    s = convert_fractions_to_float(dms[2]) / 3600
    deg = d + m + s
    return deg
