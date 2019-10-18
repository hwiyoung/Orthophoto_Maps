import cv2
import numpy as np
# import pandas as pd
import datetime

#이미지 읽기 기본 메타정보 출력######################################
cap = cv2.VideoCapture('../../DJI_0018.MOV')
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(frame_count)

#wait_time = int(1000/fps)

print(cap.get(3), cap.get(4))
print(fps)

count = 0

print('#초기 드론 로그파일(CSV) 읽기###########################################')
csv_data = np.genfromtxt('DJI_0018_modify_test.csv', delimiter=',', encoding='ascii',
                         names=('CUSTOM.updateTime', 'CUSTOM.isPhoto', 'CUSTOM.isVideo', 'CUSTOM.hSpeed [m/s]'),
                        dtype=None)#, comments='#')

print(csv_data)

#
# print('#비디오가 녹화되고 있는 시간의 record만 추출##############################')
# df = df[df['CAMERA_INFO.recordState'] == 'Starting']
# print(df.head(10))
#
# print('#필요한 colum만 추출##################################################')
# df = df[['CUSTOM.updateTime', 'OSD.latitude', 'OSD.longitude', 'OSD.height [m]', 'OSD.altitude [m]',
#              'OSD.xSpeed [m/s]', 'OSD.ySpeed [m/s]', 'OSD.zSpeed [m/s]', 'OSD.roll', 'OSD.pitch', 'OSD.yaw',
#              'CAMERA_INFO.recordState', 'CAMERA_INFO.videoRecordTime',
#              'GIMBAL.pitch', 'GIMBAL.roll', 'GIMBAL.yaw']]
#
# print(df.head(10))
#
# print('#index를 0부터 다시 부여함/첫번째 데이터에 대한 처리를 다르게 하기 위해#########')
# df = df.reset_index(drop=True)
# print(df.head(10))
#
# print('#필요한 변수 생성########################################################')
# starting_time_str = df.at[0, 'CUSTOM.updateTime']
# starting_time_obj = datetime.datetime.strptime(starting_time_str, '%Y/%m/%d %H:%M:%S.%f')
# distance_accumulate = 0
# diff_yaw_accumulate = 0
# diff_gim_yaw_accumulate = 0
#
# print('#EO 파일 저장을 위한 pandas dataframe 생성################################')
# image_info = {"imageID":[],"latitude":[], "longitude":[], "altitude":[], "roll":[], "pitch":[], "yaw":[]}
# print(image_info)
# df_image_info = pd.DataFrame(image_info)