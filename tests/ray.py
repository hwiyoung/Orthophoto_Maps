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

    # create some rays
    # DJI_0386.JPG in Data
    ray_origins = np.array([[266277.339, 237080.832, 214.9540],
                            [266277.339, 237080.832, 214.9540],
                            [266277.339, 237080.832, 214.9540],
                            [266277.339, 237080.832, 214.9540]])
    direction = np.array([1.697624393, -2.926766149, -54.16184732]) * np.pi / 180   # o, p, k
    R = Rot3D([266277.339, 237080.832, 214.9540, direction[0], direction[1], direction[2]]) # Ground to Camera
    # directions(vector) - [x(East/West), y(North/South), z]
    # width/2, height/2, focal_length ... direction vector
    direction_vectors = np.array([[-3.15, -2.36, -4.73],   # UL
                               [3.15, -2.36, -4.73],    # UR
                               [-3.15, 2.36, -4.73],   # LL
                               [3.15, 2.36, -4.73]])   # LR
    direction_vectors_rot = np.dot(R.transpose(), direction_vectors.transpose())    # Camera to Groud
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
