import detumbling_control as dc
from APILogs import apilogs

logs = apilogs()

def getangvel():
    # returns angular velocity about the z axis
    try:
        output = dc.read_angular_velocity()
        logs.addlog("Angular Velocity Request --- Value: " + str(output))
        return output
    except Exception as e:
        logs.addlog("Error in getangvel: " + str(e))
        return None

def detumble():
    # starts the detumbling process
    logs.addlog("Detumbling Started")
    dc.detumbling_control()
