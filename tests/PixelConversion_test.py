import os
import numpy as np
import cv2

if __name__ == '__main__':

    for root, dirs, files in os.walk('./testData'):
        for file in files:

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.tiff':
                print('Read the image - ' + file)
                image = cv2.imread(file_path)
                # cv2.imshow("Original", image)
                # cv2.waitKey(0)

                convertedImg = image * 0.04 - 273.15

                cv2.imshow("Test", convertedImg)
                cv2.waitKey(0)


                print('End of Test')

