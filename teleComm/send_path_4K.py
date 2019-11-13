import socket

s0 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dest = ("localhost", 57810)

s0.sendto(b'path', dest)
s0.sendto(b"15", dest)
s0.sendto(b"C:/DJI_0018.csv", dest)
