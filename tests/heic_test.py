import pyheif
import io
from PIL import Image
import numpy as np

file_name = "20200205_151125.heic"
i = pyheif.read_heif(file_name)

# Convert to other file format like jpeg
# https://stackoverflow.com/questions/54395735/how-to-work-with-heic-image-file-types-in-python
s = io.BytesIO()
pi = Image.frombytes(mode=i.mode, size=i.size, data=i.data)
# https://stackoverflow.com/questions/384759/how-to-convert-a-pil-image-into-a-numpy-array
img = np.asarray(pi)

print("Hello")
