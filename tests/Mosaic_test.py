import os
import subprocess

working_path1 = '../OTB-7.0.0-Linux64/'
working_path2 = './bin/'
set_env = './otbenv.profile'
mosaic_execution = './otbcli_Mosaic'

#change path
os.chdir(working_path1)
subprocess.call('ls')
# https://stackoverflow.com/questions/13702425/source-command-not-found-in-sh-shell/13702876
subprocess.call(set_env, shell=True)

os.chdir(working_path2)
subprocess.call('ls')
subprocess.call(mosaic_execution)
