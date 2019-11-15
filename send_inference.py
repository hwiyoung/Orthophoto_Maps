import socket
import json

# bbox = [[1469,129],[1469,130],[1470,130],[1470,129]]    # json array
# bbox = [{1469,129},{1469,130},{1470,130},{1470,129}]    # json array
with open("bbox.json", "r") as bbox:
    json_array = json.load(bbox)
str_json = str(json_array)
str_json = str_json.replace(' ', '')
length = str(len(str_json))

s0 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dest = ("localhost", 57810)

s0.sendto(b'INFE', dest)    # Header
s0.sendto(b"1", dest)       # Frame number
s0.sendto(length.encode(), dest)
s0.sendto(str_json.encode(), dest)
print('Sent inference data!')
