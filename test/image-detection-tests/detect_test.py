"""
Tests the detection of the Fiducial tags from a live camera feed
"""

from src.dataprocessing.detect_tag import detect_aruco  # run with repo root as working dir
import numpy as np
import cv2

# sample from a laptop webcam
the_coefficients = {
    "camera_mat": [455.01779335911533, 449.638776236421, 347.7758170279836, 183.2528682832296],
    "distortion_mat": [
        0.39370256196311587, -1.8790623794035874, -0.004784372375460338, -1.9735858217122795e-05, 2.3541810896089586
    ]
}
side_len = 5  # sample provided by the guys at sdc

cap = cv2.VideoCapture(0)  # default

if not cap.isOpened():
    raise RuntimeError("Camera Unavailable")

while True:
    ret, frame = cap.read()

    if not ret:
        raise RuntimeError("Error with camera feed")

    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    tag_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_1000)
    tag_parameters = cv2.aruco.DetectorParameters()

    output = detect_aruco(grey, tag_dict, tag_parameters, the_coefficients, side_len)
    if output == {}:
        print("None Detected")
    else:
        rvecs = output["Rotational"]
        tvecs = output["Translation"]
        corners = output["Corners"]
        ids = output["IDs"]

        fx, fy, cx, cy = tuple(the_coefficients["camera_mat"])
        true_cam_mat = np.array([
            [fx, 0, cx],
            [0, fy, cy],
            [0, 0, 1],
        ])

        true_dist_coeff = np.array([the_coefficients["distortion_mat"]])

        for rvec, tvec in zip(rvecs, tvecs):
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            cv2.drawFrameAxes(
                frame, true_cam_mat, true_dist_coeff, rvec, tvec, side_len * 0.5
            )

    cv2.imshow("Camera Feed", frame)
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
