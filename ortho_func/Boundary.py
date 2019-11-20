import numpy as np
from osgeo import ogr

def boundary(image, eo, R, dem, pixel_size, focal_length):
    inverse_R = R.transpose()

    image_vertex = getVertices(image, pixel_size, focal_length)  # shape: 3 x 4

    proj_coordinates = projection(image_vertex, eo, inverse_R, dem)

    bbox = np.empty(shape=(4, 1))
    bbox[0] = min(proj_coordinates[0, :])  # X min
    bbox[1] = max(proj_coordinates[0, :])  # X max
    bbox[2] = min(proj_coordinates[1, :])  # Y min
    bbox[3] = max(proj_coordinates[1, :])  # Y max

    return bbox

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


def pcs2ccs(bbox_px, rows, cols, pixel_size, focal_length):
    """
    Convert pixel coordinate system to camera coordinate system
    :param bbox_px: Bounding box in pixel coordinate system, px - shape: 2 x n
    :param rows: The length of rows in pixel, px
    :param cols: The length of columns in pixel, px
    :param pixel_size: mm/px
    :param focal_length: mm
    :return: Bounding box in camera coordinate system, mm
    """
    bbox_camera = np.empty(shape=(3, bbox_px.shape[1]))

    bbox_camera[0, :] = (bbox_px[0, :] - cols / 2) * pixel_size
    bbox_camera[1, :] = -(bbox_px[1, :] - rows / 2) * pixel_size
    bbox_camera[2, :] = -focal_length

    return bbox_camera


def export_bbox_to_wkt(bbox, dst):
    # Create a polygon
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(bbox[0][0], bbox[2][0])   # Xmin, Ymin
    ring.AddPoint(bbox[0][0], bbox[3][0])   # Xmin, Ymax
    ring.AddPoint(bbox[1][0], bbox[3][0])   # Xmax, Ymax
    ring.AddPoint(bbox[1][0], bbox[2][0])   # Xmax, Ymin
    ring.AddPoint(bbox[0][0], bbox[2][0])   # Xmin, Ymin

    geom_poly = ogr.Geometry(ogr.wkbPolygon)
    geom_poly.AddGeometry(ring)

    # Export geometry to WKT
    wkt = geom_poly.ExportToWkt()

    f = open(dst + '.txt', 'w')
    f.write(wkt)
    f.close()

    return wkt

def export_bbox_to_wkt2(bbox, dst):
    res = "POLYGON ((" + \
          str(bbox[0, 0]) + " " + str(bbox[2, 0]) + ", " + \
          str(bbox[0, 0]) + " " + str(bbox[3, 0]) + ", " + \
          str(bbox[1, 0]) + " " + str(bbox[3, 0]) + ", " + \
          str(bbox[1, 0]) + " " + str(bbox[2, 0]) + ", " + \
          str(bbox[0, 0]) + " " + str(bbox[2, 0]) + "))"

    # f = open(dst + '.txt', 'w')
    # f.write(res)
    # f.close()
    return res


def create_pgw(bbox, gsd, dst):
    pgw = str(gsd) + '\n' + str(0) + '\n' + str(0) + '\n' + str(-gsd) + \
          '\n' + str(bbox[0][0]) + '\n' + str(bbox[3][0])
    f = open(dst + '.pgw', 'w')
    f.write(pgw)
    f.close()