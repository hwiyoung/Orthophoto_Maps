import numpy as np
import math

def calibrate(roll, pitch, yaw, R_CB):
    R_rpy = A2R_RPY(roll, pitch, yaw)
    R_opk = R_rpy.dot(R_CB)

    return R2A_OPK(R_opk)


def A2R_RPY(r, p, y):
    om, ph, kp = p, r, -y

    Rot_x = np.array([[1., 0., 0.], [0., math.cos(om), -math.sin(om)], [0., math.sin(om), math.cos(om)]], dtype=float)
    Rot_y = np.array([[math.cos(ph), 0, math.sin(ph)], [0, 1, 0], [-math.sin(ph), 0, math.cos(ph)]], dtype=float)
    Rot_z = np.array([[math.cos(kp), -math.sin(kp), 0], [math.sin(kp), math.cos(kp), 0], [0, 0, 1]], dtype=float)

    Rot_rpy = np.linalg.multi_dot([Rot_y, Rot_z, Rot_x])
    return Rot_rpy


def R2A_OPK(Rot_opk):
    s_ph = Rot_opk[0, 2]
    temp = (1 + s_ph) * (1 - s_ph)
    c_ph1 = math.sqrt(temp)
    c_ph2 = -math.sqrt(temp)

    omega = math.atan2(-Rot_opk[1, 2], Rot_opk[2, 2])
    phi = math.atan2(s_ph, c_ph1)
    kappa = math.atan2(-Rot_opk[0, 1], Rot_opk[0, 0])

    return omega, phi, kappa
