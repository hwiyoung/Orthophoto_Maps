import numpy as np
import math
from osgeo.osr import SpatialReference, CoordinateTransformation
import osgeo

def read_eo_file(path):
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

def geographic2plane(eo, epsg=5186):
    # Define the Plane Coordinate System (e.g. 5186)
    plane = SpatialReference()
    plane.ImportFromEPSG(epsg)

    # Define the wgs84 system (EPSG 4326)
    geographic = SpatialReference()
    geographic.ImportFromEPSG(4326)

    coord_transformation = CoordinateTransformation(geographic, plane)

    # Check the transformation for a point close to the centre of the projected grid
    if int(osgeo.__version__[0]) >= 3:  # version 3.x
        if str(epsg).startswith("51"):  # for Korean CRS only (temporarily) ... TODO: for whole CRS
            # Transform(y,x) will return y, x (Northing, Easting)
            yx = coord_transformation.TransformPoint(float(eo[1]), float(eo[0]))  # The order: Lat, Lon
            eo[0:2] = yx[0:2][::-1]
        else:
            # Transform(y,x) will return x,y (Easting, Northing)
            xy = coord_transformation.TransformPoint(float(eo[1]), float(eo[0]))  # The order: Lat, Lon
            eo[0:2] = xy[0:2]
    else:  # version 2.x
        # Transform(x,y) will return x,y (Easting, Northing)
        xy = coord_transformation.TransformPoint(float(eo[0]), float(eo[1]))  # The order: Lon, Lat
        eo[0:2] = xy[0:2]

    return eo

def plane2geographic(eo, epsg=5186):
    # Define the TM central coordinate system (EPSG 5186)
    plane = SpatialReference()
    plane.ImportFromEPSG(5186)

    # Define the wgs84 system (EPSG 4326)
    geographic = SpatialReference()
    geographic.ImportFromEPSG(4326)

    coord_transformation = CoordinateTransformation(plane, geographic)

    # Check the transformation for a point close to the centre of the projected grid
    lonlat = coord_transformation.TransformPoint(float(eo[0]), float(eo[1]))  # The order: x, y
    eo[0:2] = lonlat[0:2]

    return eo

def rot_3d(eo):
    om, ph, kp = eo[3], eo[4], eo[5]

    #      | 1       0        0    |
    # Rx = | 0    cos(om)  sin(om) |
    #      | 0   -sin(om)  cos(om) |

    Rx = np.zeros(shape=(3, 3))
    cos, sin = np.cos(om), np.sin(om)

    Rx[0, 0] = 1
    Rx[1, 1], Rx[1, 2] = cos, sin    
    Rx[2, 1], Rx[2, 2] = -sin, cos

    #      | cos(ph)   0  -sin(ph) |
    # Ry = |    0      1      0    |
    #      | sin(ph)   0   cos(ph) |

    Ry = np.zeros(shape=(3, 3))
    cos, sin = np.cos(ph), np.sin(ph)

    Ry[0, 0], Ry[0, 2] = cos, -sin    
    Ry[1, 1] = 1
    Ry[2, 0], Ry[2, 2] = sin, cos    

    #      | cos(kp)   sin(kp)   0 |
    # Rz = | -sin(kp)  cos(kp)   0 |
    #      |    0         0      1 |

    Rz = np.zeros(shape=(3, 3))
    cos, sin = np.cos(kp), np.sin(kp)

    Rz[0, 0], Rz[0, 1] = cos, sin    
    Rz[1, 0], Rz[1, 1] = -sin, cos    
    Rz[2, 2] = 1

    # R = Rz * Ry * Rx
    Rzy = np.dot(Rz, Ry)
    R = np.dot(Rzy, Rx)

    return R

def rot_2d(theta):
    # Convert the coordinate system not coordinates
    return np.array([[np.cos(theta), np.sin(theta)],
                     [-np.sin(theta), np.cos(theta)]])

def rpy_to_opk(rpy, maker="DJI"):
    if maker == "DJI":
        roll_pitch = np.empty_like(rpy[0:2])
        roll_pitch[0] = 90 + rpy[1]
        if 180 - abs(rpy[0]) <= 0.1:
            roll_pitch[1] = 0
        else:
            roll_pitch[1] = rpy[0]

        omega_phi = np.dot(rot_2d(rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
        kappa = -rpy[2]
        return np.array([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa])
    elif maker == "samsung":
        roll_pitch = np.empty_like(rpy[0:2])

        roll_pitch[0] = -rpy[1]
        roll_pitch[1] = -rpy[0]

        omega_phi = np.dot(rot_2d(rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
        kappa = -rpy[2] - 90
        return np.array([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa])
    else:
        raise NotImplementedError
