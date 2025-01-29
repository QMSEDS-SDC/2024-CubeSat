"""
Tests the detection of the number cards from a live camera feed
"""

# run with repo root as working dir
from src.dataprocessing.processing.detect_cards import detect_card_contours, draw_card_contours, choose_card_contours
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
    shape = frame.shape

    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    result = detect_card_contours(grey, (shape[1]//10, shape[1]//2), (shape[0]//10, shape[0]//2), (100, 200))
    result = choose_card_contours(result)    
    for vals in result:
        x, y, w, h = vals
        result_img = draw_card_contours(grey, (x, y, w, h))

    cv2.imshow("frame", result_img)

    if cv2.waitKey(1) == ord("q"):
        stop_camera(cap)
        break
