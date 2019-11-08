import os
import subprocess

working_path = '../OTB-7.0.0-Linux64/'
set_env = 'source'# ./otbenv.profile'
mosaic_execution = 'otbcli_Mosaic'

#change path
os.chdir(working_path)
subprocess.call('ls')

subprocess.call(set_env, shell=True)
subprocess.call(mosaic_execution)
