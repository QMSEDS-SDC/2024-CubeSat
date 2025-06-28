import json
import datetime
import os

class apilogs:
    # Initialises
    def __init__(self):
        self.data = {"Logs": []}
    # Creates a new log entry
    def newlog(self, msg):
        output = {
            "D-T": datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S:%f"),
            "msg": msg
        }
        return output 
    # Initialises the log file
    def initialiselog(self):
        self.data["Logs"].append(self.newlog("New Log File Created"))
        with open('APILogs.json', 'w') as file:
            json.dump(self.data, file, indent=4)
    # Adds a log entry to the log file
    def addlog(self, msg):
        if not os.path.exists('APILogs.json'):
            self.initialiselog()
        with open('APILogs.json', 'r+') as file:
            data = json.load(file)
            data["Logs"].append(self.newlog(msg))
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
