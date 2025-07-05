"""
The FSM code that the CubeSat will run
"""

import torch
import torch.nn as nn
import threading
import numpy as np
import cv2

from dataprocessing.model.train import CNN
import dataprocessing.processing.image_preprocessing as preimg
import dataprocessing.processing.detect_cards as cd
import dataprocessing.processing.detect_tag as arucod
from API.comms import Server_Comms
import AOCS.detumbling_control as detumble
import AOCS.aocs_control as ctl
from AOCS.camera import Camera


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

        starts comms, creates all the objects needed for the phases and turns into default
        """
        self.server = Server_Comms()
        self.server.start_listening(size_client_queue=2)
        self.cam = Camera()
        self.model = CNN()
        self.model.load_state_dict(torch.load(digit_recorgnition_model, weights_only=True))

        self.default()

    def _digit_guesser(self, img: np.ndarray):
        self.model.eval()
        img = torch.tensor(img)
        prediction = -1
        with torch.no_grad():
            outputs = self.model(img)
            _, predicted = torch.max(outputs.data, 1)
            prediction.extend(predicted.cpu().numpy())
        return prediction

    def _pings(self):
        pass

    def default(self):
        """
        Initates the Default state the cubesat should be in

        send regular pings + wait for command to initiate some phase
        """
        pass

    def phase1(self):
        """
        Initiates Phase 1

        run health check stuff and goes back to default
        """
        pass

    def phase2(self):
        """
        Initiate Phase 2
        """
        pass

    def phase3(self):
        """
        Initiate Phase 3
        """
        pass
