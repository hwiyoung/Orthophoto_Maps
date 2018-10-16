import os
import numpy as np
import cv2
import ProcessFunction as Func

if __name__ == '__main__':
    ground_height = 0
    pixel_size = 0.00157424E-3  # unit: m/px (mm/px * 10 ^ -3)

    for root, dirs, files in os.walk('./Data'):
        for file in files:
            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]

            file_path = root + '/' + file
            if extension == '.JPG':
                print(file_path)
                image = cv2.imread(file_path)

                # 0. Extract Interior orientation paramters from the image
                focal_length = Func.GetFocalLength(file_path) # unit: m

                # 1. Restore the image based on orientation information
                restored_image = Func.Restore(image, file_path)
                #cv2.imshow('test', restored_image)
            else:
                print(file_path)
                eo = Func.ReadEO(file_path)

                # 2. Extract a projected boundary of the image
                bbox = Func.Boundary(restored_image, eo, ground_height)

                #gsd = (pixel_size * (eo_line['Height'] - ground_height)) / focal_length
                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length # unit: m/px
                rows = restored_image.shape[0]
                cols = restored_image.shape[1]

                for row in range(rows):
                    for col in range(cols):
                        # 3. Image projection
                        coord1 = Func.Projection(row, col, eo, ground_height)

                        # 4. Backprojection
                        coord2 = Func.Backprojection(coord1, eo, ground_height)

                        # 5. Resampling
                        pixel = Func.Resample(coord2, restored_image)
                        bbox[row][col] = pixel

                #cv2.imwrite(root + '/' + file, bbox)