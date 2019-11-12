import gdal
import gdal2tiles
import subprocess

dstPath = '/internalCompany/PM2019007_nifs/DKC/gomso_stacks_orthophoto/'

bandList_b_out = dstPath + '/IMG_b.tif'
bandList_g_out = dstPath + '/IMG_g.tif'
bandList_r_out = dstPath + '/IMG_r.tif'
bandList_n_out = dstPath + '/IMG_n.tif'
bandList_e_out = dstPath + '/IMG_e.tif'

vrt_options = gdal.BuildVRTOptions(resolution='average', resampleAlg='cubic', separate=True, VRTNodata=0)
my_vrt = gdal.BuildVRT(dstPath + '/IMG_RGB.vrt', [bandList_r_out, bandList_g_out, bandList_b_out],
                       options=vrt_options)
my_vrt = None

ds = gdal.Translate(dstPath + '/IMG_RGB.tif', dstPath + '/IMG_RGB.vrt')
ds = None

options = {'zoom': (14, 21)}
gdal2tiles.generate_tiles(dstPath + '/IMG_RGB.tif', dstPath + '/tiles/', **options)

# merge_command = ["python", "gdal2tiles", '-p', 'mercator', '-z', '14-21', '-r', 'average',
#                  dstPath + '/IMG_RGB.tif', dstPath + '/tiles']
# subprocess.call(merge_command)

