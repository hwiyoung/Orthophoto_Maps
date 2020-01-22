import subprocess
import numpy as np

### Vaild only in 4:3 aspect ratio

input_file = "../Data/DJI_0386.JPG"
exe = "exiftool.exe"

fullframe_diagonal = 43.3   # mm

"""" Crop Factor """
cropfactor_field = "-ScaleFactor35efl"
process = subprocess.Popen([exe, cropfactor_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
metadata = process.stdout.read().decode()

start = metadata.find(":")
end = metadata.find("\r")

cropfactor_value = float(metadata[start+2:end])
print(cropfactor_value)

diagonal = fullframe_diagonal / cropfactor_value
print(diagonal)

x = np.sqrt(diagonal*diagonal / (4*4 + 3*3))
width = 4*x     # mm
height = 3*x    # mm
print(width, height)
