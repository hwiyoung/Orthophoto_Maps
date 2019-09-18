import os
from osgeo import gdal

# file_list = os.listdir('./testData/mosaic')
# file_list.sort()

file_list = []
for root, dirs, files in os.walk('./testData/mosaic'):
    for file in files:
        file_list.append(root+'/'+file)
file_list.sort()

# https://gis.stackexchange.com/questions/44003/python-equivalent-of-gdalbuildvrt
vrt_options = gdal.BuildVRTOptions(resampleAlg='cubic', addAlpha=True)
my_vrt = gdal.BuildVRT('my.vrt', file_list, options=vrt_options)
my_vrt = None

# https://gis.stackexchange.com/questions/42584/how-to-call-gdal-translate-from-python-code
#Open existing dataset
src_ds = gdal.Open('my.vrt')

#Open output format driver, see gdal_translate --formats for list
format = "GTiff"
driver = gdal.GetDriverByName(format)

#Output to new format
dst_ds = driver.CreateCopy('my.tif', src_ds, 0)

#Properly close the datasets to flush to disk
dst_ds = None
src_ds = None