import socket

path = 'C:/DJI_0114.csv'
# path = 'C:/DJI_0018.csv'
# path = 'C:/DJI_0030.csv'
length = str(len(path))

s0 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dest = ("localhost", 57810)

s0.sendto(b'PATH', dest)
s0.sendto(length.encode(), dest)
s0.sendto(path.encode(), dest)
print('Sent!')
