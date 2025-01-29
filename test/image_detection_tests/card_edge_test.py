"""
Tests the card edge detection
"""

import cv2
import matplotlib.pyplot as plt
import numpy as np
import unittest
from src.dataprocessing.processing.detect_cards import detect_card_contours, draw_card_contours

files = ["test\\image_detection_tests\\img\\card-edge-sample.webp"]

img = files[0]
img = cv2.imread(img)

grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
shape = img.shape
width_range = (0, shape[1])
height_range = (0, shape[0])
min_x, max_x = shape[1], 0
min_y, max_y = shape[0], 0

find_cnts = (cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
method = cv2.CHAIN_APPROX_SIMPLE
mode = cv2.RETR_TREE
edges = cv2.Canny(img, 0, 255)
cnts, _ = cv2.findContours(edges, mode, method)

result = []
for cnt in cnts:
    if len(width_range) != 2 or len(height_range) != 2:
        raise ValueError("Error I.3: Invalid Arguments for Width or Height Range")
    w_min, w_max = width_range
    h_min, h_max = height_range
    x, y, w, h = cv2.boundingRect(cnt)
    min_x, max_x = min(x, min_x), max(x+w, max_x)
    min_y, max_y = min(y, min_y), max(y+h, max_y)
    print(x, y, w, h)
    cv2.rectangle(img, (x,y), (x+w,y+h), (255, 0, 0), 2)

print(result)

plt.imshow(cv2.drawContours(grey, result, -1, (0, 0, 0), 3), cmap='gray')
plt.show()
