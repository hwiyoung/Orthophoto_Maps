import socket
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


def load_log(file_path):
    df = pd.read_csv(file_path + '.csv', low_memory=False)
    df = df[df['CAMERA_INFO.recordState'] == 'Starting']
    # df = df[['CUSTOM.updateTime', 'OSD.longitude', 'OSD.latitude', 'OSD.height [m]',
    #          'OSD.roll', 'OSD.pitch', 'OSD.yaw',
    #          'GIMBAL.roll', 'GIMBAL.pitch', 'GIMBAL.yaw']]
    df_time = df[['CUSTOM.updateTime']]
    df_time_np = df_time.to_numpy()
    # df = df[['OSD.longitude', 'OSD.latitude', 'OSD.height [m]',
    #          'OSD.roll', 'OSD.pitch', 'OSD.yaw',
    #          'GIMBAL.roll', 'GIMBAL.pitch', 'GIMBAL.yaw']]
    df = df[['OSD.longitude', 'OSD.latitude', 'OSD.height [m]',
             'GIMBAL.roll', 'GIMBAL.pitch', 'GIMBAL.yaw']]
    df_np = df.to_numpy()

    return df_time_np, df_np


def load_io(file_path):
    # model = cv2.VideoCapture(filePath + '.MOV')
    model = 'FC6310R'

    # model_name, sensor_width(mm), focal_length(mm)
    io_list = np.array([['FC6310R', 13.2, 8.8],  # Phantom4RTK
                        ['FC220', 6.3, 4.3],  # Mavic
                        ['FC6520', 17.3, 15]]  # Inspire2
                       )

    sensor_width_mm = float(io_list[io_list[:, 0] == model][0, 1])
    focal_length_mm = float(io_list[io_list[:, 0] == model][0, 2])

    return sensor_width_mm, focal_length_mm


def create_bbox_json(object_id, object_type, boundary):
    """
    Create json of boundary box
    :param object_id:
    :param object_type:
    :param boundary:
    :return: list of information of boundary box ... json array
    """
    # bbox_info = [x    x
    #     {
    #         "object_id": object_id,
    #         "object_type": object_type,
    #         "boundary": "POLYGON ((%f %f, %f %f, %f %f, %f %f, %f %f))"
    #                      % (boundary[0, 0], boundary[1, 0],
    #                         boundary[0, 1], boundary[1, 1],
    #                         boundary[0, 2], boundary[1, 2],
    #                         boundary[0, 3], boundary[1, 3],
    #                         boundary[0, 0], boundary[1, 0])
    #     }
    # ]
    bbox_info = {
        "objects_id": object_id,     # uuid
        "boundary": "POLYGON ((%f %f, %f %f, %f %f, %f %f, %f %f))"
                    % (boundary[0, 0], boundary[1, 0],
                       boundary[0, 1], boundary[1, 1],
                       boundary[0, 2], boundary[1, 2],
                       boundary[0, 3], boundary[1, 3],
                       boundary[0, 0], boundary[1, 0]),
        "objects_type": object_type
    }

    return bbox_info

def send_bbox(sock, data, logdata, addr):
    datalen = 65508  # UDP 는 byte[] 배열로 전송, 최대 크기는 65508
    start = 0
    end = start + datalen - 1
    totalsize = 0
    cnt = 0

    # Sending packet info (header(start)(5), uuid(16), width(2), height(2), data)
    header = pack('5s', b'start')
    # uuid_ = uuid.uuid4().bytes # The UUID as a 16-byte string (containing the six integer fields in big-endian byte order).

    fnumber = pack('>H', frame_number)
    ftime = pack('>H', frame_time)

    fwidth = pack('>H', frame_width)  # H : uint16
    fheight = pack('>H', frame_height)

    time = logdata[0].encode()
    lat = logdata[1] * 1000000
    lon = logdata[2] * 1000000
    hei = logdata[3] * 10
    alt = logdata[4] * 10
    xSpd = logdata[5] * 10
    ySpd = logdata[6] * 10
    zSpd = logdata[7] * 10
    roll = logdata[8] * 10
    pitch = logdata[9] * 10
    yaw = logdata[10] * 10
    GBroll = logdata[11] * 10
    GBpitch = logdata[12] * 10
    GByaw = logdata[13] * 10

    log_ = pack('>23sIIHHbbbhhhhhh', time, int(lat), int(lon), int(hei), int(alt),
                int(xSpd), int(ySpd), int(zSpd), int(roll), int(pitch), int(yaw),
                int(GBroll), int(GBpitch), int(GByaw))
    # s: string
    # I: uint32
    # H: uint16
    # b: int8
    # h: int16

    # data = header + uuid_ + fwidth + fheight + data + log_   # 5+16+2+2+len(data)_log(50)
    data = header + fnumber + ftime + fwidth + fheight + data + log_  # 5+2+2+2+2+2+len(data)_log(50)

    while totalsize < len(data):
        sentsize = sock.send(data[start:end])
        # sentsize = sock.sendto(data[start:end], addr)
        if not sentsize: return None
        start = start + sentsize
        end = start + datalen - 1
        totalsize += sentsize
        cnt += 1

    return cnt


def read_memmap(rows, cols, ch):
    print("memmap read")
    np_image = np.memmap('frame_image', mode='r', shape=(rows, cols, ch), dtype=np.uint8)
    print('shape :', np_image.shape, 'type:', np_image.dtype)
    # cv2.imshow('Test', np_image)
    # cv2.waitKey(0)
    return np_image


if __name__ == '__main__':
    # For test
    R_CB = np.array(
        [[0.990635238726878, 0.135295782209043, 0.0183541578119133],
         [-0.135993334134149, 0.989711806459606, 0.0444561944563446],
         [-0.0121505910810649, -0.0465359159242159, 0.998842716179817]], dtype=float)

    data_store = 'C:/innomap_real/dataStore/'     # Have to be defined already
    # data_store = './'  # Have to be defined already
    project_path = '02_Jeonju/'  # It has to receive from client, or THIS SERVER designates in PATH step

    while True:
        ################################
        # Server for path, frame, bbox #
        ################################
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 57810))

        #########################
        # Client for map viewer #
        #########################
        s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        dest = ("localhost", 57820)
        print("binding...")

        header = s.recv(4)
        if header == b'PATH':  # header | length | b_fname
            length_path = s.recv(4)
            b_filename = s.recv(int(length_path.decode()))  # type: bytes
            filename = b_filename[:-4].decode()  # type: str .MOV
            uid = '525c671317165f77b0d31543634093aba'

            # project_path = filename.split('/')[-1] + '/'

            #################
            # Extract EO/IO #
            #################
            # EO - lon(deg), lat(deg), hei(m), gimbal.roll(deg), gimbal.pitch(deg), gimbal.yaw(deg)
            update_time, log = load_log(filename)

            prev_time = float(update_time[0, 0][17:])
            first_image = True

            # IO - sensor_width(mm), focal_length(mm)
            sensor_width, focal_length = load_io(filename)  # type: float, float
            print(sensor_width, focal_length)

        elif header == b'FRAM':  # header | frame_number | rows | cols
            frame_number = int(s.recv(4).decode())
            b_cols = s.recv(4)
            b_rows = s.recv(4)
            cols = int(b_cols.decode())  # type: int
            rows = int(b_rows.decode())  # type: int

            ####################################
            # memmap ... return to numpy array #
            ####################################
            time.sleep(1)
            np_image = read_memmap(rows, cols, 3)

            bbox_total = []

            ################################
            # Sync log w.r.t. frame_number #
            ################################
            eo = log[int((frame_number - 1) / 3 + 1), :]
            curr_time = float(update_time[int((frame_number - 1) / 3 + 1), 0][17:])
            # curr_time = 45
            # first_image = False

            if (curr_time - prev_time) < 3.0 or first_image:
                prev_time = curr_time
                first_image = False

                tm_eo = convertCoordinateSystem(eo, epsg=3857)
                # System calibration using gimbal angle
                eo[3] = eo[3] * np.pi / 180
                eo[4] = (eo[4] + 90) * np.pi / 180
                eo[5] = -eo[5] * np.pi / 180
                R_GC = Rot3D(tm_eo)
                R_CG = R_GC.transpose()

                # OPK = calibrate(eo[3], eo[4], eo[5], R_CB)
                # eo[3] = OPK[0]
                # eo[4] = OPK[1]
                # eo[5] = OPK[2]
                print('Easting | Northing | Height | Omega | Phi | Kappa')
                print(eo)

                ###########################
                # Rectify the given image #
                ###########################
                path_orthophoto, bbox_wkt = rectify(data_store, project_path, img=np_image,
                                          rectified_fname='Rectified' + str(frame_number), eo=tm_eo,
                                          ground_height=0, sensor_width=sensor_width, focal_length=focal_length)
            else:
                prev_time = curr_time
                continue

        elif header == b'INFE':  # header(4) | frame_number(4) | length(4) | ID(32) | Type(4) | boundary box
            frame_number = int(s.recv(4).decode())
            length_infe = s.recv(4)
            # TODO: Need to be assigned
            object_id = '85f46f4c-99d9-40da-880e-b943621f32c0'
            object_type = 0
            # object_id = s.recv(32)
            # object_type = int(s.recv(4).decode())
            ############################

            b_bbox = s.recv(int(length_infe.decode()))  # type: bytes
            # b_bbox = s.recv(int(length.decode())-32-4)  # type: bytes
            bbox = json.loads(b_bbox.decode())
            # # LL | UL | UR | LR - 2x4
            # bbox_px = np.array([[bbox[0][0], bbox[1][0], bbox[2][0], bbox[3][0]],
            #                     [bbox[0][1], bbox[1][1], bbox[2][1], bbox[3][1]]])

            bbox_px = np.array([bbox[0][0], bbox[0][1]]).reshape(2, 1)
            for i in range(1, len(bbox)):
                bbox_tmp = np.array([bbox[i][0], bbox[i][1]]).reshape(2, 1)
                bbox_px = np.append(bbox_px, bbox_tmp, 1)
            print(bbox_px)

            # Convert pixel coordinate system to camera coordinate system
            # input params unit: px, px, px, mm/px, mm
            pixel_size = sensor_width / cols
            bbox_camera = pcs2ccs(bbox_px, rows, cols, pixel_size, focal_length)  # shape: 3(x, y, z) x points

            # Project camera coordinates to ground coordinates
            # input params unit: mm, _, _, m
            bbox_world = projection(bbox_camera, tm_eo, R_CG, 0)  # shape: 2(x, y) x points | np.array

            # Create boundary box in type of json for each inference data
            bbox_info = create_bbox_json(object_id, object_type, bbox_world)  # dictionary
            bbox_total.append(bbox_info)
            print(bbox_total)

        elif header == b'DONE':
            objects_info = {
                "uid": uid,     # String
                "path": path_orthophoto,  # String
                "frame_number": frame_number,  # Number
                "position": [tm_eo[0], tm_eo[1]],  # Array
                "bbox": bbox_wkt,  # WKT ... String
                "objects": bbox_total  # Array includes Object
            }
            print(objects_info)
            # https://stackoverflow.com/questions/4547274/convert-a-python-dict-to-a-string-and-back
            str_objects_info = json.dumps(objects_info)

            #############################################
            # Send object information to web map viewer #
            #############################################
            fmt = '<4si' + str(len(str_objects_info)) + 's'
            data_to_send = pack(fmt, b"MAPP", len(str_objects_info), str_objects_info.encode())
            # header_length = pack('<4si', b"MAPP", len(str_objects_info))
            # body = pack('<' + str(len(str_objects_info)) + 's', str_objects_info.encode())
            # data_to_send = header_length + body
            s1.sendto(data_to_send, dest)

            # # s: string
            # # I: uint32
            # # H: uint16
            # # b: int8
            # # h: int16
            #
            # s1.sendto(b"MAPP", dest)  # Header
            # s1.sendto(str(len(str_objects_info)).encode(), dest)  # Length
            # s1.sendto(str_objects_info.encode(), dest)  # json

            bbox_total = []

        else:
            print('None')

        print("Done")
