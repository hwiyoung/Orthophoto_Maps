import os
import subprocess

working_path1 = '../OTB-7.0.0-Linux64/'
working_path2 = './bin/'
set_env = './otbenv.profile'
mosaic_execution = './otbcli_Mosaic'

dstPath = '/internalCompany/PM2019007_nifs/DKC/yeosu/001_stacks_orthophotos/'
band_b_in = [dstPath + 'IMG_0200_b.tif', dstPath + 'IMG_0201_b.tif', dstPath + 'IMG_0202_b.tif',
             dstPath + 'IMG_0203_b.tif', dstPath + 'IMG_0204_b.tif']
bandList_b_out = dstPath + '/IMG_b_test.tif'

#change path
os.chdir(working_path1)
subprocess.call('ls')
# https://stackoverflow.com/questions/13702425/source-command-not-found-in-sh-shell/13702876
subprocess.call(set_env, shell=True)

os.chdir(working_path2)
subprocess.call('ls')
subprocess.call(mosaic_execution)
subprocess.call(mosaic_execution + ' -il ' + ' '.join(band_b_in) +
                ' -comp.feather ' + ' large ' + ' -out ' + bandList_b_out, shell=True)
