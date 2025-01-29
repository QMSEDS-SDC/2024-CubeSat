"""
Tests the card edge detection
"""

import cv2
import matplotlib.pyplot as plt
import numpy as np
import unittest
from src.dataprocessing.processing.detect_cards import detect_card_contours, draw_card_contours, choose_card_contours

files = ["test\\image_detection_tests\\img\\card-edge-sample.webp"]

frame = cv2.imread(files[0])

grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
shape = frame.shape

shape = frame.shape
result = detect_card_contours(grey, (0, shape[1] - 1), (0, shape[0] - 1), (50, 250))
result = choose_card_contours(result)

for vals in result:
    x, y, w, h = vals
    result_img = draw_card_contours(grey, (x, y, w, h))

plt.imshow(result_img, cmap='gray')
plt.show()
