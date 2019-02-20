# Orthophoto_Maps
Orthophoto_Maps is a mapping software that generate individual maps(orthophotos) from images of drone. Only with images and sensor data, you can generate orthophotos of area of interests.

## Getting Started
* Run Orthophoto.py with **<u>Data</u>** folder
* Data folder is constructed with images and each sensor data

## Input & Output
* Input - ./Data
  * Images to rectify
  * Extrinsic Orientation parameters of each image
* Output
  * Individual orthophotos - .tif(GeoTIFF)

## Flow of functions in this module
1. getExif
2. restoreOrientation
3. readEO
4. convertCoordinateSystem
5. Rot3D
6. boundary
7. projectedCoord
8. backProjection
9. resample
10. createGeoTiff
