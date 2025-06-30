"""
Gets basic stats from the rpi and camera

Refer to this video for reference: https://www.youtube.com/watch?v=znKICgLJZhI
"""

import subprocess
from pyembedded.raspberry_pi_tools.raspberrypi import PI
from Camera import Camera


class status:
    # Backend Code. Relavant functions for the GUI are below
    def __init__(self):
        # Initialising
        self.pi = PI()
        self.camera = Camera()
        self.command = ["iw", "dev", "wlan0", "link"]

    # Checks if Pi is Detected
    def pidetect(self, func):
        try:
            return func()
        except Exception as e:
            return e

    def pidetecta(self, func, index):
        try:
            return func()[index]
        except Exception as e:
            return e

    # Runs a console command 
    def runcommand(self, command):
        try:
            return subprocess.check_output(command, text=True)
        except subprocess.CalledProcessError as e:
            return e

    # Parses Data returned from iwconfig command
    def parseinfo(iw_output, n):
        info = []
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
    def pitemp(self):
        x = self.pidetect(self.pi.get_cpu_temp)
        return x  # returns cpu temperature

    # returns cpu usage
    def piuse(self):
        x = self.pidetect(self.pi.get_cpu_usage)
        return x  # returns cpu usage as a %

    # returns disk space
    def pidisk(self):
        x = self.pidetecta(self.pi.get_disk_space, 3)
        return x  # returns disk usage

    # returns ram
    def piusedram(self):
        x = self.pidetecta(self.pi.get_ram_info, 1)
        return x  # returns Used RAM

    def pifreeram(self):
        x = self.pidetecta(self.pi.get_ram_info, 2)
        return x  # returns Free RAM

    # returns wifi status
    def piwifiquality(self):
        x = self.pidetecta(self.pi.get_wifi_status, 1)
        return x  # returns wifi quality

    # returns wifi strength
    def piwifistrength(self):
        x = self.parseinfo(self.runcommand(self.command), 0)
        return x  # Strength in dBm

    # returns wifi frequency
    def piwififreq(self):
        x = self.parseinfo(self.runcommand(self.command), 1)
        return x  # returns wifi frequency in MHz

    # returns wifi tx bitrate
    def piwifitxbitrate(self):
        x = self.parseinfo(self.runcommand(self.command), 2)
        return x  # returns wifi tx bitrate in Mbps

    # returns ip address
    def piip(self):
        x = self.pidetect(self.pi.get_connected_ip_addr(network='wlan0'))
        return x  # returns the ip address of the connected network

    # returns camera status
    def GetCameraStatus(self):
        x = self.pidetect(self.camera.GetStatus)
        return x  # returns camera status
