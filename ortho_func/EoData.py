import numpy as np
import math
from osgeo.osr import SpatialReference, CoordinateTransformation
from copy import copy

def readEO(path):
    eo_line = np.genfromtxt(path, delimiter='\t',
                            dtype={'names': ('Image', 'Longitude', 'Latitude', 'Height', 'Omega', 'Phi', 'Kappa'),
                                   'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')})

    eo_line['Omega'] = eo_line['Omega'] * math.pi / 180
    eo_line['Phi'] = eo_line['Phi'] * math.pi / 180
    eo_line['Kappa'] = eo_line['Kappa'] * math.pi / 180

    eo = [float(eo_line['Longitude']), float(eo_line['Latitude']), float(eo_line['Height']),
          float(eo_line['Omega']), float(eo_line['Phi']), float(eo_line['Kappa'])]

    return eo

def convertCoordinateSystem(eo, epsg):
    ### Convert wgs84 to epsg
    # Define the plane coordinate system
    epsg_dst = SpatialReference()
    epsg_dst.ImportFromEPSG(epsg)

    # Define the wgs84 system (EPSG 4326)
    epsg4326 = SpatialReference()
    epsg4326.ImportFromEPSG(4326)

    tm2latlon = CoordinateTransformation(epsg_dst, epsg4326)
    latlon2tm = CoordinateTransformation(epsg4326, epsg_dst)

    # Check the transformation for a point close to the centre of the projected grid
    # xy = latlon2tm.TransformPoint(float(eo[0]), float(eo[1]))   # The order: Lon, Lat
    xy = latlon2tm.TransformPoint(float(eo[1]), float(eo[0]))   # The order: Lat, Lon

    converted_eo = copy(eo)
    converted_eo[0:2] = xy[0:2]

    return converted_eo
    # eo[0:2] = xy[0:2]
    #
    # return eo

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
