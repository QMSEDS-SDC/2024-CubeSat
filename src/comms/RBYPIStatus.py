# Refer to this video for reference: https://www.youtube.com/watch?v=znKICgLJZhI & this library: https://pypi.org/project/pyembedded/
from pyembedded.raspberry_pi_tools.raspberrypi import PI

class status:
    
    def __init__(self):
        # Initialising
        self.pi = PI()
    
    # returns temp
    def pitemp(self):
        return self.pi.get_cpu_temp() # returns a single temperature value
    # returns cpu usage
    def piuse(self):
        return self.pi.get_cpu_usage() # returns a single percentage value
    # returns disk space
    def pidisk(self):
        return self.pi.get_disk_space() # returns an array in the format [total disk space, used disk space, free disk space, used disk space percentage]
    # returns ram
    def piram(self):
        return self.pi.get_ram_info() # retruns an array in the format [total ram, used ram, free ram]
    # returns wifi status
    def piwifi(self):
        return self.pi.get_wifi_status() # returns an array in the format [ssid, signal quality, signal strenth as a fraction of 70, signal strenth percentage]
    # returns ip address
    def piip(self):
         return self.pi.get_connected_ip_addr(network='wlan0') # returns the ip address of the connected network
    
    

