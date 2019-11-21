import subprocess
import io

# input_file = "C:/DJI_0018.MOV"    # Model - 1929
input_file = "C:/DJI_0114.MOV"  # Model - 1933
exe = "../../exiftool.exe"

process = subprocess.Popen([exe, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

metadata = process.stdout.read().decode()
model_field = metadata.find('Model')
model_name = metadata[model_field+34:model_field+34+7]
name = model_name.rstrip()
print(model_name)
