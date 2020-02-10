"""
ray.py
----------------

Do simple mesh- ray queries. Base functionality only
requires numpy, but if you install `pyembree` you get the
same API with a roughly 50x speedup.
"""

import trimesh
import numpy as np
from EoData import Rot3D

if __name__ == '__main__':

    # test on a sphere mesh
    #mesh = trimesh.primitives.Sphere()
    #mesh = trimesh.load('./models/cube_compressed.obj')
    #mesh = trimesh.load('./models/cube.OBJ')
    #mesh = trimesh.load('./models/cube_test.OBJ')
    mesh = trimesh.load('./models/DEM_yeosu/34707 - Cloud.obj')
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

    idx_ul = np.argmin(np.sqrt(np.sum((vertices[:, 0:2] - bbox[0]) ** 2, axis=1)))
    idx_ll = np.argmin(np.sqrt(np.sum((vertices[:, 0:2] - bbox[1]) ** 2, axis=1)))
    idx_ur = np.argmin(np.sqrt(np.sum((vertices[:, 0:2] - bbox[2]) ** 2, axis=1)))
    idx_lr = np.argmin(np.sqrt(np.sum((vertices[:, 0:2] - bbox[3]) ** 2, axis=1)))

    coord_ul_mesh = vertices[idx_ul]
    coord_ll_mesh = vertices[idx_ll]
    coord_ur_mesh = vertices[idx_ur]
    coord_lr_mesh = vertices[idx_lr]

    dem = vertices[((vertices[:, 0] >= coord_ul_mesh[0]) & (vertices[:, 0] <= coord_ur_mesh[0])) &
                   ((vertices[:, 1] >= coord_ll_mesh[1]) & (vertices[:, 1] <= coord_ul_mesh[1]))]

    dem_output = dem.transpose()

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
