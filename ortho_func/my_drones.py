from abc import *
import numpy as np


class BaseDrone(metaclass=ABCMeta):
    polling_config = {
        'asked_health_check': False,
        'asked_sim': False,
        'checklist_result': None,
        'polling_time': 0.5,
        'timeout': 10
    }

    # @abstractmethod
    def calibrate_initial_eo(self):
        pass


class Mavic(BaseDrone):
    def __init__(self):
        self.drone_params = {
            'model': 'FC220',
            "sensor_width": 6.3,    # unit: mm
            'focal_length': 4.3,    # unit: mm
            'gsd': 'auto',
            "R_CB": np.array(
                [[0.997391604272809, -0.0193033671589004, -0.0695511879297631],
                 [0.0115400822765142, 0.993826984996126, -0.110339251377565],
                 [0.0712517664845147, 0.109248816514592, 0.991457453380122]], dtype=float)
        }


class Phantom4RTK(BaseDrone):
    def __init__(self):
        self.ipod_params = {
            'model': 'FC6310R',
            "sensor_width": 13.2,   # unit: mm
            'focal_length': 8.8,    # unit: mm
            'gsd': 'auto',
            "R_CB": np.array(
                [[0.992103011532570, -0.0478682839576757, -0.115932057253170],
                 [0.0636038625107261, 0.988653550290218, 0.136083452970098],
                 [0.108102558627082, -0.142382530141501, 0.983890772356761]], dtype=float)
        }


class Inspire2(BaseDrone):
    def __init__(self):
        self.ipod_params = {
            'model': 'FC6520',
            "sensor_width": 17.3,   # unit: mm
            'focal_length': 15,     # unit: mm
            'gsd': 'auto',
            "R_CB": np.array(
                [[0.992103011532570, -0.0478682839576757, -0.115932057253170],
                 [0.0636038625107261, 0.988653550290218, 0.136083452970098],
                 [0.108102558627082, -0.142382530141501, 0.983890772356761]], dtype=float)
        }
