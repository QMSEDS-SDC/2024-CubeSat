#include <iostream>

extern "C" {

    // Instruction for AOCS (angle and velocity)
    void RotationInsc(double angle, double vlcty) 
    {
        double out1 = angle;
        double out2 = vlcty;
        // Placeholder for the actual implementation
        std::cout << "RotationInsc called with angle: " << out1 << " and velocity: " << out2 << std::endl;
    }

    double Returnangle()
    {
        // Placeholder for the actual implementation
        double outangle = 45.0; // Example angle
        std::cout << "Returnangle called, returning angle: " << outangle << std::endl;
        return outangle;
    }

}