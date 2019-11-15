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
    df = df[['OSD.longitude', 'OSD.latitude', 'OSD.height [m]',
             'OSD.roll', 'OSD.pitch', 'OSD.yaw',
             'GIMBAL.roll', 'GIMBAL.pitch', 'GIMBAL.yaw']]
    df_np = df.to_numpy()

    return df_np


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
    :return: list of information of boundary box
    """
    bbox_info = [
        {
            "object_id": object_id,
            "object_type": object_type,
            "boundary": "POLYGON ((%f %f, %f %f, %f %f, %f %f, %f %f))"
                         % (boundary[0, 0], boundary[1, 0],
                            boundary[0, 1], boundary[1, 1],
                            boundary[0, 2], boundary[1, 2],
                            boundary[0, 3], boundary[1, 3],
                            boundary[0, 0], boundary[1, 0])
        }
    ]

    return bbox_info


# def send_bbox(sock, data, logdata, addr):
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

    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 57810))
        print("binding...")

        header = s.recv(4)
        if header == b'PATH':  # header | length | b_fname
            length = s.recv(4)
            b_fname = s.recv(int(length.decode()))  # type: bytes
            fname = b_fname[:-4].decode()  # type: str

            #################
            # Extract EO/IO #
            #################
            # EO - lon(deg), lat(deg), hei(deg), roll(deg), pitch(deg), yaw(deg),
            #       gimbal.roll(deg), gimbal.pitch(deg), gimbal.yaw(deg)
            log = load_log(fname)
            # IO - sensor_width(mm), focal_length(mm)
            sensor_width, focal_length = load_io(fname)  # type: float, float
            print(sensor_width, focal_length)
        elif header == b'FRAM':  # header | frame_number | rows | cols
            frame_number = s.recv(4).decode()
            b_cols = s.recv(4)
            b_rows = s.recv(4)
            cols = int(b_cols.decode())  # type: int
            rows = int(b_rows.decode())  # type: int

            ####################################
            # memmap ... return to numpy array #
            ####################################
            time.sleep(1)
            np_image = read_memmap(int(rows), int(cols), 3)

            ################################
            # Sync log w.r.t. frame_number #
            ################################
            eo = log[int((int(frame_number) - 1) / 3 + 1), :]
            tm_eo = convertCoordinateSystem(eo, epsg=3857)
            eo[3] = eo[3] * np.pi / 180
            eo[4] = eo[4] * np.pi / 180
            eo[5] = eo[5] * np.pi / 180
            R_GC = Rot3D(tm_eo)
            R_CG = R_GC.transpose()

            # TODO: System calibration
            OPK = calibrate(eo[3], eo[4], eo[5], R_CB)
            eo[3] = OPK[0]
            eo[4] = OPK[1]
            eo[5] = OPK[2]
            print('Easting | Northing | Altitude | Omega | Phi | Kappa')
            print(eo)
            R = Rot3D(eo)

            ###########################
            # Rectify the given image #
            ###########################
            path_orthophoto = rectify(project_path='./', img=np_image, rectified_fname='Rectified' + frame_number,
                                     eo=tm_eo, ground_height=0, sensor_width=sensor_width, focal_length=focal_length)
        elif header == b'INFE':  # header | frame_number | length | boundary box
            frame_number = s.recv(4).decode()
            length = s.recv(4)
            # TODO: Need to be assigned
            object_id = 0
            object_type = 0
            ############################
            b_bbox = s.recv(int(length.decode()))  # type: bytes
            bbox = json.loads(b_bbox.decode())
            # LL | UL | UR | LR - 2x4
            bbox_px = np.array([[bbox[0][0], bbox[1][0], bbox[2][0], bbox[3][0]],
                                [bbox[0][1], bbox[1][1], bbox[2][1], bbox[3][1]]])
            print(bbox_px)
        else:
            print('None')

        # Assume that for each sending from inference server, only one object information is received
        # It should be modified later ... like adding for loop from pcs2ccs to create_bbox_json
        # When applying for loop, appending dictionary to list
        # https://stackoverflow.com/questions/5244810/python-appending-a-dictionary-to-a-list-i-see-a-pointer-like-behavior

        # Convert pixel coordinate system to camera coordinate system
        # input params unit: px, px, px, mm/px, mm
        bbox_camera = pcs2ccs(bbox_px, rows, cols, sensor_width, focal_length)  # shape: 3(x, y, z) x points

        # Project camera coordinates to ground coordinates
        # input params unit: mm, _, _, m
        boundary = projection(bbox_camera, tm_eo, R_CG, 0)  # shape: 2(x, y) x points

        bbox_info = create_bbox_json(object_id, object_type, boundary)

        object_info = {
            "path": path_orthophoto,
            "frame_number": frame_number,
            "bbox": bbox_info
        }
        # https://stackoverflow.com/questions/4547274/convert-a-python-dict-to-a-string-and-back
        str_object_info = json.dumps(object_info)

        #############################################
        # Send object information to web map viewer #
        #############################################
        s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        dest = ("localhost", 57820)

        s1.sendto(b"MAPP", dest)  # Header
        s1.sendto(str(len(str_object_info)).encode(), dest)     # Length
        s1.sendto(str_object_info.encode(), dest)   # json

        print("Done")
