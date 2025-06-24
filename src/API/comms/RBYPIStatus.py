# Refer to this video for reference: https://www.youtube.com/watch?v=znKICgLJZhI & this library: https://pypi.org/project/pyembedded/
# Make sure to import iw using 'sudo apt install iw'
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
        return self.pidetect(self.pi.get_cpu_temp) # returns cpu temperature
    # returns cpu usage
    def piuse(self):
        return self.pidetect(self.pi.get_cpu_usage) # returns cpu usage as a %
    # returns disk space
    def pidisk(self):
        return self.pidetecta(self.pi.get_disk_space, 3) # returns disk usage
    # returns ram
    def piusedram(self):
        return self.pidetecta(self.pi.get_ram_info, 1) # returns Used RAM
    def pifreeram(self):
        return self.pidetecta(self.pi.get_ram_info, 2) # returns Free Ram
    # returns wifi status
    def piwifiquality(self):
        return self.pidetecta(self.pi.get_wifi_status, 1) # returns wifi quality
    # returns wifi strength
    def piwifistrength(self):
        return self.parseinfo(self.runcommand(self.command), 0) # Strength in dBm
    # returns wifi frequency
    def piwififreq(self):
        return self.parseinfo(self.runcommand(self.command), 1) # returns wifi frequency in MHz
    # returns wifi tx bitrate
    def piwifitxbitrate(self):
        return self.parseinfo(self.runcommand(self.command), 2) # returns wifi tx bitrate in Mbps
    # returns ip address
    def piip(self):
         return self.pidetect(self.pi.get_connected_ip_addr(network='wlan0')) # returns the ip address of the connected network
    # returns camera status
    def GetCameraStatus(self):
        return self.pidetect(self.camera.GetStatus())
