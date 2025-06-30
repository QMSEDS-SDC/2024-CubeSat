"""
Gets basic stats from the rpi and camera

Refer to this video for reference: https://www.youtube.com/watch?v=znKICgLJZhI
"""

import subprocess
from pyembedded.raspberry_pi_tools.raspberrypi import PI
# from Camera import Camera


class status:
    # Backend Code. Relavant functions for the GUI are below
    def __init__(self):
        # Initialising
        self.pi = PI()
        # self.camera = Camera()
        self.command = ["iw", "dev", "wlan0", "link"]

    # Checks if Pi is Detected
    def pi_detect(self, func):
        try:
            return func()
        except Exception as e:
            return e

    def pi_detecta(self, func, index):
        try:
            return func()[index]
        except Exception as e:
            return e

    # Runs a console command
    def run_command(self, command):
        try:
            return subprocess.check_output(command, text=True)
        except subprocess.CalledProcessError as e:
            return e

    # Parses Data returned from iwconfig command
    def parse_info(self, iw_output, n):
        info = ["", "", ""]
        for line in iw_output.splitlines():
            line = line.strip()
            if line.startswith("signal:"):
                info[0] = line.split("signal:")[1].strip()
            elif line.startswith("freq:"):
                info[1] = line.split("freq:")[1].strip()
            elif line.startswith("tx bitrate:"):
                info[2] = line.split("tx bitrate:")[1].strip()
        return info[n]

    # Functions to get data for GUI

    # returns temp
    def pi_temp(self):
        x = self.pi_detect(self.pi.get_cpu_temp)
        return x  # returns cpu temperature

    # returns cpu usage
    def pi_use(self):
        x = self.pi_detect(self.pi.get_cpu_usage)
        return x  # returns cpu usage as a %

    # returns disk space
    def pi_disk(self):
        x = self.pi_detecta(self.pi.get_disk_space, 3)
        return x  # returns disk usage

    # returns ram
    def pi_used_ram(self):
        x = self.pi_detecta(self.pi.get_ram_info, 1)
        return x  # returns Used RAM

    def pi_free_ram(self):
        x = self.pi_detecta(self.pi.get_ram_info, 2)
        return x  # returns Free RAM

    # returns wifi status
    def pi_wifi_quality(self):
        x = self.pi_detecta(self.pi.get_wifi_status, 1)
        return x  # returns wifi quality

    # returns wifi strength
    def pi_wifi_strength(self):
        x = self.parse_info(self.run_command(self.command), 0)
        return x  # Strength in dBm

    # returns wifi frequency
    def pi_wifi_freq(self):
        x = self.parse_info(self.run_command(self.command), 1)
        return x  # returns wifi frequency in MHz

    # returns wifi tx bitrate
    def pi_wifi_tx_bitrate(self):
        x = self.parse_info(self.run_command(self.command), 2)
        return x  # returns wifi tx bitrate in Mbps

    """
    # returns camera status
    def GetCameraStatus(self):
        x = self.pi_detect(self.camera.GetStatus)
        return x  # returns camera status
    """


if __name__ == "__main__":
    status_rpi = status()
    print(status_rpi.pi_temp())
    print(status_rpi.pi_use())
    print(status_rpi.pi_disk())
    print(status_rpi.pi_used_ram())
    print(status_rpi.pi_free_ram())
    print(status_rpi.pi_wifi_quality())
    print(status_rpi.pi_wifi_strength())
    print(status_rpi.pi_wifi_freq())
    print(status_rpi.pi_wifi_tx_bitrate())
