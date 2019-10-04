import numpy as np
import math
from osgeo.osr import SpatialReference, CoordinateTransformation
import pyexiv2

def readEO(path):
    eo_line = np.genfromtxt(path, delimiter='\t',
                            dtype={'names': ('Image', 'Longitude', 'Latitude', 'Height', 'Omega', 'Phi', 'Kappa'),
                                   'formats': ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')})

    eo_line['Omega'] = eo_line['Omega'] * math.pi / 180
    eo_line['Phi'] = eo_line['Phi'] * math.pi / 180
    eo_line['Kappa'] = eo_line['Kappa'] * math.pi / 180

    eo = [float(eo_line['Latitude']), float(eo_line['Longitude']), float(eo_line['Height']),
          float(eo_line['Omega']), float(eo_line['Phi']), float(eo_line['Kappa'])]
    print(eo)

    return eo

def readEO_multiSpectral(path):
    metadata = pyexiv2.ImageMetadata(path)
    metadata.read()

    # Lon, Lat, Alt, Roll, Pitch, Yaw
    latitude = metadata['Exif.GPSInfo.GPSLatitude']
    latitudeValue = latitude.raw_value.split('/')
    latitudeDeg = int(latitudeValue[0]) / int(latitudeValue[1].split(' ')[0])
    latitudeMin = int(latitudeValue[1].split(' ')[1]) / int(latitudeValue[2].split(' ')[0])
    latitudeSec = int(latitudeValue[2].split(' ')[1]) / int(latitudeValue[3].split(' ')[0])
    lat = latitudeDeg + latitudeMin / 60 + latitudeSec / 3600

    longitude = metadata['Exif.GPSInfo.GPSLongitude']
    longitudeValue = longitude.raw_value.split('/')
    longitudeDeg = int(longitudeValue[0]) / int(longitudeValue[1].split(' ')[0])
    longitudeMin = int(longitudeValue[1].split(' ')[1]) / int(longitudeValue[2].split(' ')[0])
    longitudeSec = int(longitudeValue[2].split(' ')[1]) / int(longitudeValue[3].split(' ')[0])
    lon = longitudeDeg + longitudeMin / 60 + longitudeSec / 3600

    altitude = metadata['Exif.GPSInfo.GPSAltitude']
    altitudeValue = altitude.raw_value.split('/')
    alt = int(altitudeValue[0]) / int(altitudeValue[1])

    roll = metadata['Xmp.DLS.Roll']
    pitch = metadata['Xmp.DLS.Pitch']
    yaw = metadata['Xmp.DLS.Yaw']

    # Radians
    rollValue = float(roll.value)
    pitchValue = float(pitch.value)
    yawValue = float(yaw.value)

    # # Degrees
    # rollValue = float(roll.value) * 180 / math.pi
    # pitchValue = float(pitch.value) * 180 / math.pi
    # yawValue = float(yaw.value) * 180 / math.pi

    eo = [lon, lat, alt, rollValue, pitchValue, yawValue]

    return eo

def convertCoordinateSystem(eo):
    # Define the TM central coordinate system (EPSG 5186)
    epsg5186 = SpatialReference()
    epsg5186.ImportFromEPSG(5186)

    # Define the TM central coordinate system (EPSG 5186)
    epsg3857 = SpatialReference()
    epsg3857.ImportFromEPSG(3857)

    # Define the wgs84 system (EPSG 4326)
    epsg4326 = SpatialReference()
    epsg4326.ImportFromEPSG(4326)

    tm2latlon = CoordinateTransformation(epsg5186, epsg4326)
    latlon2tm = CoordinateTransformation(epsg4326, epsg5186)
    latlon2world = CoordinateTransformation(epsg4326, epsg3857)

    # Check the transformation for a point close to the centre of the projected grid
    # xy = latlon2tm.TransformPoint(float(eo[0]), float(eo[1]))  # The order: Lon, Lat
    xy = latlon2world.TransformPoint(float(eo[0]), float(eo[1]))  # The order: Lon, Lat
    eo[0:2] = xy[0:2]

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
