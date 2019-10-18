import socket
import cv2
import time
import uuid
from numba import jit

# 1. 서버 주소 지정
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = ("localhost", 5000)
# 2. Video 경로 지정 (추후 udp통신으로 경로를 전달받도록 수정 예정)
vidcap = cv2.VideoCapture('../../DJI_0018.MOV')
# 3. FPS 지정
fps = 1

frame_width = str(int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH)))
frame_height = str(int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT)))


@jit(nopython=True)
def sendall(sock, data, addr):
    datalen = 65508
    start = 0
    end = start + datalen - 1
    totalsize = 0
    uuid_ = uuid.uuid4().hex

    # Sending packet info (header(start), uuid, width, height, data)
    sock.sendto(b'start', addr)
    sock.sendto(uuid_.encode(), addr)
    sock.sendto(frame_width.encode(), addr)
    sock.sendto(frame_height.encode(), addr)

    while totalsize < len(data):
        sentsize = sock.sendto(data[start:end], addr)
        # time.sleep(0.01)
        if not sentsize: return None
        start = start + sentsize
        end = start + datalen - 1
        totalsize += sentsize

    # Sending log info

    return totalsize


success = True
count = 0
total_time = time.time()

while success:
    vidcap.set(cv2.CAP_PROP_POS_MSEC, (count * (1 / fps) * 1000))
    start = time.time()
    success, image = vidcap.read()

    if not success:
        break

    print("frame extract time:", time.time() - start)

    count += 1
    strimg = image.tostring()
    ret = sendall(s, strimg, dest)
    print("1 frame sent: ", time.time() - start)

print("total: ", time.time() - total_time)
s.close()
