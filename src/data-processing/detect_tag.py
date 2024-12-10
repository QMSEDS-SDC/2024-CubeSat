"""
Collection of Functions to Detect Fiducial Tags in Images, and Get Positional Data from them

Supports: ArUco Tags only
"""

from typing import Dict, List
import numpy as np
import cv2


def image_valid(img: np.ndarray) -> int:
    """
    Checks if an image is valid or not (valid array and greyscaled)

    Parameter:
        - img: The image array to check

    Returns:
        - 0: Image is valid
        - -1: The image is not grey scale
        - -2: The array is not valid for an image
    """

    if img.size == 0 or np.amin(img) < 0 or np.amax(img) > 255:
        return -2
    elif len(img.shape) != 2:
        return -1
    return 0


def detect_aruco(
    img: np.ndarray, aruco_dict: cv2.aruco.Dictionary, aruco_parameters: cv2.aruco.DetectorParameters,
    calibration: Dict[str, List[float]], debug: bool = False
) -> Dict[str, List[float]]:

    """
    The functions detects the existance of ArUco Tags. If detected, return position information

    Parameters:
        - img: The image array, must be grey scale
        - aruco_dict: The dict used for detection
        - aruco_parameters: The parameters used for detection
        - calibration:
            - "camera_mat": [fx, fy, cx, cy]
            - "distortion_mat": [k1, k2, p1, p2, k3]
        - debug (false): allows viewing of the detected tag, but debug purposes

    Returns:
        - {}: ArUco tag not detected
        - {"Translation" : [tx, ty, tz], "Rotational": [rx, ry, rz]}
        - if debug=True:
            - {"Result": (corners, ids, rejecteds)} -- only for debugging purposes

    Raises:
        - ValueError
            - I.1: if image supplied is not grey scale
            - I.2: if the array supplied is invalid as an image
            - if aruco dictionary input or/and aruco parameter input are invalid
                - A.1 (dict only), A.2 (para only) and A.3 (both)

    Notes:
        - The validity of other parameters is not checked as they are checked though type casting
    """

    img_validity = image_valid(img)
    if img_validity == -1:
        raise ValueError("Error I.1: Image is not greyscale")
    elif img_validity == -2:
        raise ValueError("Error I.2: Image Array format is invalid")

    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_parameters)

    # corners - (x, y) for the tags; ids - ID encoded in tag; rejected - potential markers but rejected
    if debug:
        return {"Result": detector.detectMarkers(img)}
    corners, ids, rejected = detector.detectMarkers(img)

    # no ids found
    if ids is None:
        return {}
