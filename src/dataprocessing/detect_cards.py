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
