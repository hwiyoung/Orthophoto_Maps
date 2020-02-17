import numpy as np
import trimesh

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

def ray_tracing(image, eo, R, dem, pixel_size, focal_length):
    vertices = np.array(dem.vertices)

    # create some rays
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
    bbox = np.array([[min(locations[:, 0]), max(locations[:, 1])],  # Upper Left
                     [max(locations[:, 0]), max(locations[:, 1])],  # Upper Right
                     [max(locations[:, 0]), min(locations[:, 1])],  # Lower Right
                     [min(locations[:, 0]), min(locations[:, 1])]]) # Lower Left
    # print(bbox)

    idx_ul = np.argmin(np.sqrt(np.sum((vertices[:, 0:2] - bbox[0]) ** 2, axis=1)))
    idx_ur = np.argmin(np.sqrt(np.sum((vertices[:, 0:2] - bbox[1]) ** 2, axis=1)))
    idx_lr = np.argmin(np.sqrt(np.sum((vertices[:, 0:2] - bbox[2]) ** 2, axis=1)))
    idx_ll = np.argmin(np.sqrt(np.sum((vertices[:, 0:2] - bbox[3]) ** 2, axis=1)))

    coord_ul_mesh = vertices[idx_ul]
    coord_ur_mesh = vertices[idx_ur]
    coord_lr_mesh = vertices[idx_lr]
    coord_ll_mesh = vertices[idx_ll]

    dem_extracted = vertices[((vertices[:, 0] >= coord_ul_mesh[0]) & (vertices[:, 0] <= coord_ur_mesh[0])) &
                             ((vertices[:, 1] >= coord_ll_mesh[1]) & (vertices[:, 1] <= coord_ul_mesh[1]))]
    dem_output = dem_extracted.transpose()
    dem_output[0] -= eo[0]
    dem_output[1] -= eo[1]
    dem_output[2] -= eo[2]

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

    return bbox, dem_output
