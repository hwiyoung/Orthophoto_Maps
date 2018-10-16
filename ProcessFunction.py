import numpy as np
import math
import cv2
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def ExtractIOP(path):
    print('ExtractIOP')
    src_image = Image.open(path)

    info = src_image._getexif()
    pixel_size = 0
    focal_length = info[37386]

    return pixel_size, focal_length

def Restore(image, path):
    print('Restore')
    ori = GetOrientation(path)

    if ori == 8:
        restored_image = Rotate(image, -90)
    elif ori == 6:
        restored_image = Rotate(image, 90)
    elif ori == 3:
        restored_image = Rotate(image, 180)
    else:
        restored_image = image

    return restored_image

def GetOrientation(path):
    #print('GetOrientation')
    src_image = Image.open(path)

    info = src_image._getexif()
    ori = info[274]

    return ori

def Rotate(image, angle):
    # https://www.pyimagesearch.com/2017/01/02/rotate-images-correctly-with-opencv-and-python/
    #print('Rotate')

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

def ReadEO(path):
    eo_line = np.genfromtxt(path, delimiter='\t',
                            dtype={'names': ('Image', 'Latitude', 'Longitude', 'Height', 'Omega', 'Phi', 'Kappa'),
                                   'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')})

    eo_line['Omega'] = eo_line['Omega'] * math.pi / 180
    eo_line['Phi'] = eo_line['Phi'] * math.pi / 180
    eo_line['Kappa'] = eo_line['Kappa'] * math.pi / 180

    eo = [eo_line['Latitude'], eo_line['Longitude'], eo_line['Height'],
          eo_line['Omega'], eo_line['Phi'], eo_line['Kappa']]

    # print(eo_line['Kappa'])
    # print(eo[5])

    return eo

def Boundary(image, eo, dem):
    print('Boundary')

def Projection(row, col, eo, dem):
    print('Projection')

def Backprojection(coord, eo, dem):
    print('Backprojection')

def Resample(coord, image):
    print('Resample')