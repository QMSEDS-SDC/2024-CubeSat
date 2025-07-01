import time
import smbus
import RPi.GPIO as GPIO


# Pin Configuration based on provided pin allocation
# L298N Motor Driver Pins
IN1 = 17     # GPIO17 (Pin 11) - Motor direction pin 1
IN2 = 27     # GPIO27 (Pin 13) - Motor direction pin 2
ENA = 18     # GPIO18 (Pin 12) - PWM pin for controlling motor speed (EnA)

# MPU9250 I2C Configuration
# The MPU9250 is connected to the I2C bus (SDA: GPIO2/Pin 3, SCL: GPIO3/Pin 5)
MPU9250_ADDR = 0x68  # Default I2C address of MPU9250
I2C_BUS = 1          # Raspberry Pi I2C bus number

# MPU9250 Register Addresses
GYRO_XOUT_H = 0x43
GYRO_XOUT_L = 0x44
GYRO_YOUT_H = 0x45
GYRO_YOUT_L = 0x46
GYRO_ZOUT_H = 0x47
GYRO_ZOUT_L = 0x48
PWR_MGMT_1 = 0x6B
GYRO_CONFIG = 0x1B

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

# Setup PWM for motor speed control
pwm = GPIO.PWM(ENA, 1000)  # 1000 Hz frequency
pwm.start(0)                # Start with 0% duty cycle (motor off)

# Initialise I2C
bus = smbus.SMBus(I2C_BUS)


# Initialise MPU9250
def initialise_mpu9250():
    """Initialise the MPU9250 IMU"""
    try:
        # Wake up the MPU9250
        bus.write_byte_data(MPU9250_ADDR, PWR_MGMT_1, 0x00)

        # Configure gyroscope range to ±250 degrees/s
        # 0x00 = 250 degrees/s, 0x08 = 500 degrees/s, 0x10 = 1000 degrees/s, 0x18 = 2000 degrees/s
        bus.write_byte_data(MPU9250_ADDR, GYRO_CONFIG, 0x00)

        time.sleep(0.1)  # Allow time for device to stabilise
        print("MPU9250 IMU initialised successfully")
        return True
    except Exception as e:
        print(f"Failed to initialise MPU9250 IMU: {e}")
        return False


# Read gyroscope data
def read_gyro_data():
    """Read raw gyroscope data from MPU9250"""
    try:
        # Read 6 bytes of data from register GYRO_XOUT_H
        data = bus.read_i2c_block_data(MPU9250_ADDR, GYRO_XOUT_H, 6)

        # Convert the data
        gyro_x = (data[0] << 8) | data[1]
        gyro_y = (data[2] << 8) | data[3]
        gyro_z = (data[4] << 8) | data[5]

        # Convert to signed values
        if gyro_x > 32767:
            gyro_x -= 65536
        if gyro_y > 32767:
            gyro_y -= 65536
        if gyro_z > 32767:
            gyro_z -= 65536

        # Convert to degrees per second (depends on the range set in GYRO_CONFIG)
        # For ±250 degrees/s range, sensitivity is 131 LSB/(degrees/s)
        gyro_x = gyro_x / 131.0
        gyro_y = gyro_y / 131.0
        gyro_z = gyro_z / 131.0

        return {'x': gyro_x, 'y': gyro_y, 'z': gyro_z}
    except Exception as e:
        print(f"Error reading gyroscope data: {e}")
        return {'x': 0, 'y': 0, 'z': 0}


# Control Parameters
Kp = 2.0  # Proportional gain - adjust based on your system's response
Ki = 0.1  # Integral gain
Kd = 0.5  # Derivative gain

# Filter parameters
alpha = 0.7  # Complementary filter coefficient (0 < alpha < 1)

# Variables for PID control
error_sum = 0
last_error = 0
filtered_gyro_z = 0


def set_motor_direction(direction):
    """
    Sets the motor direction
    direction: 1 for forward, -1 for reverse, 0 for stop
    """
    if direction > 0:
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
    elif direction < 0:
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
    else:
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.LOW)


def set_motor_speed(speed):
    """
    Sets the motor speed via PWM
    speed: 0-100 (percentage of maximum speed)
    """
    # Ensure speed is within valid range
    speed = max(0, min(100, speed))
    pwm.ChangeDutyCycle(speed)


def read_angular_velocity():
    """
    Reads angular velocity from the IMU
    Returns: angular velocity around z-axis in degrees per second
    """
    gyro = read_gyro_data()
    return gyro['z']  # Extract z-axis angular velocity


def detumbling_control():
    """
    Implements detumbling control to bring angular velocity to zero
    """
    global error_sum, last_error, filtered_gyro_z

    try:
        print("Starting detumbling control mode...")
        print("Press Ctrl+C to stop")

        # Control loop
        dt = 0.01  # 10ms control period
        while True:
            start_time = time.time()

            # Read current angular velocity
            current_gyro_z = read_angular_velocity()

            # Apply complementary filter to smooth readings
            filtered_gyro_z = alpha * filtered_gyro_z + (1 - alpha) * current_gyro_z

            # Calculate error (desired angular velocity is zero)
            error = 0 - filtered_gyro_z

            # Update integral term with anti-windup
            error_sum += error * dt
            error_sum = max(-50, min(50, error_sum))  # Limit integral term

            # Calculate derivative term
            error_rate = (error - last_error) / dt if dt > 0 else 0
            last_error = error

            # PID control output
            control_output = Kp * error + Ki * error_sum + Kd * error_rate

            # Determine motor direction and speed
            if abs(control_output) < 5:
                # Dead zone to prevent motor oscillation at low speeds
                speed = 0
                set_motor_direction(0)
                set_motor_speed(0)
            else:
                direction = 1 if control_output > 0 else -1
                speed = min(abs(control_output), 100)  # Limit to valid PWM range
                set_motor_direction(direction)
                set_motor_speed(speed)

            # Debug output
            print(f"Angular Velocity: {filtered_gyro_z:.2f} deg/s, Control Output: {control_output:.2f}, PWM: {speed:.1f}%")

            # Calculate loop time and sleep to maintain consistent dt
            elapsed = time.time() - start_time
            sleep_time = max(0, dt - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("Detumbling control stopped by user")
    finally:
        # Cleanup
        pwm.stop()
        GPIO.cleanup()
        print("GPIO cleaned up")


if __name__ == "__main__":
    # Initialise the IMU
    if not initialise_mpu9250():
        GPIO.cleanup()
        exit(1)

    # Calibration period to let sensors stabilise
    print("Initialising and calibrating sensors. Please keep the system stationary...")
    time.sleep(2)

    # Run detumbling control
    detumbling_control()
