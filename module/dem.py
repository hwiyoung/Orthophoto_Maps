# import laspy
# import CSF
import numpy as np
from scipy.interpolate import griddata
import time
import os
# import open3d as o3d


def boundary(image, IO, EO, ground_height):
    pos, R = EO["eo"], EO["rotation_matrix"]
    pixel_size, focal_length = IO["pixel_size"], IO["focal_length"]

    inverse_R = R.transpose()

    image_vertex = get_vertices(image, pixel_size, focal_length)  # shape: 3 x 4

    proj_coordinates = projection(image_vertex, pos, inverse_R, ground_height)

    bbox = np.empty(shape=(4, 1))
    bbox[0] = min(proj_coordinates[0, :])  # X min
    bbox[1] = max(proj_coordinates[0, :])  # X max
    bbox[2] = min(proj_coordinates[1, :])  # Y min
    bbox[3] = max(proj_coordinates[1, :])  # Y max

    return bbox


def get_vertices(image, pixel_size, focal_length):
    rows = image.shape[0]
    cols = image.shape[1]

    # (1) ------------ (2)
    #  |     image      |
    #  |                |
    # (4) ------------ (3)

    vertices = np.empty(shape=(3, 4))

    vertices[0, 0] = -cols * pixel_size / 2
    vertices[1, 0] = rows * pixel_size / 2

    vertices[0, 1] = cols * pixel_size / 2
    vertices[1, 1] = rows * pixel_size / 2

    vertices[0, 2] = cols * pixel_size / 2
    vertices[1, 2] = -rows * pixel_size / 2

    vertices[0, 3] = -cols * pixel_size / 2
    vertices[1, 3] = -rows * pixel_size / 2

    vertices[2, :] = -focal_length

    return vertices


def projection(vertices, position, rotation_matrix, ground_height):
    coord_GCS = np.dot(rotation_matrix, vertices)
    scale = (ground_height - position[2]) / coord_GCS[2]

    plane_coord_GCS = scale * coord_GCS[0:2] + [[position[0]], [position[1]]]

    return plane_coord_GCS


def cloth_simulation_filtering(xyz, bSloopSmooth=False, cloth_resolution=0.5):
    csf = CSF.CSF()

    # prameter settings
    csf.params.bSloopSmooth = bSloopSmooth
    csf.params.cloth_resolution = cloth_resolution
    # more details about parameter: http://ramm.bnu.edu.cn/projects/CSF/download/

    csf.setPointCloud(xyz)
    ground = CSF.VecInt()  # a list to indicate the index of ground points after calculation
    non_ground = CSF.VecInt()  # a list to indicate the index of non-ground points after calculation
    csf.do_filtering(ground, non_ground)  # do actual filtering.

    filtered_xyz = xyz[ground]  # extract ground points

    return filtered_xyz, ground


def interpolate_dem(xyz, gsd, method='linear'):
    X_min = np.min(xyz[:, 0])
    X_max = np.max(xyz[:, 0])
    Y_min = np.min(xyz[:, 1])
    Y_max = np.max(xyz[:, 1])

    # grid_x, grid_y = np.mgrid[X_min:X_max:gsd, Y_max:Y_min:-gsd]
    grid_y, grid_x = np.mgrid[Y_max:Y_min:-gsd, X_min:X_max:gsd]
    grid_z = griddata(xyz[:, 0:2], xyz[:, 2], (grid_x, grid_y), method=method)

    bbox = np.array([X_min, X_max, Y_min, Y_max])

    return grid_x, grid_y, grid_z, bbox


def generate_dem(point_clouds, gsd):
    start = time.time()
    # 1. Import point clouds
    # inFile = laspy.file.File(point_clouds, mode='r')  # read a las file
    # points = inFile.points
    # xyz = np.vstack((inFile.x, inFile.y, inFile.z)).transpose()  # extract x, y, z and put into a list
    # print("No. raw points:", len(xyz))

    cloud = o3d.io.read_point_cloud(point_clouds)
    print("No. raw points:", len(cloud.points))

    # 2. Denoising
    cl, ind = cloud.remove_statistical_outlier(nb_neighbors=6, std_ratio=1.0)
    inlier_cloud = cloud.select_by_index(ind)
    xyz = np.asarray(inlier_cloud.points)
    print("No. denoised points:", len(xyz))

    # 3. Ground filtering
    csf_start = time.time()
    filtered_xyz, ground = cloth_simulation_filtering(xyz)
    print("No. filtered points:", len(filtered_xyz))
    print(f"Ground filetering: {time.time() - csf_start:.2f} sec")

    # outFile = laspy.file.File(r"ground.las", mode='w', header=inFile.header)
    # outFile.points = points[ground]  # extract ground points, and save it to a las file.
    # outFile.close()  # do not forget this
    # filtered_xyz = xyz

    # 4. Interpolation
    interpolation_start = time.time()
    grid_x, grid_y, grid_z, bbox = interpolate_dem(filtered_xyz, gsd)
    print(f"Interpolation: {time.time() - interpolation_start:.2f} sec")
    print(f"Elpased time: {time.time() - start:.2f} sec")

    # import matplotlib.pyplot as plt
    # plt.imshow(grid_z)
    # plt.show()

    return grid_x, grid_y, grid_z, bbox

    
def generate_dem_pdal(point_clouds, dem_type="dtm", gsd=0.1):
    #TODO: using pdal python
    start = time.time()
    # Convert ply to las
    las_name = os.path.join(os.path.dirname(point_clouds), "reconstruction.las")
    os.system(f"pdal translate {point_clouds} {las_name}")
    # Filter the las
    if dem_type == "dtm":
        json = f"""
        [
            "{las_name}",
            {{
                "type":"filters.assign",
                "assignment":"Classification[:]=0"
            }},
            {{
                "type":"filters.elm"
            }},
            {{
                "type":"filters.outlier"
            }},
            {{
                "type":"filters.smrf",
                "ignore":"Classification[7:7]",
                "slope":0.2,
                "window":16,
                "threshold":0.45,
                "scalar":1.2
            }},
            {{
                "type":"filters.range",
                "limits":"Classification[2:2]"
            }}
        ]
        """
    elif dem_type == "dsm":
        json = f"""
        [
            "{las_name}",
            {{
                "type":"filters.assign",
                "assignment":"Classification[:]=0"
            }},
            {{
                "type":"filters.elm"
            }},
            {{
                "type":"filters.outlier"
            }},
            {{
                "type":"filters.range",
                "limits":"Classification[0:0]"
            }}
        ]
        """
    else:
        raise Exception("Invalid type of DEM!!!")
    
    import pdal
    pipeline = pdal.Pipeline(json)
    count = pipeline.execute()
    arrays = pipeline.arrays
    metadata = pipeline.metadata
    log = pipeline.log
    # pdal translate input.las output.las --json pipeline.json

    xyz = arrays[0]
    filtered_xyz = np.vstack((xyz['X'], xyz['Y'], xyz['Z'])).T

    # Generate DEM
    # pdal pipeline ./exercises/analysis/dtm/gdal.json

    # filtered_las = os.path.join(os.path.dirname(point_clouds), "reconstruction_filtered.las")
    # os.system(f"""pdal translate {las_name} \
    #             -o {filtered_las} \
    #             outlier smrf range  \
    #             --filters.outlier.method="statistical" \
    #             --filters.outlier.mean_k=8 --filters.outlier.multiplier=3.0 \
    #             --filters.smrf.ignore="Classification[7:7]"  \
    #             --filters.range.limits="Classification[2:2]" \
    #             --writers.las.compression=true \
    #             --verbose 4""")

    # 4. Interpolation
    interpolation_start = time.time()
    grid_x, grid_y, grid_z, bbox = interpolate_dem(filtered_xyz, gsd)
    print(f"Interpolation: {time.time() - interpolation_start:.2f} sec")
    print(f"Elpased time: {time.time() - start:.2f} sec")

    # import matplotlib.pyplot as plt
    # plt.imsave("dem.tif", grid_z)
    # # plt.imshow(grid_z)
    # # plt.show()

    return grid_x, grid_y, grid_z, bbox


def generate_dem_cloudcompare(point_clouds, dem_type, gsd):
    #TODO
    #1. SOR -SOR {number of neighbors} {sigma multiplier}
    #2. CSF -CSF {filename}
    #3. Rasterize -RASTERIZE -GRID_STEP {value}
    raise NotImplementedError

if __name__ == "__main__":
    generate_dem_pdal("data/yangpyeong/reconstruction.ply", "dsm", 0.1)
