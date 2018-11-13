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

                # 0. Extract EXIF data from a image
                focal_length, orientation = Func.getExif(file_path) # unit: m

                # 1. Restore the image based on orientation information
                restored_image = Func.restoreOrientation(image, orientation)
                image_rows = restored_image.shape[0]
                image_cols = restored_image.shape[1]

                pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px

            else:
                print('Read EOP - ' + file)
                print('Latitude | Longitude | Height | Omega | Phi | Kappa')
                eo = Func.readEO(file_path)
                eo = Func.convertCoordinateSystem(eo)
                R = Func.Rot3D(eo)

                # 2. Extract a projected boundary of the image
                bbox = Func.boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)

                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                projected_cols = (bbox[1] - bbox[0]) / gsd
                projected_rows = (bbox[3] - bbox[2]) / gsd
                projected_rows, projected_cols = int(projected_rows), int(projected_cols)

                # Define the orthophoto
                output_b = np.zeros(shape=(projected_rows, projected_cols), dtype=np.uint8)
                output_g = np.zeros(shape=(projected_rows, projected_cols), dtype=np.uint8)
                output_r = np.zeros(shape=(projected_rows, projected_cols), dtype=np.uint8)
                output_a = np.zeros(shape=(projected_rows, projected_cols), dtype=np.uint8)

                print('backProjection_resample')
                coord1 = np.zeros(shape=(3, 1))
                coord2 = np.zeros(shape=(2, 1))
                for row in range(projected_rows):
                    for col in range(projected_cols):
                        coord1[0] = bbox[0] + col * gsd - eo[0]
                        coord1[1] = bbox[3] - row * gsd - eo[1]
                        coord1[2] = ground_height - eo[2]

                        # 3. Backprojection
                        Func.backProjection(coord1, R, focal_length, pixel_size, (image_rows, image_cols), coord2)

                        # 4. Resampling
                        Func.resample(coord2, restored_image, output_b, output_g, output_r, output_a, (row, col))

                output_image = cv2.merge((output_b, output_g, output_r, output_a))

                cv2.imwrite('./' + filename + '.png', output_image)
