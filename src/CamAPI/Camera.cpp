#include <Camera.h>
using namespace std;

// Constructor
Camera::Camera () {}
// Destructor
Camera::~Camera () {
  CloseCamera();
}

int BootCamera()
{
  cam.set( CV_CAP_PROP_FORMAT, CV_8UC1 ); // Sets Camera Format
  if (!cam.open())
  {
    cerr<<"Error opening the camera"<<endl;
    return -1;
  }
  else
  {
    cout<<"Camera Open (Sleeping for 3secs)"<<endl;
    sleep(3);
     return 0;
  }
}

unsigned char* CaptureFrame()
{
  // Grabs Frame and Saves as a JPEG
  cam.grab();  
  cam.retrieve(image);
  return image.data;
}

    
int CloseCamera()
{
  // Closes Camera
  cam.realease();
  cam.close();
}
      
