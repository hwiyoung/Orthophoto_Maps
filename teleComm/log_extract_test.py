import cv2
import numpy as np
import pandas as pd

cap = cv2.VideoCapture('../../DJI_0018.MOV')
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(frame_count)

print(cap.get(3), cap.get(4))
print(fps)

count = 0

csv_file = 'DJI_0018_modify.csv'

print('********** Read csv file of drone log **********')
df = pd.read_csv(csv_file, low_memory=False)

print('********** Extract rows on recording **********')
df = df[df['CAMERA_INFO.recordState'] == 'Starting']

print('********** Extract columns on need **********')
df = df[['CUSTOM.updateTime', 'OSD.latitude', 'OSD.longitude', 'OSD.height [m]',
         'OSD.xSpeed [m/s]', 'OSD.ySpeed [m/s]', 'OSD.zSpeed [m/s]',
         'OSD.roll', 'OSD.pitch', 'OSD.yaw',
         'GIMBAL.pitch', 'GIMBAL.roll', 'GIMBAL.yaw']]

df_np = df.to_numpy()
for i in range(df_np[:, 0].shape[0]):
    df_np[i, 0] = df_np[:, 0][i][11:23]
    # df_np[i, 0][0:2] = str(int(df_np[i, 0][0:2]) + 9)

logs = np.empty((df_np.shape[0]*3, df_np.shape[1]), dtype=object)
for i in range(df_np.shape[0]):
    logs[3*i:3*i+3][:] = df_np[i][:].reshape(1, df_np.shape[1])
