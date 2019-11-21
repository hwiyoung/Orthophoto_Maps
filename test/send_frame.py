import socket
import numpy as np
import cv2

s0 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dest = ("localhost", 57810)

video_path = 'C:/DJI_0114.MOV'
# video_path = 'C:/DJI_0018.MOV'
# video_path = 'C:/DJI_0030.MOV'
vidcap = cv2.VideoCapture(video_path)

frame_number = str(int(vidcap.get(cv2.CAP_PROP_POS_FRAMES)))
rows = str(int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
cols = str(int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH)))
success, np_image = vidcap.read()

s0.sendto(b'FRAM', dest)
s0.sendto(frame_number.encode(), dest)
s0.sendto(cols.encode(), dest)
s0.sendto(rows.encode(), dest)

# cv2.imshow('Test', np_image)
# cv2.waitKey(0)

mm = np.memmap('frame_image', mode='w+', shape=np_image.shape, dtype=np_image.dtype)
mm[:] = np_image[:]
mm.flush()
print(np_image.shape)
