import socket
import numpy as np
import cv2

s0 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dest = ("localhost", 57810)

video_path = 'C:/DJI_0018.MOV'
vidcap = cv2.VideoCapture(video_path)

frame_number = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
success, np_image = vidcap.read()
print(np_image.shape)

s0.sendto(b'FRAM', dest)
s0.sendto(b"1", dest)
s0.sendto(b"3840", dest)
s0.sendto(b"2160", dest)

# cv2.imshow('Test', np_image)
# cv2.waitKey(0)

mm = np.memmap('frame_image', mode='w+', shape=np_image.shape, dtype=np_image.dtype)
mm[:] = np_image[:]
mm.flush()
