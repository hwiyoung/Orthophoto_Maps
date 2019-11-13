import socket
import cv2
import time
import numpy as np
from struct import *
import pandas as pd

def loadcsv(csv_file, fps):
    # print('********** Read csv file of drone log **********')
    df = pd.read_csv(csv_file, low_memory=False)

    # print('********** Extract rows on recording **********')
    df = df[df['CAMERA_INFO.recordState'] == 'Starting']

    # print('********** Extract columns on need **********')
    df = df[['CUSTOM.updateTime', 'OSD.latitude', 'OSD.longitude',
             'OSD.height [m]', 'OSD.altitude [m]',
             'OSD.xSpeed [m/s]', 'OSD.ySpeed [m/s]', 'OSD.zSpeed [m/s]',
             'OSD.roll', 'OSD.pitch', 'OSD.yaw',
             'GIMBAL.pitch', 'GIMBAL.roll', 'GIMBAL.yaw']]

    # Convert UTC to KST
    df_np = df.to_numpy()
    for i in range(df_np[:, 0].shape[0]):
        hours_edit = str(int(df_np[i, 0][11:13]) + 9)   # UTC to KST
        time_edit = df_np[i, 0][0:11] + hours_edit + df_np[i, 0][13:len(df_np[i, 0])]
        df_np[i, 0] = time_edit

    # Synchronize the video with the log
    freq_diff = int(fps / 10)  # fps in video: e.g. 30, fps in log: 10 ... freq: 3
    logs = np.empty((df_np.shape[0] * freq_diff, df_np.shape[1]), dtype=object)
    for i in range(df_np.shape[0]):
        logs[freq_diff*i:freq_diff*i+freq_diff][:] = df_np[i][:].reshape(1, df_np.shape[1])

    return logs


def sendall(sock, data, logdata, addr):
    datalen = 65508     # UDP 는 byte[] 배열로 전송, 최대 크기는 65508
    start = 0
    end = start + datalen - 1
    totalsize = 0
    cnt = 0

    # Sending packet info (header(start)(5), uuid(16), width(2), height(2), data)
    header = pack('5s', b'start')
    # uuid_ = uuid.uuid4().bytes # The UUID as a 16-byte string (containing the six integer fields in big-endian byte order).

    fnumber = pack('>H', frame_number)
    ftime = pack('>H', frame_time)

    fwidth = pack('>H', frame_width)   # H : uint16
    fheight = pack('>H', frame_height)

    time    = logdata[0].encode()
    lat     = logdata[1] * 1000000
    lon     = logdata[2] * 1000000
    hei     = logdata[3] * 10
    alt     = logdata[4] * 10
    xSpd    = logdata[5] * 10
    ySpd    = logdata[6] * 10
    zSpd    = logdata[7] * 10
    roll    = logdata[8] * 10
    pitch   = logdata[9] * 10
    yaw     = logdata[10] * 10
    GBroll  = logdata[11] * 10
    GBpitch = logdata[12] * 10
    GByaw   = logdata[13] * 10

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

    # chksum = crc8.crc8()
    # chksum.update(data)
    # chksum_byte = pack('<h', chksum._sum)
    # data = data + chksum_byte

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
    np_image = np.memmap('frame_image.dat', mode='r', shape=(rows, cols, ch), dtype=np.uint8)
    print('shape :', np_image.shape, 'type:', np_image.dtype)
    # cv2.imshow('Test', np_image)
    # cv2.waitKey(0)
    return np_image


if __name__ == '__main__':
    # read_memmap(2160, 3840, 3)
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 57810))
        print("binding...")

        rows = 0
        cols = 0

        head = s.recv(4)
        if head == b'path':
            length = s.recv(4)
            body = s.recv(int(length))
            csv = body.decode()
            print(csv)
        elif head == b'fram':
            frameNumber = s.recv(4)
            b_rows = s.recv(4)
            b_cols = s.recv(4)
            rows = b_rows.decode()
            cols = b_cols.decode()
            print(frameNumber.decode(), rows, cols)
        else:
            print('None')

        time.sleep(1)
        np_image = read_memmap(int(rows), int(cols), 3)
        cv2.imshow('Test', np_image)
        cv2.waitKey(0)


        # vidcap = cv2.VideoCapture(video_path)
        # fps = int(vidcap.get(cv2.CAP_PROP_FPS) + 0.5)
        # log = loadcsv(video_path[:-4] + '.csv', fps)  # UDP 로 받을 경로   .MOV path[:-4] +'.csv'
        #
        # frame_width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # frame_height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        #
        # success = True
        # count = 0
        # total_time = time.time()
        #
        # while success:
        #
        #     vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*(1/fps)*1000))
        #
        #     frame_number = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
        #     frame_time = int(vidcap.get(cv2.CAP_PROP_POS_MSEC))
        #
        #     start = time.time()
        #     success, image = vidcap.read()
        #     if not success:
        #         break
        #     strimg = image.tostring()
        #     senttime = time.time()
        #     cnt = sendall(s1, strimg, log[count][:], dest)
        #     count += 1
        #     print("1 frame sent", time.time()-senttime, cnt)
        #
        # print("total: ", time.time()-total_time)
        # s_log.close()
