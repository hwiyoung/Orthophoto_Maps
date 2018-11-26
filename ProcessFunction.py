import numpy as np
import math
import cv2
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from osgeo.osr import SpatialReference, CoordinateTransformation
from numba import jit, prange

def getExif(path):
    src_image = Image.open(path)
    info = src_image._getexif()

    # Focal Length
    focalLength = info[37386]
    focal_length = focalLength[0] / focalLength[1] # unit: mm
    focal_length = focal_length * pow(10, -3) # unit: m

    # Orientation
    orientation = info[274]

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

def readEO(path):
    eo_line = np.genfromtxt(path, delimiter='\t',
                            dtype={'names': ('Image', 'Latitude', 'Longitude', 'Height', 'Omega', 'Phi', 'Kappa'),
                                   'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')})

    eo_line['Omega'] = eo_line['Omega'] * math.pi / 180
    eo_line['Phi'] = eo_line['Phi'] * math.pi / 180
    eo_line['Kappa'] = eo_line['Kappa'] * math.pi / 180

    eo = [float(eo_line['Latitude']), float(eo_line['Longitude']), float(eo_line['Height']),
          float(eo_line['Omega']), float(eo_line['Phi']), float(eo_line['Kappa'])]

    return eo

def convertCoordinateSystem(eo):
    # Define the TM central coordinate system (EPSG 5186)
    epsg5186 = SpatialReference()
    epsg5186.ImportFromEPSG(5186)

    # Define the wgs84 system (EPSG 4326)
    epsg4326 = SpatialReference()
    epsg4326.ImportFromEPSG(4326)

    tm2latlon = CoordinateTransformation(epsg5186, epsg4326)
    latlon2tm = CoordinateTransformation(epsg4326, epsg5186)

    # Check the transformation for a point close to the centre of the projected grid
    xy = latlon2tm.TransformPoint(float(eo[0]), float(eo[1]))
    eo[0:2] = xy[0:2]

    return eo

def boundary(image, eo, R, dem, pixel_size, focal_length):
    inverse_R = R.transpose()

    image_vertex = getVertices(image, pixel_size, focal_length)  # shape: 3 x 4

    proj_coordinates = projection(image_vertex, eo, inverse_R, dem)

    bbox = np.empty(shape=(4, 1))
    bbox[0] = min(proj_coordinates[:, 0])  # X min
    bbox[1] = max(proj_coordinates[:, 0])  # X max
    bbox[2] = min(proj_coordinates[:, 1])  # Y min
    bbox[3] = max(proj_coordinates[:, 1])  # Y max

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
    Rz[0, 1] = sin
    Rz[1, 0] = -sin
    Rz[1, 1] = cos
    Rz[2, 2] = 1

    # R = Rz * Ry * Rx
    Rzy = np.dot(Rz, Ry)
    R = np.dot(Rzy, Rx)

    return R

def getVertices(image, pixel_size, focal_length):
    rows = image.shape[0]
    cols = image.shape[1]

    # (1) ------------ (2)
    #  |     image      |
    #  |                |
    # (4) ------------ (3)

    vertices = np.empty(shape=(3, 4))

    vertices[0, 0] = -cols * pixel_size / 2
    vertices[1, 0] = rows * pixel_size / 2

    vertices[0, 1] = cols * pixel_size / 2
    vertices[1, 1] = rows * pixel_size / 2

    vertices[0, 2] = cols * pixel_size / 2
    vertices[1, 2] = -rows * pixel_size / 2

    vertices[0, 3] = -cols * pixel_size / 2
    vertices[1, 3] = -rows * pixel_size / 2

    vertices[2, :] = -focal_length

    return vertices

def projection(vertices, eo, rotation_matrix, dem):
    coord_GCS = np.dot(rotation_matrix, vertices)
    scale = (dem - eo[2]) / coord_GCS[2]

    plane_coord_GCS = scale * coord_GCS[0:2] + [[eo[0]], [eo[1]]]

    return plane_coord_GCS

#@profile
@jit(nopython=True)
def backProjection(coord, R, focal_length, pixel_size, image_size, coord_out):
    coord_CCS_m = np.dot(R, coord)  # unit: m
    scale = (coord_CCS_m[2]) / (-focal_length)
    plane_coord_CCS = coord_CCS_m[0:2] / scale

    # Convert CCS to Pixel Coordinate System
    coord_CCS_px = plane_coord_CCS / pixel_size  # unit: px

    coord_out[0] = image_size[1] / 2 + coord_CCS_px[0]
    coord_out[1] = image_size[0] / 2 - coord_CCS_px[1]

#@profile
@jit(nopython=True)
def resample(coord, image, b, g, r, a, row_col):
    # row_col: row, column in for loop
    proj_col = int(coord[0, 0])  # projected column
    proj_row = int(coord[1, 0])  # projected row

    if proj_col < 0 or proj_col >= image.shape[1]:
        return
    elif proj_row < 0 or proj_row >= image.shape[0]:
        return
    else:
        b[row_col[0], row_col[1]], g[row_col[0], row_col[1]], r[row_col[0], row_col[1]], a[row_col[0], row_col[1]] = \
            image[proj_row, proj_col][0], image[proj_row, proj_col][1], image[proj_row, proj_col][2], 255

@jit(nopython=True, parallel=True)
def backprojection_resample(boundary, gsd, eo, R, ground_height, focal_length, pixel_size, image):
    # Boundary size
    boundary_cols = int((boundary[1, 0] - boundary[0, 0]) / gsd)
    boundary_rows = int((boundary[3, 0] - boundary[2, 0]) / gsd)

    # Image size
    image_rows = image.shape[0]
    image_cols = image.shape[1]

    # Define the orthophoto
    output_b = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    output_g = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    output_r = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)
    output_a = np.zeros(shape=(boundary_rows, boundary_cols), dtype=np.uint8)

    coord1 = np.empty(shape=(3, 1))
    coord2 = np.empty(shape=(2, 1))
    for row in prange(boundary_rows):
        for col in prange(boundary_cols):
            coord1[0] = boundary[0] + col * gsd - eo[0]
            coord1[1] = boundary[3] - row * gsd - eo[1]
            coord1[2] = ground_height - eo[2]

            # 3. Backprojection
            backProjection(coord1, R, focal_length, pixel_size, (image_rows, image_cols), coord2)

            # 4. Resampling
            resample(coord2, image, output_b, output_g, output_r, output_a, (row, col))

    return output_b, output_g, output_r, output_a
