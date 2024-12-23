"""
Detects cards (rectangles) in an image and if detected then detects the number printed on it
"""

import cv2
import numpy as np
from typing import Tuple, List


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


def detect_rectangular_contours(
    img: np.ndarray, width_range: Tuple(int, int), height: Tuple(int, int), algo: str = "canny"
) -> List[Tuple(float, float, float, float)]:
    """
    Detects rectangular contours in an image

    Parameters:
        - img: The image array (needs to be greyscale)
        - width_range: The range of width of the rectangle to detect (min, max)
        - height_range: The range of height of the rectangle to detect (min, max)
        - algo: The algorithm to use for detection (default: canny)

    Returns:
        - img: The image array with detected rectangles drawn

    Exceptions:
        - ValueError
            - I.1: if image supplied is not grey scale
            - I.2: if the array supplied is invalid as an image
            - A.1: if the algorithm is invalid or not implemented
    """

    img_validity = image_valid(img)
    if img_validity == -1:
        raise ValueError("Error I.1: Image is not greyscale")
    elif img_validity == -2:
        raise ValueError("Error I.2: Image Array format is invalid")

    if algo == "canny":
        edges = cv2.Canny(img, 50, 150)
        cnts, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    else:
        raise ValueError("Error A.1: Invalid Algorithm or not Implemented")

    result = []
    for cnt in cnts:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 50 and h > 50:
            result.append((x, y, w, h))

    return result
