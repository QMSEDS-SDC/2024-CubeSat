# distutils: language = c++
# distutils: sources = Camera.cpp

from libcpp.cv

cdef extern from "Camera.h":
  cdef cppclass Camera:
    Camera() except +
    int BootCamera();
    int CaptureFrame();
    int CloseCamera();

cdef extern from "raspicam/raspicam.h" namespace "raspicam":
    cdef cppclass RaspiCam:
        RaspiCam() except +
        bool open()
        void grab()
        void retrieve(unsigned char* data)
        void release()

cdef class PyCam:
    cdef Camera *cam
    cdef RaspiCam *raspicam
    def __cinit__(self):
        self.cam = new Camera()
    
    def __dealloc__(self):
        del self.cam

    def BootCamera(self):
        return self.cam.BootCamera()

    def CaptureFrame(self):
        return self.cam.CaptureFrame()

    def CloseCamera(self):
        return self.cam.CloseCamera()