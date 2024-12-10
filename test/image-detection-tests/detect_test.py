"""
Tests the detection of the Fiducial tags from a live camera feed
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

    cv2.imshow("Camera Feed", frame)
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
