import gdal
from PIL import Image
import exifread
# from libxmp import XMPFiles, consts

if __name__ == '__main__':
    file_path1 = './testData/20180213_064947.tiff'
    file_path2 = '../Data/DJI_0386.JPG'
    file_path3 = './testData/20181018_160439_346.tiff'

    # ## GDAL
    # hDataset = gdal.Open(file_path1, gdal.GA_ReadOnly)
    # hDriver = hDataset.GetDriver()
    # print("Driver: %s/%s" % (hDriver.ShortName, hDriver.LongName))


    ## exifread
    # Open image file for reading (binary mode)
    f = open(file_path2, 'rb')

    # Return Exif tags
    tags = exifread.process_file(f)

    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            print("Key: %s, value %s" % (tag, tags[tag]))


    # ### Python XMP Toolkit
    # xmpfile = XMPFiles(file_path2, open_forupdate=True)
    # xmp = xmpfile.get_xmp()
    # print(xmp.get_property(consts.XMP_NS_DC, 'format'))



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
