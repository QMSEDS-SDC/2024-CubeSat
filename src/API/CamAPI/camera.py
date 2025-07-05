import subprocess
import logging
import cv2
import numpy as np
from threading import Thread, Event
import queue
import time
import os

# Setup logging
logger = logging.getLogger(__name__)


class CameraNotFound(Exception):
    def __init__(self, message="No cameras available"):
        self.message = message
        super().__init__(self.message)


class Camera:
    """
    Handles the RPi's own camera module - provides live frame streaming using rpicam-vid
    """

    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.frame_size = width * height * 3 // 2  # YUV420 size
        self.process = None
        self.streaming = False
        self.frame_queue = queue.Queue(maxsize=5)  # Buffer for frames
        self.stop_event = Event()
        self.capture_thread = None

        # Check if camera is available during initialisation
        self._check_camera_availability()

    def _check_camera_availability(self):
        """Check if camera is available using rpicam-hello"""
        try:
            result = subprocess.run(
                ["rpicam-hello", "--timeout", "1000"],  # 1 second test
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            output = result.stdout + result.stderr
            logger.debug(f"Camera check output: {output}")

            if "ERROR: *** no cameras available ***" in output:
                logger.error("No cameras available")
                raise CameraNotFound("No cameras available")
            elif "INFO Camera camera_manager.cpp" in output or "Preview" in output:
                logger.info("Camera detected and available")
                return True
            else:
                logger.warning("Unexpected camera check output, assuming camera is available")
                return True

        except subprocess.TimeoutExpired:
            logger.error("Camera check timeout")
            raise CameraNotFound("Camera check timeout")
        except FileNotFoundError:
            logger.error("rpicam-hello not found. Make sure rpicam-apps is installed.")
            raise CameraNotFound("rpicam-apps not installed")

    def start_streaming(self):
        """Start the camera streaming process"""
        if self.streaming:
            logger.warning("Camera is already streaming")
            return True

        try:
            # Start rpicam-vid process
            self.process = subprocess.Popen(
                [
                    "rpicam-vid",
                    "-t", "0",  # Continuous capture
                    "-o", "-",  # Output to stdout
                    "--codec", "yuv420",
                    "--width", str(self.width),
                    "--height", str(self.height),
                    "--framerate", "30",
                    "--nopreview"  # Don't show preview window
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )

            # Start capture thread
            self.stop_event.clear()
            self.capture_thread = Thread(target=self._capture_frames, daemon=True)
            self.capture_thread.start()

            self.streaming = True
            logger.info("Camera streaming started")

            # Give it a moment to initialise
            time.sleep(1)
            return True

        except Exception as e:
            logger.error(f"Failed to start camera streaming: {e}")
            self.stop_streaming()
            return False

    def _capture_frames(self):
        """Background thread to capture frames from the subprocess"""
        while not self.stop_event.is_set() and self.process:
            try:
                raw = self.process.stdout.read(self.frame_size)
                if not raw or len(raw) != self.frame_size:
                    logger.warning("Incomplete frame received")
                    continue

                # Convert YUV420 to BGR
                yuv = np.frombuffer(raw, dtype=np.uint8).reshape((self.height * 3 // 2, self.width))
                bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)

                # Add frame to queue (non-blocking)
                try:
                    self.frame_queue.put(bgr, block=False)
                except queue.Full:
                    # Remove oldest frame if queue is full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put(bgr, block=False)
                    except queue.Empty:
                        pass

            except Exception as e:
                if not self.stop_event.is_set():
                    logger.error(f"Error capturing frame: {e}")
                break

    def get_frame(self, timeout=1.0):
        """
        Get the latest frame from the camera
        Returns: numpy array (BGR image) or None if no frame available
        """
        if not self.streaming:
            logger.error("Camera is not streaming. Call start_streaming() first.")
            return None

        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            logger.warning("No frame available within timeout")
            return None

    def get_latest_frame(self):
        """
        Get the most recent frame, discarding older ones
        Returns: numpy array (BGR image) or None if no frame available
        """
        if not self.streaming:
            logger.error("Camera is not streaming. Call start_streaming() first.")
            return None

        latest_frame = None
        try:
            # Get all available frames, keeping only the latest
            while True:
                latest_frame = self.frame_queue.get_nowait()
        except queue.Empty:
            pass

        return latest_frame

    def stop_streaming(self):
        """Stop the camera streaming"""
        if not self.streaming:
            return

        logger.info("Stopping camera streaming...")

        # Signal threads to stop
        self.stop_event.set()

        # Terminate subprocess
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

        # Wait for capture thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)

        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        self.streaming = False
        logger.info("Camera streaming stopped")

    def is_streaming(self):
        """Check if camera is currently streaming"""
        return self.streaming

if __name__ == "__main__":
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cam = None
    try:
        cam = Camera(width=640, height=480)
        if cam.start_streaming():
            print("Camera streaming started. Capturing 10 frames...")
            for i in range(10):
                frame = cam.get_frame(timeout=2.0)
                if frame is not None:
                    filename = os.path.join(script_dir, f"frame_{i+1}.jpg")
                    cv2.imwrite(filename, frame)
                    print(f"Saved {filename}")
                else:
                    print(f"Frame {i+1} not available.")
            cam.stop_streaming()
            print("Camera streaming stopped.")
        else:
            print("Failed to start camera streaming.")
    except CameraNotFound as e:
        print(f"Camera error: {e}")
    finally:
        if cam and cam.is_streaming():
            cam.stop_streaming()
