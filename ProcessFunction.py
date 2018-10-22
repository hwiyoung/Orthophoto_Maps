import numpy as np
import math
import cv2
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def getFocalLength(path):
    print('GetFocalLength')
    src_image = Image.open(path)
    info = src_image._getexif()

    # Focal Length
    focalLength = info[37386]
    focal_length = focalLength[0] / focalLength[1] # unit: mm
    focal_length = focal_length * pow(10, -3) # unit: m

    return focal_length

def restoreOrientation(image, path):
    print('Restore')
    orientation = getOrientation(path)

    if orientation == 8:
        restored_image = rotate(image, -90)
    elif orientation == 6:
        restored_image = rotate(image, 90)
    elif orientation == 3:
        restored_image = rotate(image, 180)
    else:
        restored_image = image

    return restored_image

def getOrientation(path):
    src_image = Image.open(path)
    info = src_image._getexif()
    ori = info[274]

    return ori

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

def readEO(path):
    eo_line = np.genfromtxt(path, delimiter='\t',
                            dtype={'names': ('Image', 'Latitude', 'Longitude', 'Height', 'Omega', 'Phi', 'Kappa'),
                                   'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')})

    eo_line['Omega'] = eo_line['Omega'] * math.pi / 180
    eo_line['Phi'] = eo_line['Phi'] * math.pi / 180
    eo_line['Kappa'] = eo_line['Kappa'] * math.pi / 180

    eo = [eo_line['Latitude'], eo_line['Longitude'], eo_line['Height'],
          eo_line['Omega'], eo_line['Phi'], eo_line['Kappa']]

    return eo

def boundary(image, eo, dem, pixel_size, focal_length):
    print('Boundary')

    R = Rot3D(eo)

    image_vertex = getVertices(image, pixel_size, focal_length)

    proj_coordinates = np.zeros(shape=(4, 2))
    for i in range(len(image_vertex)):
        proj_coordinates[i, :] = computeProjCoords(image_vertex, eo, R, dem)

    bbox = np.zeros(shape=(4, 1))
    bbox[0] = min(proj_coordinates[:, 0])
    bbox[1] = max(proj_coordinates[:, 0])
    bbox[2] = min(proj_coordinates[:, 1])
    bbox[3] = max(proj_coordinates[:, 1])

    return bbox

def Rot3D(eo):
    om = eo[3]
    ph = eo[4]
    kp = eo[5]

    #      | 1       0        0    |
    # Rx = | 0    cos(om)  sin(om) |
    #      | 0   -sin(om)  cos(om) |

    Rx = np.zeros(shape=(3, 3))
    cos, sin = np.cos(om), np.sin(om)

    Rx[0, 0] = 1
    Rx[1, 1] = cos
    Rx[1, 2] = sin
    Rx[2, 1] = -sin
    Rx[2, 2] = cos

    #      | cos(ph)   0  -sin(ph) |
    # Ry = |    0      1      0    |
    #      | sin(ph)   0   cos(ph) |

    Ry = np.zeros(shape=(3, 3))
    cos, sin = np.cos(ph), np.sin(ph)

    Ry[0, 0] = cos
    Ry[0, 2] = -sin
    Ry[1, 1] = 1
    Ry[2, 0] = sin
    Ry[2, 2] = cos

    #      | cos(kp)   sin(kp)   0 |
    # Rz = | -sin(kp)  cos(kp)   0 |
    #      |    0         0      1 |

    Rz = np.zeros(shape=(3, 3))
    cos, sin = np.cos(kp), np.sin(kp)

    Rz[0, 0] = cos
    Rz[1, 1] = sin
    Rz[1, 0] = -sin
    Rz[1, 1] = cos
    Rz[2, 2] = 1

    # R = Rz * Ry * Rx

    R = Rz * Ry * Rx

    return R

def getVertices(image, pixel_size, focal_length):
    rows = image.shape[0]
    cols = image.shape[1]

    # (1) ------------ (2)
    #  |                |
    #  |                |
    # (4) ------------ (3)

    vertices = np.zeros(shape=(4, 3))

    vertices[0, 0] = -cols * pixel_size / 2
    vertices[0, 1] = rows * pixel_size / 2

    vertices[1, 0] = cols * pixel_size / 2
    vertices[1, 1] = rows * pixel_size / 2

    vertices[2, 0] = cols * pixel_size / 2
    vertices[2, 1] = -rows * pixel_size / 2

    vertices[3, 0] = -cols * pixel_size / 2
    vertices[3, 1] = -rows * pixel_size / 2

    vertices[:, 2] = -focal_length

    return vertices

def computeProjCoords(vertices, eo, rotation_matrix, ground_height):
    pass


def projection(row, col, eo, dem):
    print('Projection')

def backProjection(coord, eo, dem):
    print('Backprojection')

def resample(coord, image):
    print('Resample')