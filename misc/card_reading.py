"""
Tests the detection of the number cards from a live camera feed
"""

from src.dataprocessing.detect_cards import detect_card  # run with repo root as working dir
from misc.use_camera import start_camera, stop_camera, get_frame
import numpy as np
import cv2


# default, change it to the video feed from mobile if that is something you find interesting
# note when using a http feed, the feed should be in the form of http://<ip>:<port>/video
inp = input("Enter the camera feed url (0 = default laptop one): ")
if inp == "0":
    inp = 0
cap = start_camera(inp)

while True:
    frame = get_frame(cap)

    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cv2.imshow("frame", frame)

    if cv2.waitKey(1) == ord("q"):
        stop_camera(cap)
        break
