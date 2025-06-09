import ctypes

class aocsapi:
    # Initialising
    def __init__(self):
        self.lib = ctypes.CDLL("AOCS.so") # insert path of AOCS.so here
        self.lib.RotationInsc.argtypes = [ctypes.c_double, ctypes.c_double]
        self.lib.Returnangle.restype = ctypes.c_double

    def RotationInsc(self, x, y):
        self.lib.RotationInsc(x,y)

   
    def Returnangle(self):
        angle = self.lib.Returnangle()
        return angle