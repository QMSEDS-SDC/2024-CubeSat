"""
Tests the position detection from Fiducial tags from a live camera feed
"""

from src.dataprocessing.detect_tag import detect_aruco  # run with repo root as working dir
import cv2

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

    output = detect_aruco(grey, tag_dict, tag_parameters, {})
    if output == {}:
        print("None Detected")
    else:
        corners, ids, rejected = output["Result"]
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

    cv2.imshow("Camera Feed", frame)
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
