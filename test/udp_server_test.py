import socket
import numpy as np
import cv2
import os

# 1. 주소 지정
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('localhost', 5000))
print("binding..")

packetsize = 65507
cnt = 0

result_folder = "result"
if not os.path.isdir(result_folder):
    os.mkdir(result_folder)

while True:
    if s.recv(5) == b'start':
        totalsize = 0
        frame_cnt=0
        pre_frame = 0
        uuid_ = s.recv(32)
        framewidth = s.recv(4)
        frameheight = s.recv(4)
        datasize = int(frameheight)*int(framewidth)*3

        while totalsize < datasize:

            bytesimg = s.recv(packetsize)
            frame = np.fromstring(bytesimg, dtype='uint8')
            if frame_cnt :
                frame = np.append(pre_frame, frame)

            pre_frame = frame
            frame_cnt += 1
            totalsize += len(bytesimg)
            test=1

        decimg = frame.reshape((int(frameheight),int(framewidth),3))
        cv2.imwrite("./"+result_folder+"/test%d.jpg"%cnt, decimg)
        # cv2.imshow('SERVER', decimg)
        # cv2.waitKey(0)

    cnt += 1

s.close()
