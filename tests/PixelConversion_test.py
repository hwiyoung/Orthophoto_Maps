import os
import numpy as np
import cv2
from PIL import Image

import gdal

if __name__ == '__main__':

    for root, dirs, files in os.walk('./testData'):
        for file in files:

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            # file_path = '../Data/DJI_0386.JPG'

            if extension == '.tiff':
                print('Read the image - ' + file)
                # image = cv2.imread(file_path)
                # # cv2.imshow("Original", image)
                # # cv2.waitKey(0)
                #
                # convertedImg = image * 0.04 - 273.15
                #
                # cv2.imshow("Test", convertedImg)
                # cv2.waitKey(0)

                # https: // stackoverflow.com / questions / 45012128 / calculating - parameter - on - raster - using - gdal - and -python
                image = gdal.Open(file_path, gdal.GA_ReadOnly)
                columns = image.RasterXSize
                rows = image.RasterYSize
                band = image.GetRasterBand(1).ReadAsArray(0, 0, columns, rows)

                calculation = band * 0.04 - 273.15

                winname = 'Test'
                cv2.namedWindow(winname)  # Create a named window
                cv2.moveWindow(winname, 40, 30)  # Move it to (40,30)
                cv2.imshow(winname, calculation)
                cv2.waitKey(0)
                cv2.destroyAllWindows()


                print('End of Test')

