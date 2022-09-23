import cv2
import numpy as np
import pyexiv2
import exiftool
from os.path import exists


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


def get_metadata(input_file):
    img = pyexiv2.Image(input_file)

    exif = img.read_exif()
    xmp = img.read_xmp()

    focal_length = convert_string_to_float(
        exif['Exif.Photo.FocalLength']) / 1000    # unit: m
    orientation = int(exif['Exif.Image.Orientation'])
    maker = exif["Exif.Image.Make"]

    longitude = convert_dms_to_deg(exif["Exif.GPSInfo.GPSLongitude"])
    latitude = convert_dms_to_deg(exif["Exif.GPSInfo.GPSLatitude"])

    lon_ref = exif['Exif.GPSInfo.GPSLongitudeRef']
    lat_ref = exif['Exif.GPSInfo.GPSLatitudeRef']

    if lon_ref == "W":
        longitude = -longitude
    if lat_ref == "S":
        latitude = -latitude

    if exif["Exif.Image.Make"] == "DJI":
        altitude = float(xmp['Xmp.drone-dji.RelativeAltitude'])
        roll = float(xmp['Xmp.drone-dji.GimbalRollDegree'])
        pitch = float(xmp['Xmp.drone-dji.GimbalPitchDegree'])
        yaw = float(xmp['Xmp.drone-dji.GimbalYawDegree'])
    elif exif["Exif.Image.Make"] == "samsung":
        altitude = convert_string_to_float(exif['Exif.GPSInfo.GPSAltitude'])
        roll = float(xmp['Xmp.DLS.Roll']) * 180 / np.pi
        pitch = float(xmp['Xmp.DLS.Pitch']) * 180 / np.pi
        yaw = float(xmp['Xmp.DLS.Yaw']) * 180 / np.pi
    else:
        altitude = 0
        roll = 0
        pitch = 0
        yaw = 0

    eo = np.array([longitude, latitude, altitude, roll, pitch, yaw])

    return focal_length, orientation, eo, maker


def get_exif(path_name):

    if (not exists(path_name)):
        print(f'Error {path_name} is not a path to an existing file')
        exit(0)

    print(f'Extracting Exif data  from {path_name}')
    with exiftool.ExifToolHelper() as et:
        metadata = et.get_metadata(path_name)[0]

    #for tag in metadata:
    #    print(f'{tag} {metadata[tag]}')

    Camera = {}
    Camera['FileName'] = path_name
    if 'File:ImageWidth' in metadata:
        Camera['ImageWidth'] = int(metadata['File:ImageWidth'])
        Camera['ImageHeight'] = int(metadata['File:ImageHeight'])
    elif 'EXIF:ImageWidth' in metadata:
        Camera['ImageWidth'] = int(metadata['EXIF:ImageWidth'])
        Camera['ImageHeight'] = int(metadata['EXIF:ImageHeight'])

    Camera['Focalength'] = float(metadata['EXIF:FocalLength']) / 1000
    Camera['Lat'] = float(metadata['EXIF:GPSLatitude'])
    Camera['Lon'] = float(metadata['EXIF:GPSLongitude'])
    Camera['LatRef'] = metadata['EXIF:GPSLatitudeRef']
    Camera['LonRef'] = metadata['EXIF:GPSLongitudeRef']
    Camera['Make'] = metadata['EXIF:Make']

    # __import__("IPython").embed()

    Camera['Orientation'] = int(metadata['EXIF:Orientation'])

    if 'S' in Camera['LatRef']:
        Camera['Lat'] = -Camera['Lat']

    if 'W' in Camera['LonRef']:
        Camera['Lon'] = -Camera['Lon']

    if 'DJI' in Camera['Make']:
        Camera['AbsAltitude'] = float(metadata['XMP:AbsoluteAltitude'])
        Camera['RelAltitude'] = float(metadata['XMP:RelativeAltitude'])
        Camera['Yaw'] = float(metadata['XMP:GimbalYawDegree'])
        Camera['Pitch'] = float(metadata['XMP:GimbalPitchDegree'])
        Camera['Roll'] = float(metadata['XMP:GimbalRollDegree'])

        # Sensor Size
        # Phantom 4 RTK
        if 'XMP:Model' in metadata:
            # Phantom 4 RTK
            if 'FC6310R' in metadata['XMP:Model']:
                Camera['Focalength'] = 8.8 / 1000
                # 5472 x 3648 (3:2) mode
                if Camera['ImageWidth'] == 5472:
                    Camera['Size'] = (13.2, 8.8)   # in mm
                # 4864 x 3648 (4:3) mode
                elif Camera['ImageWidth'] == 4864:
                    Camera['Size'] = (13.2 * 4864 / 5472,
                                      8.8 * 4864 / 5472)  # unit: mm
            # Mavic Pro
            elif 'FC220' in metadata['XMP:Model']:
                Camera['Focalength'] = 4.74 / 1000
                Camera['Size'] = (6.16, 4.55)
            else :
                print('Drone not yet in the code.')
                print('https://www.djzphoto.com/blog/2018/12/5/dji-drone-quick-specs-amp-comparison-page')
        
    elif 'samsung' in metadata['EXIF:Make']:
        #Camera['AbsAltitude'] = float(metadata['XMP:AbsoluteAltitude'])
        Camera['RelAltitude'] = float(metadata['EXIF:GPSAltitude'])
        Camera['Yaw'] = float(metadata['Xmp:Yaw']) * 180 / np.pi
        Camera['Pitch'] = float(metadata['Xmp:Pitch']) * 180 / np.pi
        Camera['Roll'] = float(metadata['Xmp:Roll']) * 180 / np.pi

    else:
        print('Your UAV/Camera is not supported yet')
        exit(0)
#        altitude = 0
#        roll = 0
#        pitch = 0
#        yaw = 0

    return Camera
    #eo = np.array([longitude, latitude, altitude, roll, pitch, yaw])


def main():
    file = './Data/DJI_0386.JPG'
    file = './tests/20191011_074853.JPG'

    #file = './mayo/100_0138_0001.JPG'
    print(f'Reading EXIF of {file}')
    print(get_exif(file))


if __name__ == "__main__":
    main()
