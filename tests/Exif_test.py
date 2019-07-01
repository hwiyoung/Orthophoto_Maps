import gdal
from PIL import Image
#import exifread
import pyexiv2

if __name__ == '__main__':
    file_path1 = './testData/20180213_064947.tiff'
    file_path2 = '../Data/DJI_0386.JPG'
    file_path3 = './testData/20181018_160439_346.TIFF'

    # ## GDAL
    # hDataset = gdal.Open(file_path1, gdal.GA_ReadOnly)
    # hDriver = hDataset.GetDriver()
    # print("Driver: %s/%s" % (hDriver.ShortName, hDriver.LongName))


    ### exifread
    ## Open image file for reading (binary mode)
    #f = open(file_path2, 'rb')
    #
    ## Return Exif tags
    #tags = exifread.process_file(f)
    #
    #for tag in tags.keys():
    #    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
    #        print("Key: %s, value %s" % (tag, tags[tag]))


    metadata = pyexiv2.ImageMetadata(file_path3)
    metadata.read()
    print(metadata.get_focal_length())
    # print(metadata.exif_keys)
    # print(metadata.xmp_keys)
    focalLength = metadata['Exif.Photo.FocalLength']
    sensorWidth = metadata['Exif.Photo.FocalPlaneXResolution']
    sensorWidthValue = sensorWidth.raw_value
    print('Focal Length: ', focalLength.value, 'mm')
    print('Sensor Width: ', int(sensorWidthValue[0:5])-10000)



# def getExif(path):
#     src_image = Image.open(path)
#     info = src_image._getexif()
#
#     # Focal Length
#     focalLength = info[37386]
#     focal_length = focalLength[0] / focalLength[1] # unit: mm
#     focal_length = focal_length * pow(10, -3) # unit: m
#
#     # Orientation
#     orientation = info[274]
#
#     return focal_length, orientation
