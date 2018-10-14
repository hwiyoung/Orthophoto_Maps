import os
import numpy as np
import math
import cv2
import ProcessFunction as Func

if __name__ == '__main__':
    ground_height = 0
    pixel_size = 0.00157424E-3  # unit: m(mm * 10 ^ -3)
    focal_length = 4.73E-3      # unit: m(mm * 10 ^ -3)

    for root, dirs, files in os.walk('./Data'):
        for file in files:
            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            if extension == '.JPG':
                image = cv2.imread(root + '/' + file)
                print(root + '/' + file)
            else:
                print(root + '/' + file)
                #eo = np.loadtxt(root + '/' + file, delimiter="\t",
                #                dtype={'names' : ('Image', 'Latitude', 'Longitude', 'Height', 'Omega', 'Phi', 'Kappa'),
                #                       'formats' : ('U15', np.float, np.float, np.float, np.float, np.float, np.float, np.float)})
                eo_line = np.genfromtxt(root + '/' + file, delimiter='\t',
                                   dtype={'names' : ('Image', 'Latitude', 'Longitude', 'Height', 'Omega', 'Phi', 'Kappa'),
                                          'formats' : ('U15', '<f8', '<f8', '<f8', '<f8', '<f8', '<f8')})
                eo_line['Omega'] = eo_line['Omega'] * math.pi / 180
                eo_line['Phi'] = eo_line['Phi'] * math.pi / 180
                eo_line['Kappa'] = eo_line['Kappa'] * math.pi / 180

                eo = [eo_line['Latitude'], eo_line['Longitude'], eo_line['Height'],
                   eo_line['Omega'], eo_line['Phi'], eo_line['Kappa']]

                print(eo_line['Kappa'])
                print(eo[5])

                # 1. Restore the image based on orientation information
                restored_image = Func.Restore(image)

                # 2. Extract a projected boundary of the image
                bbox = Func.Boundary(restored_image, eo, ground_height)

                #gsd = (pixel_size * (eo_line['Height'] - ground_height)) / focal_length
                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length
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