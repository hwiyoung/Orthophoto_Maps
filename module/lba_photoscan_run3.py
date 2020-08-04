import PhotoScan
import time
import argparse


def photoscan_alignphotos(images, reference_eo, sequence):
    start_time = time.time()

    doc = PhotoScan.app.document
    chunk = doc.addChunk()
    chunk.addPhotos(images)
    for i in range(len(chunk.cameras)):
        chunk.cameras[i].reference.location = (float(reference_eo[6 * i]), float(reference_eo[6 * i + 1]), float(reference_eo[6 * i + 2]))
        chunk.cameras[i].reference.rotation = (float(reference_eo[6 * i + 5]), float(reference_eo[6 * i + 4]), float(reference_eo[6 * i + 3]))

    chunk.camera_location_accuracy = PhotoScan.Vector([0.001, 0.001, 0.001])
    chunk.camera_rotation_accuracy = PhotoScan.Vector([0.01, 0.01, 0.01])
    # chunk.cameras[-1].reference.location_accuracy = PhotoScan.Vector([10, 10, 10])
    # chunk.cameras[-1].reference.rotation_accuracy = PhotoScan.Vector([10, 10, 10])
    chunk.cameras[-1].reference.accuracy = PhotoScan.Vector([10, 10, 10])
    chunk.cameras[-1].reference.accuracy_ypr = PhotoScan.Vector([10, 10, 10])

    chunk.matchPhotos(accuracy=PhotoScan.MediumAccuracy)
    chunk.alignCameras()

    # doc.save("test_" + str(int(sequence)+1) + ".psz")

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

    print(estimated_coord[0])
    print(estimated_coord[1])
    print(estimated_coord[2])
    print(estimated_ypr[0])
    print(estimated_ypr[1])
    print(estimated_ypr[2])
    print(estimated_opk[0])
    print(estimated_opk[1])
    print(estimated_opk[2])


if __name__ == '__main__':
    # # Set argument parser
    # parser = argparse.ArgumentParser(description='LBA-photoscan')
    # parser.add_argument('--image-path', nargs='+', required=True)
    # parser.add_argument('--reference', required=True)
    #
    # args = parser.parse_args()
    # image_path = args.image_path
    # reference = args.reference
    #
    # photoscan_alignphotos(image_path, reference)

    # Set argument parser
    parser = argparse.ArgumentParser(description='LBA-photoscan')
    parser.add_argument('--image-path', nargs='+', required=True)
    parser.add_argument('--reference', nargs='+', required=True)
    parser.add_argument('--sequence', required=True)

    args = parser.parse_args()
    image_path = args.image_path
    reference = args.reference
    sequence = args.sequence

    photoscan_alignphotos(image_path, reference, sequence)

