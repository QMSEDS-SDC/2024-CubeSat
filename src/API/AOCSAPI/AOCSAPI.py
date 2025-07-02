import detumbling_control as dc


def getangvel():
    # returns angular velocity about the z axis
    try:
        output = dc.read_angular_velocity()
        return output
    except Exception as e:
        return None

def detumble():
    # starts the detumbling process
    dc.detumbling_control()
