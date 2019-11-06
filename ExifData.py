import cv2
import pyexiv2

def getMetadataExiv2(path):
    metadata = pyexiv2.ImageMetadata(path)
    metadata.read()

    # Focal Length
    try:
        focalLength = metadata['Exif.Photo.FocalLength']
        focal_length = focalLength.value
        focal_length = focal_length * pow(10, -3)  # unit: m
    except:
        focalLength = metadata['Exif.Image.FocalLength'].raw_value
        focal_length = int(focalLength[0])
        focal_length = focal_length * pow(10, -3)  # unit: m

    # # Sensor Width
    # sensorWidth = metadata['Exif.Photo.FocalPlaneXResolution'].value    # width
    # sensor_width = sensorWidth.numerator / sensorWidth.denominator   # unit: mm

    sensor_width = 0

    return focal_length, sensor_width

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
