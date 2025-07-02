"""
The FSM code that the CubeSat will run
"""

import torch
import torch.nn as nn

import numpy as np
import cv2
from dataprocessing.model.train import CNN
import dataprocessing.processing.image_preprocessing as preimg
import dataprocessing.processing.detect_cards as cd
import dataprocessing.processing.detect_tag as arucod
import API.comms
import AOCS.detumbling_control as detumble
import AOCS.aocs_control as ctl


# Constants
digit_recorgnition_trained = False
digit_recorgnition_model = "./dataprocessing/model/cnnNumClassifier.pth"
camera_calibration_done = False
camera_calibration_factors = "./dataprocessing/calibration/calibration_factors.txt"
comms_env_values = "./API/env_values.json"
log_dir_comms = "./API/logs"
log_dir_aocs = "./AOCS/logs"  # TODO
log_dir_img_processing = "./dataprocessing/logs"  # TODO


class FSM:
    def __init__(self):
        """
        Initialses the stuff
        """
        pass

    def default_init(self):
        """
        Initates the Default state the cubesat should be in
        """

    def phase1_init(self):
        """
        Initiates Phase 1
        """
        pass

    def phase2_init(self):
        """
        Initiate Phase 2
        """
        pass

    def phase3_init(self):
        """
        Initiate Phase 3
        """
        pass
