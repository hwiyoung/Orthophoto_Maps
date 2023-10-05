config = {
    # Params for files
    "image_path": "/home/user/hdd/LDM_Jeju/02_211113-14_Pyoseon/211113_Pyoseon/Raw_test/",
    "extension": "JPG",
    "metadata_in_image": False,     # Whether to read metadata in an image itself(True) or from an external file(False)
    "output_path": "/home/user/hdd/LDM_Jeju/02_211113-14_Pyoseon/211113_Pyoseon/Orthophotos_test/",

    # Params for georeferencing
    "no_images_process": 5,         # Number of images to perform local bundle adjustment. At least 3
    "types": "nonfixed-estimated",  # Types of setting accuracy (fixed, nonfixed-initial, nonfixed-estimated)
    "matching_accuracy": 1,         # Image matching accuracy (Highest = 0, High = 1, Medium = 2, Low = 4, Lowest = 8)
                                    # https://www.agisoft.com/forum/index.php?topic=11697.msg52465#msg52465
    "no_gpus": 1,                   # Number of GPUs to process in Metashape
    "sys_cal": "KAU",               # Types of system calibration w.r.t. drones (KAU, DJI)

    # Params for handling error
    "diff_init_esti": 10,           # Difference between location of initial and estimated in m
    # "std_init_esti": -,             # The standard deviation of bundle adjustment
    "diff_before_current": 10,      # Difference between location of just before and current photo in m

    # Params for CSF
    "rigidness": 3,                 # Scenes type of the point clouds (1: Mountain area with dense vegetation, 2: complex scenes, 3: flat terrain with high-rise buildings_
    "slope_smooth": False,          # Slope post processing for disconnected terrain
    "cloth_resolution": 0.5,        # The grid size (the unit is same as the unit of pointclouds) of cloth
    "iterations": 500,              # The maximum iteration times of terrain simulation. 500 is enough for most of scenes.
    "class_threshold": 0.5,         # The distances between points and the simulated terrain. 0.5 is adapted to most of scenes.
    "time_step": 0.65,

    # Params for mapping
    "epsg": 5186,                   # Target coordinate system in EPSG
    "gsd": 0.1,                     # Target ground sampling distance in m. Set to 0 to disable
    "dem": "plane",                 # Types of projection plane for indirect mapping (dsm, dtm, plane)
    "ground_height": 0.0            # Target ground height in m
}
