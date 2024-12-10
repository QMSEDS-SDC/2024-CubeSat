"""
Run calibration for the camera and get the coefficient values

It uses chess board to calibrate using the same algorithm as documentation from OpenCV
"""

import time
from typing import List
import numpy as np
import cv2


def generate_samples(
    required_number: int, row: int, col: int, camera_num: int = 0, interval: int = 5
) -> List[np.ndarray]:
    """
    Generates the required images for calibration

    Parameter:
        - required_number: The number of samples that will be generated though this function
        - row: internal row (so lower right corner of 1st square to upper right corner of last square)
        - col: internal col (same logic but inverted for col)
        - camera_num (=0): The index to access the webcam or camera from the device
        - interval (=5): The number of seconds to pause for

    Returns:
        - List of images choosen

    Exceptions:
        - ValueError: If required_number < 10 as per the OpenCV documentation atleast 10 samples are required to
                      calibrate the camera

    Note:
        - Use a printed chessboard or a real chessboard but it must me kept straight.
        - Only select the image if all the points are properly detected, else just don't
        - If you have the time less than one second, then there is a chance a image with no detected grid may be choosen
          which returns an exception with text - "nimages > 0 in function 'cv::calibrateCameraRO'"

    """

    imgs = []
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Camera Unavailable")
    elif required_number < 10:
        raise ValueError("The argument - required_number is less than 10 which is not enough for calibration")

    while required_number != 0:
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Error with camera feed")

        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(grey, (row, col), None)

        if ret:
            cv2.drawChessboardCorners(frame, (row, col), corners, ret)

        cv2.imshow("Camera Feed", frame)

        key = cv2.waitKey(1) & 0xFF  # Mask for 8-bit ASCII value
        if key == ord('q'):  # If 'q' is pressed
            imgs.append(frame)
            required_number -= 1
            print("Total left = {}".format(required_number))
        elif key == 27:  # esc
            raise RuntimeError("Quit before generating the images")

        time.sleep(interval)

    return imgs


def calibrate_camera(images: List[np.ndarray], row: int, col: int):
    """
    Calibrates the camera using chessboard images.

    Parameters:
        - images: List of captured images containing the chessboard pattern.
        - row: Number of inner corners per chessboard row.
        - col: Number of inner corners per chessboard column.

    Returns:
        - (Camera matrix, distortion coefficients, rotation vectors, and translation vectors)
    """

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    objp = np.zeros((row * col, 3), np.float32)
    objp[:, :2] = np.mgrid[0:col, 0:row].T.reshape(-1, 2)

    # Arrays to store object points and image points from all images
    objpoints = []  # 3D points in real-world space
    imgpoints = []  # 2D points in image plane

    for img in images:
        grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chessboard corners
        ret, corners = cv2.findChessboardCorners(grey, (col, row), None)

        if ret:
            objpoints.append(objp)  # Corresponding 3D points

            corners2 = cv2.cornerSubPix(grey, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)  # Corresponding 2D points

    # Camera calibration
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, grey.shape[::-1], None, None)

    if not ret:
        raise RuntimeError("Camera calibration failed.")

    return mtx, dist


def save_calibration_to_file(
    camera_matrix: np.ndarray, dist_coeffs: np.ndarray, filename: str = "camera_calibration.txt"
) -> None:

    """
    Saves camera calibration parameters to a text file.

    Parameters:
        camera_matrix: Camera intrinsic matrix.
        dist_coeffs: Distortion coefficients.
        filename (=camera_calibration.txt): Name of the file to save the calibration parameters.
    """
    with open(filename, 'w') as file:
        f_x = camera_matrix[0][0]
        c_x = camera_matrix[0][2]
        f_y = camera_matrix[1][1]
        c_y = camera_matrix[1][2]

        k_1 = dist_coeffs[0][0]
        k_2 = dist_coeffs[0][1]
        p_1 = dist_coeffs[0][2]
        p_2 = dist_coeffs[0][3]
        k_3 = dist_coeffs[0][4]

        file.write(f"f_x = {f_x}\n")
        file.write(f"c_x = {c_x}\n")
        file.write(f"f_y = {f_y}\n")
        file.write(f"c_y = {c_y}\n")

        file.write(f"k_1 = {k_1}\n")
        file.write(f"k_2 = {k_2}\n")
        file.write(f"p_1 = {p_1}\n")
        file.write(f"p_2 = {p_2}\n")
        file.write(f"k_3 = {k_3}\n")

    return None


if __name__ == "__main__":
    imgs = generate_samples(15, 9, 6, interval=1)
    camera_matrix, dist_coeffs = calibrate_camera(imgs, 9, 6)
    save_calibration_to_file(camera_matrix, dist_coeffs, filename="calibration_factors.txt")
