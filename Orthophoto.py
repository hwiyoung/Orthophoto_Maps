import os
import numpy as np
import cv2
import ProcessFunction as Func

if __name__ == '__main__':
    ground_height = 0  # unit: m
    sensor_width = 6.3  # unit: mm

    for root, dirs, files in os.walk('./Data'):
        for file in files:
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
                print('Latitude | Longitude | Height | Omega | Phi | Kappa')
                eo = Func.readEO(file_path)
                eo = Func.convertCoordinateSystem(eo)

                # 2. Extract a projected boundary of the image
                bbox = Func.boundary(restored_image, eo, ground_height, pixel_size, focal_length)

                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                projected_cols = (bbox[1] - bbox[0]) / gsd
                projected_rows = (bbox[3] - bbox[2]) / gsd

                # Define the orthophoto
                output_image_b = np.zeros(shape=(int(projected_rows), int(projected_cols)), dtype='float32')
                output_image_g = np.zeros(shape=(int(projected_rows), int(projected_cols)), dtype='float32')
                output_image_r = np.zeros(shape=(int(projected_rows), int(projected_cols)), dtype='float32')
                output_image_a = np.zeros(shape=(int(projected_rows), int(projected_cols)), dtype='float32')

                coord1 = np.zeros(shape=(3, 1))
                for row in range(int(projected_rows)):
                    for col in range(int(projected_cols)):
                        coord1[0] = bbox[0] + col * gsd
                        coord1[1] = bbox[3] - row * gsd
                        coord1[2] = ground_height

                        # 3. Backprojection
                        coord2 = Func.backProjection(coord1, eo, focal_length, pixel_size, [image_rows, image_cols])

                        # 4. Resampling
                        pixel = Func.resample(coord2, restored_image)

                        output_image_b[row, col] = pixel[0]
                        output_image_g[row, col] = pixel[1]
                        output_image_r[row, col] = pixel[2]
                        output_image_a[row, col] = pixel[3]

                output_image = cv2.merge(output_image_b, output_image_g, output_image_r, output_image_a)

                #cv2.imwrite(root + '/' + file, output_image)