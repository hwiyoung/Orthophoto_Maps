"""
ray.py
----------------

Do simple mesh- ray queries. Base functionality only
requires numpy, but if you install `pyembree` you get the
same API with a roughly 50x speedup.
"""

import trimesh
import numpy as np
from module.EoData import Rot3D
from scipy.interpolate import griddata


def interpolate_dem(xyz, gsd, method='linear'):     # only 'inter'polation
    X_min = np.min(xyz[:, 0])
    X_max = np.max(xyz[:, 0])
    Y_min = np.min(xyz[:, 1])
    Y_max = np.max(xyz[:, 1])

    # grid_x, grid_y = np.mgrid[X_min:X_max:gsd, Y_max:Y_min:-gsd]
    grid_y, grid_x = np.mgrid[Y_max:Y_min:-gsd, X_min:X_max:gsd]
    grid_z = griddata(xyz[:, 0:2], xyz[:, 2], (grid_x, grid_y), method=method)

    bbox = np.array([X_min, X_max, Y_min, Y_max])

    return grid_x, grid_y, grid_z, bbox



if __name__ == '__main__':

    # test on a sphere mesh
    #mesh = trimesh.primitives.Sphere()
    #mesh = trimesh.load('./models/cube_compressed.obj')
    #mesh = trimesh.load('./models/cube.OBJ')
    #mesh = trimesh.load('./models/cube_test.OBJ')
    mesh = trimesh.load('./models/DEM_yeosu/34707 - Cloud.obj')     # GSD: 90m
    vertices = np.array(mesh.vertices)

    # create some rays
    # DJI_0386.JPG
    # ray_origins = np.array([[266277.339, 237080.832, 214.9540],   # Absolute height
    #                         [266277.339, 237080.832, 214.9540],
    #                         [266277.339, 237080.832, 214.9540],
    #                         [266277.339, 237080.832, 214.9540]])
    ray_origins = np.array([[266277.339, 237080.832, 149.9540],     # Relative height
                            [266277.339, 237080.832, 149.9540],
                            [266277.339, 237080.832, 149.9540],
                            [266277.339, 237080.832, 149.9540]])
    direction = np.array([1.697624393, -2.926766149, -54.16184732]) * np.pi / 180   # o, p, k
    R = Rot3D([266277.339, 237080.832, 214.9540, direction[0], direction[1], direction[2]]) # Ground to Camera
    # directions(vector) - [x(East/West), y(North/South), z]
    # width/2, height/2, focal_length ... direction vector
    # (1) ------------ (2)
    #  |     image      |
    #  |                |
    # (4) ------------ (3)
    direction_vectors = np.array([[-3.15, 2.36, -4.73],     # Upper Left
                                  [3.15, 2.36, -4.73],      # Upper Right
                                  [3.15, -2.36, -4.73],     # Lower Right
                                  [-3.15, -2.36, -4.73]])   # Lower Left

    direction_vectors_rot = np.dot(R.transpose(), direction_vectors.transpose())    # Camera to Ground
    ray_directions = direction_vectors_rot.transpose()

    """
    Signature: mesh.ray.intersects_location(ray_origins,
                                            ray_directions,
                                            multiple_hits=True)
    Docstring:

    Return the location of where a ray hits a surface.

    Parameters
    ----------
    ray_origins:    (n,3) float, origins of rays
    ray_directions: (n,3) float, direction (vector) of rays


    Returns
    ---------
    locations: (n) sequence of (m,3) intersection points
    index_ray: (n,) int, list of ray index
    index_tri: (n,) int, list of triangle (face) indexes
    """

    # run the mesh- ray test
    locations, index_ray, index_tri = mesh.ray.intersects_location(
        ray_origins=ray_origins,
        ray_directions=ray_directions)
    bbox = np.array([[min(locations[:, 0]), max(locations[:, 1])],  # Upper Left
                    [min(locations[:, 0]), min(locations[:, 1])],   # Lower Left
                    [max(locations[:, 0]), max(locations[:, 1])],   # Upper Right
                    [max(locations[:, 0]), min(locations[:, 1])]])  # Lower Right
    print(bbox)

    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')  # Axe3D object

    x = vertices[:, 0]
    y = vertices[:, 1]
    z = vertices[:, 2]
    # ax.scatter(x, y, z, c=z, s=20, alpha=0.5, cmap=plt.cm.Greens, label="first")
    # ax.scatter(locations[:, 0], locations[:, 1], max(mesh.bounds[:, 2]), c='red', s=50, label="second")
    ax.scatter(x, y, c='green', s=20, alpha=0.5, label="DEM")
    ax.scatter(locations[:, 0], locations[:, 1], c='red', s=50, label="boundary")
    ax.view_init(azim=-90, elev=90)
    # Labels.
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    plt.axis([min(locations[:, 0]) - 100, max(locations[:, 0]) + 100,
              min(locations[:, 1]) - 100, max(locations[:, 1]) + 100])
    plt.title("ax.scatter")
    plt.legend(loc='upper left')
    plt.show()

    dem = vertices[((vertices[:, 0] >= bbox[0, 0]) & (vertices[:, 0] <= bbox[2, 0])) &  # x
                   ((vertices[:, 1] >= bbox[1, 1]) & (vertices[:, 1] <= bbox[0, 1]))]   # y

    # TODO: RBF for extrapolation
    grid_x, grid_y, grid_z, _ = interpolate_dem(xyz=dem, gsd=0.1)
    plt.imshow(grid_z)
    plt.title("interpolated dem")
    plt.show()

    # stack rays into line segments for visualization as Path3D
    ray_visualize = trimesh.load_path(np.hstack((
        ray_origins,
        ray_origins + ray_directions)).reshape(-1, 2, 3))

    # make mesh transparent- ish
    mesh.visual.face_colors = [100, 100, 100, 100]

    # create a visualization scene with rays, hits, and mesh
    scene = trimesh.Scene([
        mesh,
        ray_visualize,
        trimesh.points.PointCloud(locations)])

    # display the scene
    scene.show()
