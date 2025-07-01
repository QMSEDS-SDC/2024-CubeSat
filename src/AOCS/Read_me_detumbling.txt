# Reaction Wheel Detumbling Control System

This document provides instructions for implementing a detumbling control system using a reaction wheel DC motor with a Raspberry Pi Zero 2W.

## Hardware Requirements

- Raspberry Pi Zero 2W
- L298N motor driver
- MPU9250 IMU (Inertial Measurement Unit)
- DC motor (used as a reaction wheel)
- Appropriate power supply
- Connecting wires

## Pin Connections

Raspberry Pi Pin   | Connected To           | Function
------------------ | ---------------------- | ----------------------------------
Pin 1 (3V3_1)      | MPU9250 (VDD, CS)      | Supply voltage and I2C activation
Pin 2 (5V_2)       | L298N (Vss)            | Power supply from Pi to driver
Pin 3 (GPIO2/SDA1) | MPU9250 (SDA/MOSI)     | I2C data communication
Pin 5 (GPIO3/SCL)  | MPU9250 (SCL)          | I2C clock communication
Pin 11 (GPIO17)    | L298N (IN1)            | Motor direction (forward)
Pin 12 (GPIO18)    | L298N (EnA)            | Motor speed control (PWM)
Pin 13 (GPIO27)    | L298N (IN2)            | Motor direction (reverse)
Ground pins        | MPU9250, L298N grounds | Common ground

Note: The L298N pins OUT1/OUT2 connect directly to the motor, and the L298N 
requires an external power supply at pin 4 (U3).

## Software Setup

### 1. Update your Raspberry Pi

```
sudo apt-get update
sudo apt-get upgrade
```

### 2. Enable I2C Interface

```
sudo raspi-config
```
Navigate to: Interface Options → I2C → Enable → Yes → Finish

### 3. Install Required Dependencies

```
sudo apt-get install python3-pip python3-smbus
sudo pip3 install RPi.GPIO numpy
```

### 4. Download the Script

Create the script:

```
nano detumbling_control.py
```
Then paste the script contents and save (Ctrl+X, Y, Enter).

### 5. Set Proper Permissions

```
chmod +x detumbling_control.py
```

## Running the System

Execute the script with:

```
sudo python3 detumbling_control.py
```

The script needs to be run with `sudo` because it accesses GPIO pins which require
root privileges.

## Control Parameters

The script uses a PID controller with the following default parameters:

```
Kp = 0.8  # Proportional gain
Ki = 0.1  # Integral gain
Kd = 0.2  # Derivative gain
```

You may need to tune these parameters based on your specific setup:
- Increase Kp for faster response
- Increase Ki to reduce steady-state error
- Increase Kd to reduce overshoot and oscillations

## Monitoring and Debugging

The script will print real-time data to the console:
- Current angular velocity (degrees/second)
- Control output
- PWM duty cycle (%)

Example output:
```
Angular Velocity: -2.14 deg/s, Control Output: 1.71, PWM: 1.7%
```

## Stopping the System

Press Ctrl+C to stop the script. The GPIO pins will be cleaned up automatically 
upon exit.

## Troubleshooting

### I2C Address Issues
If the IMU is not detected, check the actual address of your MPU9250:
```
sudo i2cdetect -y 1
```
Then update the MPU9250_ADDR variable in the script with the correct address.

### Permission Errors
Ensure you're running the script with sudo privileges.

### GPIO Conflicts
Make sure no other program is using the same GPIO pins.

### Motor Not Responding
- Check all physical connections
- Verify the L298N has appropriate power
- Ensure the PWM duty cycle is high enough to overcome motor inertia

## Working Principle

The detumbling control system works by:
1. Reading angular velocity from the MPU9250 IMU
2. Filtering the readings to reduce noise
3. Calculating the error from the desired angular velocity (zero)
4. Applying PID control to determine the appropriate motor response
5. Driving the motor in the direction that will counteract the rotation

This creates a negative feedback loop that stabilizes the system by bringing its
angular velocity to zero.