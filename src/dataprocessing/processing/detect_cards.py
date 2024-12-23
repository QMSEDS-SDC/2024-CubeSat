"""
Detects cards (rectangles) in an image and if detected then detects the number printed on it
"""

import cv2
import numpy as np
from typing import Tuple, List, Dict


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


def detect_card_contours(
    img: np.ndarray, width_range: Tuple(int, int), height_range: Tuple(int, int), args: Tuple[int], algo: str = "canny",
    find_cnts: Tuple(str, str) = (cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
) -> List[Tuple(float, float, float, float)]:
    """
    Detects card (rectangular) contours in an image

    Parameters:
        - img: The image array (needs to be greyscale)
        - width_range: The range of width of the rectangle to detect (min, max)
        - height_range: The range of height of the rectangle to detect (min, max)
        - algo: The algorithm to use for detection (default: canny)
        - args: The arguments for the algorithm
            - canny: The threshold values for the canny algorithm - (max, min)
        - find_cnts: The arguments for finding contours (default: (cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE))

    Returns:
        - img: The image array with detected rectangles drawn

    Exceptions:
        - ValueError
            - I.1: if image supplied is not grey scale
            - I.2: if the array supplied is invalid as an image
            - I.3: if the width or height range is invalid
            - A.1: if the algorithm is invalid or not implemented
            - A.2: if the arguments supplied are invalid for the canny algorithm
            - A.3: if the arguments supplied are invalid for finding contours
    """

    img_validity = image_valid(img)
    if img_validity == -1:
        raise ValueError("Error I.1: Image is not greyscale")
    elif img_validity == -2:
        raise ValueError("Error I.2: Image Array format is invalid")

    if algo == "canny":
        if len(args) != 2:
            raise ValueError("Error A.2: Invalid Arguments for Canny Algorithm")
        elif len(find_cnts) != 2:
            raise ValueError("Error A.3: Invalid Arguments for Finding Contours")
        min_thresh, max_thresh = args
        mode, method = find_cnts
        edges = cv2.Canny(img, min_thresh, max_thresh)
        cnts, _ = cv2.findContours(edges, mode, method)
    else:
        raise ValueError("Error A.1: Invalid Algorithm or not Implemented")

    result = []
    for cnt in cnts:
        if len(width_range) != 2 or len(height_range) != 2:
            raise ValueError("Error I.3: Invalid Arguments for Width or Height Range")
        w_min, w_max = width_range
        h_min, h_max = height_range
        x, y, w, h = cv2.boundingRect(cnt)
        if w_min >= w >= w_max and h_min >= h >= h_max:
            result.append((x, y, w, h))

    return result


def detect_card_numbers(
    img: np.ndarray, card_cnts: List[Tuple(float, float, float, float)]
) -> Dict[str, Tuple[Tuple(float, float, float, float), int]]:

    """
    Detects the number present on the card

    Parameters:
        - img: The image array (needs to be greyscale)
        - card_cnts: The contours of the cards

    Returns:
        - {
            "Number": (
                (x_point, y_point, width, height), detected_number
            )
        }
    """

    return {}
