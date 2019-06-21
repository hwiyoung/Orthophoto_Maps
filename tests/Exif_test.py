import gdal
from PIL import Image
import piexif
# from libxmp import XMPFiles, consts

if __name__ == '__main__':
    file_path1 = './testData/20180213_064947.tiff'
    file_path2 = './Data/DJI_0386.JPG'

    # ## GDAL
    # hDataset = gdal.Open(file_path1, gdal.GA_ReadOnly)
    # hDriver = hDataset.GetDriver()
    # print("Driver: %s/%s" % (hDriver.ShortName, hDriver.LongName))


    ### piexif
    # exif_dict = piexif.load(file_path1)
    # for ifd in ("0th", "Exif", "GPS", "1st"):
    #     for tag in exif_dict[ifd]:
    #         print(piexif.TAGS[ifd][tag]["name"], exif_dict[ifd][tag])

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
