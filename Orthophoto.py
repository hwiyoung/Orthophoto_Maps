import os
import numpy as np
import cv2
import ProcessFunction as Func
import time

if __name__ == '__main__':
    ground_height = 0  # unit: m
    sensor_width = 6.3  # unit: mm

    for root, dirs, files in os.walk('./Data'):
        for file in files:
            start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.JPG':
                print('Read the image - ' + file)
                image = cv2.imread(file_path)

                # 0. Extract Interior orientation parameters from the image
                focal_length = Func.getFocalLength(file_path) # unit: m

                # 1. Restore the image based on orientation information
                restored_image = Func.restoreOrientation(image, file_path)
                image_rows = restored_image.shape[0]
                image_cols = restored_image.shape[1]

                pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px

            else:
                print('Read EOP - ' + file)
                print('Longitude | Latitude | Height | Omega | Phi | Kappa')
                eo = Func.readEO(file_path)
                eo = Func.convertCoordinateSystem(eo)

                # 2. Extract a projected boundary of the image
                print('Extract a boundary')
                bbox = Func.boundary(restored_image, eo, ground_height, pixel_size, focal_length)
                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px

                # 3. Backprojection & resample
                print('Backprojection & resample')
                channel_b, channel_g, channel_r, channel_a = Func.backprojection_resample(bbox, gsd, eo,
                                                                                          ground_height, focal_length,
                                                                                          pixel_size, restored_image)

                print('Merge channels')
                output_image = cv2.merge((channel_b, channel_g, channel_r, channel_a))

                print('Save the image')
                cv2.imwrite('./' + filename + '.png', output_image)

                print("--- %s seconds ---" % (time.time() - start_time))