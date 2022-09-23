import numpy as np
import math
from osgeo.osr import SpatialReference, CoordinateTransformation
import osgeo

def readEO(path):
    eo_line = np.genfromtxt(path, delimiter='\t',
                            dtype={'names': ('Image', 'Longitude', 'Latitude', 'Height', 'Omega', 'Phi', 'Kappa'),
                                   'formats': ('U30', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')})

    eo_line['Omega'] = eo_line['Omega'] * math.pi / 180
    eo_line['Phi'] = eo_line['Phi'] * math.pi / 180
    eo_line['Kappa'] = eo_line['Kappa'] * math.pi / 180

    eo = [float(eo_line['Longitude']), float(eo_line['Latitude']), float(eo_line['Height']),
          float(eo_line['Omega']), float(eo_line['Phi']), float(eo_line['Kappa'])]
    print(eo)

    return eo


def tmcentral2latlon(eo):
    # Define the TM central coordinate system (EPSG 5186)
    epsg5186 = SpatialReference()
    epsg5186.ImportFromEPSG(5186)

    # Define the wgs84 system (EPSG 4326)
    epsg4326 = SpatialReference()
    epsg4326.ImportFromEPSG(4326)

    tm2latlon = CoordinateTransformation(epsg5186, epsg4326)

    # Check the transformation for a point close to the centre of the projected grid
    lonlat = tm2latlon.TransformPoint(float(eo[0]), float(eo[1]))  # The order: x, y
    eo[0:2] = lonlat[0:2]

    return eo

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

def rot_2d(theta):
    # Convert the coordinate system not coordinates
    return np.array([[np.cos(theta), np.sin(theta)],
                     [-np.sin(theta), np.cos(theta)]])

def rpy_to_opk(Camera, maker=""):
    """
    Convert Roll Pitch Yaw from Camera in degrees
    to OPK (Omega Phi Kappa) np.array in radians 
    return the OPK np.array
    """
    rpy = [Camera['Roll'], Camera['Pitch'],Camera['Yaw']]

    roll_pitch = np.empty_like(rpy[0:2])
    
    if maker == "samsung":

        roll_pitch[0] = -rpy[1]
        roll_pitch[1] = -rpy[0]

        omega_phi = np.dot(rot_2d(rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
        kappa = -rpy[2] - 90
        return np.array([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa])
    else:
        roll_pitch[0] = 90 + rpy[1]
        if 180 - abs(rpy[0]) <= 0.1:
            roll_pitch[1] = 0
        else:
            roll_pitch[1] = rpy[0]

        omega_phi = np.dot(rot_2d(rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
        kappa = -rpy[2]

        return np.array(np.radians([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa]))
