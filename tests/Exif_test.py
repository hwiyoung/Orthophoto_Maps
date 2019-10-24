import gdal
from PIL import Image
# import exifread
import pyexiv2
import os
import math

if __name__ == '__main__':
    file_path1 = './testData/20180213_064947.tiff'
    file_path2 = '../Data/DJI_0386.JPG'
    file_path3 = './20181018_160439_346.TIFF'
    file_path4 = './testData/20190619_131032_R.tif'
    file_path5 = './20191011_074853.JPG'

    # ## GDAL
    # hDataset = gdal.Open(file_path1, gdal.GA_ReadOnly)
    # hDriver = hDataset.GetDriver()
    # print("Driver: %s/%s" % (hDriver.ShortName, hDriver.LongName))


    # ## exifread
    # # Open image file for reading (binary mode)
    # f = open(file_path4, 'rb')
    #
    # # Return Exif tags
    # tags = exifread.process_file(f)
    #
    # for tag in tags.keys():
    #    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
    #        print("Key: %s, value %s" % (tag, tags[tag]))

    ### pyexiv2
    metadata = pyexiv2.ImageMetadata(file_path5)
    metadata.read()
    print(metadata.exif_keys)
    print(metadata.xmp_keys)
    #
    # latitude = metadata['Exif.GPSInfo.GPSLatitude']
    # latitudeValue = latitude.raw_value.split('/')
    # latitudeDeg = int(latitudeValue[0])
    # latitudeMin = int(latitudeValue[1].split(' ')[1])
    # latitudeSec = int(latitudeValue[2].split(' ')[1]) / 1000
    # lat = latitudeDeg + latitudeMin/60 + latitudeSec/3600
    #
    # longitude = metadata['Exif.GPSInfo.GPSLongitude']
    # longitudeValue = longitude.raw_value.split('/')
    # longitudeDeg = int(longitudeValue[0])
    # longitudeMin = int(longitudeValue[1].split(' ')[1])
    # longitudeSec = int(longitudeValue[2].split(' ')[1]) / 1000
    # lon = longitudeDeg + longitudeMin/60 + longitudeSec/3600
    #
    # altitude = metadata['Exif.GPSInfo.GPSAltitude']
    # altitudeValue = altitude.raw_value.split('/')
    # alt = int(altitudeValue[0])/int(altitudeValue[1])
    #
    # focalLength = metadata['Exif.Photo.FocalLength']
    # sensorWidth = metadata['Exif.Photo.FocalPlaneXResolution']  # row
    # sensorWidthValue = sensorWidth.raw_value
    #
    # print('GPS info: ', lat, " ", lon, " ", alt)
    # print('Focal Length: ', focalLength.value, 'mm')
    # print('Sensor Width(Row): ', int(sensorWidthValue[0:5])-10000)

    # f = open('RPY000.txt', 'w')
    #
    # for root, dirs, files in os.walk('/home/innopam-ldm/hdd/dbrain/20190829_여수_1소티/000'):
    #     for file in files:
    #         filename = os.path.splitext(file)[0]
    #         extension = os.path.splitext(file)[1]
    #         file_path = root + '/' + file
    #
    #         if filename.split('_')[2] == '1':
    #
    #             metadata = pyexiv2.ImageMetadata(file_path)
    #             metadata.read()
    #
    #             latitude = metadata['Exif.GPSInfo.GPSLatitude']
    #             latitudeValue = latitude.raw_value.split('/')
    #             latitudeDeg = int(latitudeValue[0]) / int(latitudeValue[1].split(' ')[0])
    #             latitudeMin = int(latitudeValue[1].split(' ')[1]) / int(latitudeValue[2].split(' ')[0])
    #             latitudeSec = int(latitudeValue[2].split(' ')[1]) / int(latitudeValue[3].split(' ')[0])
    #             lat = latitudeDeg + latitudeMin/60 + latitudeSec/3600
    #
    #             longitude = metadata['Exif.GPSInfo.GPSLongitude']
    #             longitudeValue = longitude.raw_value.split('/')
    #             longitudeDeg = int(longitudeValue[0]) / int(longitudeValue[1].split(' ')[0])
    #             longitudeMin = int(longitudeValue[1].split(' ')[1]) / int(longitudeValue[2].split(' ')[0])
    #             longitudeSec = int(longitudeValue[2].split(' ')[1]) / int(longitudeValue[3].split(' ')[0])
    #             lon = longitudeDeg + longitudeMin/60 + longitudeSec/3600
    #
    #             altitude = metadata['Exif.GPSInfo.GPSAltitude']
    #             altitudeValue = altitude.raw_value.split('/')
    #             alt = int(altitudeValue[0])/int(altitudeValue[1])
    #
    #             roll = metadata['Xmp.DLS.Roll']
    #             pitch = metadata['Xmp.DLS.Pitch']
    #             yaw = metadata['Xmp.DLS.Yaw']
    #
    #             rollValue = float(roll.value) * 180 / math.pi
    #             pitchValue = float(pitch.value) * 180 / math.pi
    #             yawValue = float(yaw.value) * 180 / math.pi
    #
    #             # print(file, '\t', rollValue, '\t', pitchValue, '\t', yawValue)
    #             data = filename + '\t' + str(lon) + '\t' + str(lat) + '\t' + str(alt) + '\t' + \
    #                    str(rollValue) + '\t' + str(pitchValue) + '\t' + str(yawValue) + '\n'
    #             f.write(data)
    #
    # f.close()
