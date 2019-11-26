import numpy as np
from copy import copy


def rot_mat(theta):
    return np.array([[np.cos(theta), np.sin(theta)],
                     [-np.sin(theta), np.cos(theta)]])


def rpy_to_opk(rpy):
    for i in range(len(rpy)):
        x = copy(rpy[i, 0:2])
        x[0] = 90 + rpy[i, 1]
        x[1] = rpy[i, 0]
        # print("x :", x)
        omega_phi = np.dot(rot_mat(rpy[i, 2] * np.pi / 180), x.reshape(2, 1))
        kappa = -rpy[i, 2]
        print("omega: ", float(omega_phi[0]),
              "phi: ", float(omega_phi[1]),
              "kappa: ", kappa)


rpy = np.array([[0, -40.1, -167.5],     # -43.78917451	18.02675188	163.018622
                [0, -29.7, 133.7],      # -52.27467493	-21.30461996	-163.4304214
                [0,	-52.2, 158.2],      # -54.55762791	-1.306542383	-178.5022116
                [0, -31.1, 179.8],      # -56.45022792	8.58366281	174.8241069
                [0, -27.2, -173.3]])    # -55.68315463	10.91059053	173.3515329

rpy_to_opk(rpy)
