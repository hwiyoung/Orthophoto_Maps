import numpy as np
# import trimesh
import time

def boundary(image, eo, R, dem, pixel_size, focal_length):
    inverse_R = R.transpose()

    image_vertex = getVertices(image, pixel_size, focal_length)  # shape: 3 x 4

    proj_coordinates = projection(image_vertex, eo, inverse_R, dem)

    bbox = np.empty(shape=(4, 1))
    bbox[0] = min(proj_coordinates[0, :])  # X min
    bbox[1] = max(proj_coordinates[0, :])  # X max
    bbox[2] = min(proj_coordinates[1, :])  # Y min
    bbox[3] = max(proj_coordinates[1, :])  # Y max

    return bbox

def getVertices(image, pixel_size, focal_length):
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

def projection(vertices, eo, rotation_matrix, dem):
    coord_GCS = np.dot(rotation_matrix, vertices)
    scale = (dem - eo[2]) / coord_GCS[2]

    plane_coord_GCS = scale * coord_GCS[0:2] + [[eo[0]], [eo[1]]]

    return plane_coord_GCS

def pcs2ccs(bbox_px, rows, cols, pixel_size, focal_length):
    bbox_camera = np.empty(shape=(3, bbox_px.shape[1]))

    bbox_camera[0, :] = (bbox_px[0, :] - cols / 2) * pixel_size
    bbox_camera[1, :] = -(bbox_px[1, :] - rows / 2) * pixel_size
    bbox_camera[2, :] = -focal_length

    return bbox_camera

def ray_tracing(image, eo, R, dem, vertices, pixel_size, focal_length):
    # create rays
    ray_origins = np.empty(shape=(4, 3))
    ray_origins[:, 0] = eo[0]
    ray_origins[:, 1] = eo[1]
    ray_origins[:, 2] = eo[2]

    # (1) ------------ (2)
    #  |     image      |
    #  |                |
    # (4) ------------ (3)
    image_vertex = getVertices(image, pixel_size, focal_length)  # shape: 3 x 4
    direction_vectors = image_vertex.transpose()    # shape: 4 x 3
    direction_vectors_rot = np.dot(R.transpose(), direction_vectors.transpose())  # Camera to Ground
    ray_directions = direction_vectors_rot.transpose()

    # run the mesh- ray test
    locations, index_ray, index_tri = dem.ray.intersects_location(
        ray_origins=ray_origins,
        ray_directions=ray_directions)
    bbox = np.empty(shape=(4, 1))
    bbox[0] = min(locations[:, 0])  # X min
    bbox[1] = max(locations[:, 0])  # X max
    bbox[2] = min(locations[:, 1])  # Y min
    bbox[3] = max(locations[:, 1])  # Y max

    test_origins = np.array([[bbox[0, 0], bbox[3, 0], eo[2]],   # UL
                             [bbox[1, 0], bbox[3, 0], eo[2]],   # UR
                             [bbox[1, 0], bbox[2, 0], eo[2]],   # LR
                             [bbox[0, 0], bbox[2, 0], eo[2]]])  # LL
    test_directions = np.array([[0, 0, -1],
                                [0, 0, -1],
                                [0, 0, -1],
                                [0, 0, -1]])
    test_locations, test_index_ray, test_index_tri = dem.ray.intersects_location(
        ray_origins=test_origins, ray_directions=test_directions)
    coord_ul_mesh = test_locations[0]
    coord_ur_mesh = test_locations[1]
    coord_lr_mesh = test_locations[2]
    coord_ll_mesh = test_locations[3]

    dem_extracted = vertices[((vertices[:, 0] >= coord_ul_mesh[0]) & (vertices[:, 0] <= coord_ur_mesh[0])) &
                             ((vertices[:, 1] >= coord_ll_mesh[1]) & (vertices[:, 1] <= coord_ul_mesh[1]))]

    dem_extracted[:, 0] -= eo[0]
    dem_extracted[:, 1] -= eo[1]
    dem_extracted[:, 2] -= eo[2]

    # ### Check for boundary
    # # stack rays into line segments for visualization as Path3D
    # ray_visualize = trimesh.load_path(np.hstack((
    #     ray_origins,
    #     ray_origins + ray_directions)).reshape(-1, 2, 3))
    #
    # # make mesh transparent- ish
    # dem.visual.face_colors = [100, 100, 100, 100]
    #
    # # create a visualization scene with rays, hits, and mesh
    # scene = trimesh.Scene([
    #     dem,
    #     ray_visualize,
    #     trimesh.points.PointCloud(locations)])
    #
    # # display the scene
    # scene.show()

    return bbox, dem_extracted
