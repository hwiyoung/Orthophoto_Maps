import socket
import os
import cv2
import time
import numpy as np
from struct import *
import pandas as pd
import json
from ortho_func.Orthophoto import rectify
from ortho_func.EoData import convertCoordinateSystem, Rot3D
from ortho_func.Boundary import pcs2ccs, projection
from copy import copy
from rdp import rdp

data_store = 'C:/innomap_real/dataStore/'  # Have to be defined already
bbox_total = []
frame_number_check_infe = -1
frame_number_check_fram = -1
frame_rate = 90
rdp_epsilon = 5

#########################
# Client for map viewer #
#########################
s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dest = ("localhost", 57820)
print("binding...")


def pldist(x0, x1, x2):
    return np.divide(np.linalg.norm(np.linalg.det([x2 - x1, x1 - x0])),
                     np.linalg.norm(x2 - x1))


def rdp_index(M, epsilon=0, dist=pldist):
    dmax = 0.0
    index = -1

    for i in range(1, M.shape[0]):
        d = dist(M[i], M[0], M[-1])
        if d > dmax:
            index = i
            dmax = d

    if dmax > epsilon:
        r1 = rdp_index(M[:index + 1], epsilon, dist)
        r2 = rdp_index(M[index:], epsilon, dist)
        return np.vstack((r1[:-1], r2))
    else:
        part_mask = np.empty_like(M, dtype=bool)
        part_mask.fill(False)
        part_mask[0] = True
        part_mask[-1] = True
        return part_mask


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
    df = pd.read_csv(file_path, low_memory=False, encoding='latin1')
    model = df['CAMERA_INFO.cameraType'][0]

    df = df[df['CAMERA_INFO.recordState'] == 'Starting']
    df = df[['OSD.longitude', 'OSD.latitude', 'OSD.height [m]',
             'GIMBAL.roll', 'GIMBAL.pitch', 'GIMBAL.yaw']]

    global log_eo
    log_eo = df.to_numpy()

    # model_name, sensor_width(mm), focal_length(mm)
    io_list = np.array([['FC6310', 13.2, 8.8],  # Phantom4RTK
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

    bbox_info["boundary"] = wkt_info
    # print("bbox_info: " ,bbox_info)

    return bbox_info

def PATH(path, video_id):
    print(path, video_id)
    file_path_wo_ext = path[:-4]
    global uuid
    uuid = video_id.rstrip()
    if not(os.path.isdir(data_store + uuid)):
        os.mkdir(data_store + uuid)

    load_log(file_path_wo_ext + ".csv")  # Extract EO, IO

def FRAM(np_image, frame_number):
    global frame_number_check_fram
    #############################################
    # Check the frame number is changed
    # w.r.t the designated frame_rate
    if int(frame_number / frame_rate) == frame_number_check_fram:
        return
    frame_number_check_fram = int(frame_number / frame_rate)
    #############################################

    #############################################
    # Sync log w.r.t. frame_number
    try:
        eo = log_eo[int(frame_number / 3), :]
        print(eo)
    except IndexError:
        eo = log_eo[-1, :]
        print(eo)
    #############################################

    if eo[4] > -29:
        tm_eo = convertCoordinateSystem(eo, epsg=3857)
        ortho_json = {
            "uid": uuid,  # String
            "path": "",  # String
            "frame_number": frame_number,  # Number
            "position": [tm_eo[0], tm_eo[1]],  # Array
            "bbox": "",  # WKT ... String
        }
        str_objects_info = json.dumps(ortho_json)
        print(str_objects_info)

        #############################################
        # Send object information to web map viewer #
        #############################################
        fmt = '<4si' + str(len(str_objects_info)) + 's'  # s: string, i: int
        data_to_send = pack(fmt, b"MAPP", len(str_objects_info), str_objects_info.encode())
        s1.sendto(data_to_send, dest)
        return

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
    # https://stackoverflow.com/questions/4547274/convert-a-python-dict-to-a-string-and-back
    str_objects_info = json.dumps(ortho_json)
    print(str_objects_info)

    #############################################
    # Send object information to web map viewer #
    #############################################
    fmt = '<4si' + str(len(str_objects_info)) + 's'  # s: string, i: int
    data_to_send = pack(fmt, b"MAPP", len(str_objects_info), str_objects_info.encode())
    s1.sendto(data_to_send, dest)


def INFE(infe_res, cols, rows):
    if len(infe_res) == 0:
        return
    infe_res_json = json.loads(infe_res)    # for application
    # infe_res_json = infe_res    # for test
    frame_number = infe_res_json[0]["frame_number"]

    #############################################
    # Check the frame number is changed
    # w.r.t the designated frame_rate
    global frame_number_check_infe
    if int(frame_number / frame_rate) == frame_number_check_infe:
        return
    frame_number_check_infe = int(frame_number / frame_rate)
    #############################################

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
        bbox = np.array(infe_res_json[i]["objects"])
        mask = rdp_index(bbox, epsilon=rdp_epsilon, dist=pldist)
        # print(bbox.shape[0], np.argwhere(mask==True).shape[0])
        bbox_px = bbox[mask[:, 0]].transpose()
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
#             # file_path_wo_ext = path
#             # project_path = file_path_wo_ext.split('/')[-1] + '/'
#
#             global uuid
#             uuid = video_id
#             if not (os.path.isdir(data_store + uuid)):
#                 os.mkdir(data_store + uuid)
#
#             load_log(path)  # Extract EO
#             # load_log(path + ".csv")  # Extract EO ... test
#
#             # e.g. for an inference result for each frame
#             # infe_res = [
#             # ]
#             with open("bbox2.json") as json_file:
#                 infe_res = json.load(json_file)
#
#             vidcap = cv2.VideoCapture(file_path_wo_ext + ".MOV")
#             count = 0
#             while vidcap.isOpened():
#                 ret, np_image = vidcap.read()
#                 rows = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#                 cols = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
#
#                 if int(vidcap.get(1) - 1) % frame_rate == 0:
#                     frame_number = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
#                     # mm = np.memmap('frame_image', mode='w+', shape=np_image.shape, dtype=np_image.dtype)
#                     # mm[:] = np_image[:]
#                     # mm.flush()
#                     # del mm
#                     # print(np_image.shape)
#
#                     INFE(infe_res, cols, rows)
#                     FRAM(np_image, frame_number)
#
#             print("Hello")
