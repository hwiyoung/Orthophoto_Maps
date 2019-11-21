import socket
from struct import *

# header | length | path | video_id(34 for test)

# path = 'C:/DJI_0114.csv'
path = 'C:/DJI_0018.csv'        # 525c671317165f77b0d31543634093abb
# path = 'C:/DJI_0030.csv'        # 525c671317165f77b0d31543634093aba
length = len(path)     # 15
uuid = "525c671317165f77b0d31543634093abb"  # 33

s0 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dest = ("localhost", 57810)

fmt = '<4si' + str(length) + 's33s'  # s: string, i: int
data_to_send = pack(fmt, b"PATH", length, path.encode(), uuid.encode())
s0.sendto(data_to_send, dest)

# data_to_send = "PATH" + length + path + uuid
# s0.sendto(data_to_send.encode(), dest)

# s0.sendto(b'PATH', dest)
# s0.sendto(length.encode(), dest)
# s0.sendto(path.encode(), dest)
print('Sent!')
