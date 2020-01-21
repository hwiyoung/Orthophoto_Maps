import subprocess
import os

input_file = "./20191011_074853.JPG"
exe = "exiftool.exe"
# process = subprocess.Popen([exe, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

""" GPS Longitude """
longitude_field = "-gpslongitude"
process = subprocess.Popen([exe, longitude_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
metadata = process.stdout.read().decode()

start = metadata.find(":")
deg = metadata.find("deg")
min = metadata.find("'")
sec = metadata.find("\"")

lon_deg_value = float(metadata[start+2:deg-1])
lon_min_value = float(metadata[deg+4:min])
lon_sec_value = float(metadata[min+2:sec])
lon_value = lon_deg_value + lon_min_value / 60 + lon_sec_value / 3600


""" GPS Latitude """
latitude_field = "-gpslatitude"
process = subprocess.Popen([exe, latitude_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
metadata = process.stdout.read().decode()

start = metadata.find(":")
deg = metadata.find("deg")
min = metadata.find("'")
sec = metadata.find("\"")

lat_deg_value = float(metadata[start+2:deg-1])
lat_min_value = float(metadata[deg+4:min])
lat_sec_value = float(metadata[min+2:sec])
lat_value = lat_deg_value + lat_min_value / 60 + lat_sec_value / 3600


"""" GPS Altitude """
altitude_field = "-gpsaltitude"
process = subprocess.Popen([exe, altitude_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
metadata = process.stdout.read().decode()

start = metadata.find(":")
meter = metadata.find("m")

alt_value = float(metadata[start+2:meter-1])


"""" Focal length """
focallength_field = "-focallength"
process = subprocess.Popen([exe, focallength_field, input_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
metadata = process.stdout.read().decode()

start = metadata.find(":")
millimeter = metadata.find("mm")

focallength_value = float(metadata[start+2:millimeter-1])

print('Hello')
