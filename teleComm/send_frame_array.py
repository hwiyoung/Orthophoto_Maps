import numpy as np
import cv2

video_path = 'C:/DJI_0018.MOV'
vidcap = cv2.VideoCapture(video_path)

frame_number = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
success, np_image = vidcap.read()

mm = np.memmap('frame_image', mode='w+', shape=np_image.shape, dtype=np_image.dtype)
mm[:] = np_image[:]
mm.flush()

# read_info = np.arange(0, dtype='uint8')
# read_info.resize(300, 303, 3)
# np_read = np.memmap('frame_image', mode='r', shape=np_image.shape, dtype=np_images.dtype)
# print('read shape :', np_read.shape, 'type:', np_read.dtype)
# Image.fromarray(np_read).show()