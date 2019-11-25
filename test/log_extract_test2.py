import cv2
import numpy as np
import pandas as pd


def load_log(file_path):
    df = pd.read_csv(file_path, low_memory=False)
    df = df[df['CAMERA_INFO.recordState'] == 'Starting']
    df = df[['OSD.longitude', 'OSD.latitude', 'OSD.height [m]', 'GIMBAL.roll', 'GIMBAL.pitch', 'GIMBAL.yaw']]

    global log_eo
    log_eo = df.to_numpy()


if __name__ == '__main__':
    file_name = "DJI_0002 (2)"
    folder_path = "Z:/PM2019005_ndmi/20191125/"

    rate = 60

    load_log(folder_path + file_name + ".csv")  # Extract EO

    count = 0
    vidcap = cv2.VideoCapture(folder_path + file_name + ".MOV")
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    eo = log_eo[0, :]
    for i in range(rate, length):
        if i % rate == 0:
            try:
                eo_new = log_eo[int((i - 1) / 3), :]
                eo = np.vstack((eo, eo_new))
                count = count + 1
                print(count)
            except:
                break

    print("Writing files...")
    np.savetxt(folder_path + file_name + ".txt", eo, delimiter='\t', fmt='%.10e')

    print("Hello")
