import PhotoScan
import time
import argparse


def photoscan_alignphotos(images):
    EOs = []
    start_time = time.time()

    doc = PhotoScan.app.document
    chunk = doc.addChunk()
    chunk.addPhotos(images)
    for camera in chunk.cameras:
        if not camera.reference.location:
            continue
        if ("DJI/RelativeAltitude" in camera.photo.meta.keys()) and camera.reference.location:
            z = float(camera.photo.meta["DJI/RelativeAltitude"])
            camera.reference.location = (camera.reference.location.x, camera.reference.location.y, z)
        gimbal_roll = float(camera.photo.meta["DJI/GimbalRollDegree"])
        gimbal_pitch = float(camera.photo.meta["DJI/GimbalPitchDegree"])
        gimbal_yaw = float(camera.photo.meta["DJI/GimbalYawDegree"])
        camera.reference.rotation = (gimbal_yaw, 90 + gimbal_pitch, gimbal_roll)

    chunk.matchPhotos(accuracy=PhotoScan.MediumAccuracy)
    chunk.alignCameras()

    doc.save("test.psz")

    camera = chunk.cameras[-1]
    if not camera.transform:
        print("There is no transformation matrix")

    estimated_coord = chunk.crs.project(
        chunk.transform.matrix.mulp(camera.center))  # estimated XYZ in coordinate system units
    T = chunk.transform.matrix
    m = chunk.crs.localframe(
        T.mulp(camera.center))  # transformation matrix to the LSE coordinates in the given point
    R = (m * T * camera.transform * PhotoScan.Matrix().Diag([1, -1, -1, 1])).rotation()
    estimated_ypr = PhotoScan.utils.mat2ypr(R)  # estimated orientation angles - yaw, pitch, roll
    estimated_opk = PhotoScan.utils.mat2opk(R)  # estimated orientation angles - omega, phi, kappa

    pos = list(estimated_coord)
    ori = list(estimated_opk)
    eo = [pos[0], pos[1], pos[2], ori[0], ori[1], ori[2]]
    EOs.append(eo)
    print("======================================================================================================")
    print(images[-1].split("/")[-1], eo)
    print("======================================================================================================")
    print("process time of each image = ", time.time() - start_time)

    print(estimated_coord, estimated_opk)
    print(estimated_coord[0])
    print(estimated_coord[1])
    print(estimated_coord[2])
    print(estimated_opk[0])
    print(estimated_opk[1])
    print(estimated_opk[2])


if __name__ == '__main__':
    # Set argument parser
    parser = argparse.ArgumentParser(description='LBA-photoscan')
    parser.add_argument('--image-path', nargs='+', required=True)

    args = parser.parse_args()
    image_path = args.image_path
    print(type(image_path))
    print(image_path[0])

    photoscan_alignphotos(image_path)

