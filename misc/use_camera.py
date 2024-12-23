"""
Just to simplify the use of the camera
"""

import cv2
import numpy as np
from typing import Union


def start_camera(source: Union[str, int]) -> cv2.VideoCapture:
    """
    Starts the camera feed

    Parameters:
      - source (Union[str, int]): the source of the camera feed, can be a URL or an integer for a connected camera

    Returns:
      - cap (cv2.VideoCapture): the camera feed object

    Exceptions:
        - RuntimeError: if the camera feed is not available

    """

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        raise RuntimeError("Camera Unavailable")

    return cap


def stop_camera(cap: cv2.VideoCapture) -> None:
    """
    Stops the camera feed

    Parameters:
        - cap (cv2.VideoCapture): the camera feed object
    """

    cap.release()
    cv2.destroyAllWindows()


def get_frame(cap: cv2.VideoCapture) -> np.ndarray:
    """
    Gets the frame from the camera feed

    Parameters:
        - cap (cv2.VideoCapture): the camera feed object

    Returns:
        - frame (np.ndarray): the frame from the camera feed
    """

    ret, frame = cap.read()

    if not ret:
        raise RuntimeError("Error with camera feed")

    return frame
