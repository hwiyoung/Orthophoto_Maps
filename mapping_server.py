import socket
import os
import cv2
import time
import numpy as np
from struct import *
import pandas as pd
import json
from ortho_func.system_calibration import calibrate
from ortho_func.Orthophoto import rectify
from ortho_func.EoData import convertCoordinateSystem, Rot3D
from ortho_func.Boundary import pcs2ccs, projection
import subprocess
from copy import copy

data_store = 'C:/innomap_real/dataStore/'  # Have to be defined already
# data_store = '../map_demo/dataStore/'
bbox_total = []
frame_number_check = -1
frame_rate = 60

#########################
# Client for map viewer #
#########################
s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dest = ("localhost", 57820)
print("binding...")


def rot_2d(theta):
    return np.array([[np.cos(theta), np.sin(theta)],
                     [-np.sin(theta), np.cos(theta)]])


def rpy_to_opk(rpy):
    x = copy(rpy[0:2])
    x[0] = 90 + rpy[1]
    x[1] = rpy[0]
    # print("x :", x)
    omega_phi = np.dot(rot_2d(rpy[2] * np.pi / 180), x.reshape(2, 1))
    kappa = -rpy[2]
    # print("omega: ", float(omega_phi[0]),
    #       "phi: ", float(omega_phi[1]),
    #       "kappa: ", kappa)
    return np.array([float(omega_phi[0]), float(omega_phi[1]), kappa])


def load_log(file_path):
    df = pd.read_csv(file_path, low_memory=False)
    df = df[df['CAMERA_INFO.recordState'] == 'Starting']
    df = df[['OSD.longitude', 'OSD.latitude', 'OSD.height [m]',
             'GIMBAL.roll', 'GIMBAL.pitch', 'GIMBAL.yaw']]

    global log_eo
    log_eo = df.to_numpy()


def load_io(file_path):
    exe = "exiftool.exe"
    process = subprocess.Popen([exe, file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    metadata = process.stdout.read().decode()
    model_field = metadata.find('Model')
    model_name = metadata[model_field + 34:model_field + 34 + 7]
    model = model_name.rstrip()

    # model_name, sensor_width(mm), focal_length(mm)
    io_list = np.array([['FC6310R', 13.2, 8.8],  # Phantom4RTK
                        ['FC220', 6.3, 4.3],  # Mavic
                        ['FC6520', 17.3, 15]]  # Inspire2
                       )

    sensor_width_mm = float(io_list[io_list[:, 0] == model][0, 1])
    focal_length_mm = float(io_list[io_list[:, 0] == model][0, 2])

    global io
    io = [sensor_width_mm, focal_length_mm]


def create_bbox_json(frame_number, object_id, object_type, boundary):
    """
    Create json of boundary box
    :param object_id:
    :param object_type:
    :param boundary:
    :return: list of information of boundary box ... json array
    """
    bbox_info = {
        "frame_number": frame_number,
        "objects_id": object_id,  # uuid
        "objects_type": object_type
    }

    wkt_info = "POLYGON (("
    for i in range(boundary.shape[1]):
        wkt_info = wkt_info + str(boundary[0, i]) + " " + str(boundary[1, i]) + ", "
    wkt_info = wkt_info + str(boundary[0, 0]) + " " + str(boundary[1, 0]) + "))"
    # print("wkt_info: ", wkt_info)

    # for i in range(boundary.shape[1]):
    #     boundary_wkt = {
    #         "boundary": "POLYGON ((%f %f, %f %f, %f %f, %f %f, %f %f))"
    #                     % (boundary[0, 0], boundary[1, 0],
    #                        boundary[0, 1], boundary[1, 1],
    #                        boundary[0, 2], boundary[1, 2],
    #                        boundary[0, 3], boundary[1, 3],
    #                        boundary[0, 0], boundary[1, 0]),
    #     }
    #
    bbox_info["boundary"] = wkt_info
    # print("bbox_info: " ,bbox_info)

    return bbox_info

def PATH(path, video_id):
    print(path, video_id)
    file_path_wo_ext = path[:-4]
    # project_path = file_path_wo_ext.split('/')[-1] + '/'
    global uuid
    uuid = video_id.rstrip()
    if not(os.path.isdir(data_store + uuid)):
        os.mkdir(data_store + uuid)

    load_log(file_path_wo_ext + ".csv")  # Extract EO
    load_io(path)   # Extract IO

def FRAM(np_image, frame_number):
    ################################
    # Sync log w.r.t. frame_number #
    ################################
    global frame_number_check
    # print(frame_number_check)
    # Check the frame number is changed w.r.t each 90 frame
    if int(frame_number / frame_rate) == frame_number_check:
        return

    frame_number_check = int(frame_number / frame_rate)
    try:
        eo = log_eo[int(frame_number / 3), :]
        print(eo)
    except IndexError:
        eo = log_eo[-1, :]
        print(eo)

    # if eo[4] > -30:
    #     return

    tm_eo = convertCoordinateSystem(eo, epsg=3857)
    # System calibration using gimbal angle
    opk = rpy_to_opk(eo[3:])
    tm_eo[3:] = opk * np.pi / 180
    #print('Easting | Northing | Height | Omega | Phi | Kappa')
    # print(tm_eo)

    ###########################
    # Rectify the given image #
    ###########################
    path_orthophoto, bbox_wkt = rectify(data_store, uuid + '/', img=np_image,
                                        rectified_fname='Rectified_' + str(frame_number), eo=tm_eo,
                                        ground_height=0, sensor_width=io[0], focal_length=io[1])

    # path_orthophoto, bbox_wkt = rectify(data_store, uuid + '/', img=np_image,
    #                                     rectified_fname='Rectified_' + str(frame_number) + "_" + str(eo[4]), eo=tm_eo,
    #                                     ground_height=0, sensor_width=io[0], focal_length=io[1])

    ortho_json = {
        "uid": uuid,  # String
        "path": path_orthophoto,  # String
        "frame_number": frame_number,  # Number
        "position": [tm_eo[0], tm_eo[1]],  # Array
        "bbox": bbox_wkt,  # WKT ... String
    }

    bbox_to_add = []
    count = 0
    for i in range(len(bbox_total)):
        if bbox_total[i]["frame_number"] == ortho_json["frame_number"]:
            bbox_to_add.append(bbox_total[i])
            count = count + 1

    del bbox_total[:(count - 1)]

    ortho_json["objects"] = bbox_to_add
    #print(ortho_json)
    # https://stackoverflow.com/questions/4547274/convert-a-python-dict-to-a-string-and-back
    str_objects_info = json.dumps(ortho_json)

    #############################################
    # Send object information to web map viewer #
    #############################################
    fmt = '<4si' + str(len(str_objects_info)) + 's'  # s: string, i: int
    data_to_send = pack(fmt, b"MAPP", len(str_objects_info), str_objects_info.encode())
    s1.sendto(data_to_send, dest)


def INFE(infe_res, cols, rows):
    if len(infe_res) == 0:
        return
    # infe_res_json = json.loads(infe_res)
    infe_res_json = infe_res
    #print(infe_res_json)
    #print(len(infe_res_json))
    frame_number = infe_res_json[0]["frame_number"]

    try:
        eo = log_eo[int(frame_number / 3), :]
    except IndexError:
        eo = log_eo[-1, :]

    tm_eo = convertCoordinateSystem(eo, epsg=3857)
    # System calibration using gimbal angle
    opk = rpy_to_opk(eo[3:])
    tm_eo[3:] = opk * np.pi / 180

    R_GC = Rot3D(tm_eo)
    R_CG = R_GC.transpose()
    # print('Easting | Northing | Height | Omega | Phi | Kappa')
    # print(tm_eo)

    for i in range(len(infe_res_json)):
        object_id = infe_res_json[i]["uid"]
        object_type = infe_res_json[i]["type"]
        bbox = infe_res_json[i]["objects"]
        bbox_px = np.array(bbox).transpose()
        # print(bbox_px)

        # Convert pixel coordinate system to camera coordinate system
        # input params unit: px, px, px, mm/px, mm
        pixel_size = io[0] / cols
        bbox_camera = pcs2ccs(bbox_px, rows, cols, pixel_size, io[1])  # shape: 3(x, y, z) x points

        # Project camera coordinates to ground coordinates
        # input params unit: mm, _, _, m
        bbox_world = projection(bbox_camera, tm_eo, R_CG, 0)  # shape: 2(x, y) x points | np.array
        # print(bbox_world.shape)

        # Create boundary box in type of json for each inference data
        bbox_info = create_bbox_json(frame_number, object_id, object_type, bbox_world)  # dictionary
        bbox_total.append(bbox_info)
    #print(bbox_total)


# if __name__ == '__main__':
#     while True:
#         ################################
#         # Server for path, frame, bbox #
#         ################################
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         s.bind(('localhost', 57810))
#
#         #########################
#         # Client for map viewer #
#         #########################
#         s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         dest = ("localhost", 57820)
#         print("binding...")
#
#         data, addr = s.recvfrom(200)
#
#         header = data[:4]
#         if header == b'PATH':  # header | length | path | video_id(33 for test)
#             print("Received")
#             length_path = int.from_bytes(data[4:8], "little")
#             path = data[8:8 + length_path].decode()
#             video_id = data[8 + length_path:].decode()
#
#             file_path_wo_ext = path[:-4]
#             # project_path = file_path_wo_ext.split('/')[-1] + '/'
#
#             global uuid
#             uuid = video_id
#             if not (os.path.isdir(data_store + uuid)):
#                 os.mkdir(data_store + uuid)
#
#             load_log(path)  # Extract EO
#             load_io(file_path_wo_ext + ".MOV")  # Extract IO
#
#             # e.g. for an inference result for each frame
#             infe_res = [
#             ]
#
#             vidcap = cv2.VideoCapture(file_path_wo_ext + ".MOV")
#             count = 0
#             while vidcap.isOpened():
#                 ret, np_image = vidcap.read()
#                 rows = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#                 cols = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
#
#                 if int(vidcap.get(1)) % frame_rate == 1:
#                     frame_number = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
#                     # mm = np.memmap('frame_image', mode='w+', shape=np_image.shape, dtype=np_image.dtype)
#                     # mm[:] = np_image[:]
#                     # mm.flush()
#                     # del mm
#                     # print(np_image.shape)
#
#                     INFE(infe_res, cols, rows)
#                     FRAM(np_image, frame_number)
#
#                     # json_to_map_server(np_image, frame_number, infe_res, cols, rows)
#
#             print("Hello")
