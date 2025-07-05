"""
The FSM code that the CubeSat will run
"""

import time
import torch
import torch.nn as nn
import threading
import numpy as np
import cv2
import datetime

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
        self.comms_thread = threading.Thread(
            target=self.server.start_listening, 
            args=(2,), 
            daemon=True
        )
        self.comms_thread.start()
        self.cam = Camera()
        self.model = CNN()
        self.model.load_state_dict(torch.load(digit_recorgnition_model, weights_only=True))

        # FSM state management
        self.current_phase = "default"
        self.phase_results = {}
        self.running = True

        # Register FSM with comms for phase control
        self.server.fsm = self

        self.default()
    
    def get_telemetry_data(self):
        """
        Get formatted telemetry data for Phase 1 dashboard
        """
        status_data = self.server._get_system_status()
        current_time = datetime.now()
        
        # Check camera availability
        try:
            camera_status = self.cam_api._check_camera_availability()
            status_data["payload"]["camera_available"] = True
        except Exception:
            status_data["payload"]["camera_available"] = False
            status_data["payload"]["status"] = "NOT OK"
        
        # Format telemetry message
        telemetry = {
            "timestamp": current_time.isoformat(),
            "phase": self.current_phase,
            "power": status_data.get("power", {}),
            "thermal": status_data.get("thermal", {}),
            "communication": status_data.get("communication", {}),
            "adcs": status_data.get("adcs", {}),
            "payload": status_data.get("payload", {}),
            "cdh": status_data.get("cdh", {}),
            "overall_status": self._assess_overall_status(status_data)
        }
        
        return telemetry

    def _assess_overall_status(self, status_data):
        """
        Assess overall system health
        """
        subsystem_statuses = []
        
        for subsystem in ["power", "thermal", "communication", "adcs", "payload", "cdh"]:
            if subsystem in status_data:
                subsystem_statuses.append(status_data[subsystem].get("status", "UNKNOWN"))
        
        if "CRITICAL" in subsystem_statuses:
            return "CRITICAL"
        elif "NOT OK" in subsystem_statuses or "WARNING" in subsystem_statuses:
            return "ANOMALIES_DETECTED"
        else:
            return "NOMINAL"

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
        """
        Send regular status pings
        """
        try:
            ping_data = {
                "type": "ping",
                "timestamp": datetime.now().isoformat(),
                "phase": self.current_phase,
                "status": "alive"
            }
            # This would be sent via downlink in real implementation
            print(f"FSM: Ping sent - Phase: {self.current_phase}")
        except Exception as e:
            print(f"FSM: Ping error: {e}")


    def default(self):
        """
        Initates the Default state the cubesat should be in

        send regular pings + wait for command to initiate some phase
        """
        self.current_phase = "default"
        print("FSM: Entering default state")
        
        while self.running and self.current_phase == "default":
            self._pings()
            time.sleep(30)  # Send pings every 30 seconds

    def phase1(self):
        """
        Initiates Phase 1

        run health check stuff and goes back to default
        """
        self.current_phase = "phase1"
        print("FSM: Starting Phase 1 - Health Check")
        
        try:
            # Perform comprehensive health check
            telemetry = self.get_telemetry_data()
            
            # Store results
            self.phase_results["phase1"] = {
                "completed": True,
                "timestamp": datetime.now().isoformat(),
                "telemetry": telemetry,
                "status": telemetry["overall_status"]
            }
            
            print(f"FSM: Phase 1 completed - Status: {telemetry['overall_status']}")
            
            # Return to default state
            time.sleep(5)  # Brief pause before returning to default
            self.default()
            
        except Exception as e:
            print(f"FSM: Phase 1 error: {e}")
            self.phase_results["phase1"] = {
                "completed": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.default()

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
