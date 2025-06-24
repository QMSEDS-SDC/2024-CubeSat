#ifndef CAMERA_H
#define CAMERA_H
#include <ctime>
#include <iostream>
#include <vector>
#include <raspicam/raspicam.h>
using namespace std;

class Camera {
    private:
        raspicam::RaspiCam cam;  
        cv::Mat image;  
    public:
        Camera();
        ~Camera();
        int BootCamera();
        int CaptureFrame();
        int CloseCamera();
};