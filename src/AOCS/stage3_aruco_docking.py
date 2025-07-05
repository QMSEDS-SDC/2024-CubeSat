import time
import smbus
import RPi.GPIO as GPIO
import numpy as np
import json
import threading
from queue import Queue
import socket
import struct

# Pin Configuration (same as previous scripts)
IN1 = 17     # GPIO17 (Pin 11) - Motor direction pin 1
IN2 = 27     # GPIO27 (Pin 13) - Motor direction pin 2
ENA = 18     # GPIO18 (Pin 12) - PWM pin for controlling motor speed (EnA)

# MPU9250 I2C Configuration
MPU9250_ADDR = 0x68
I2C_BUS = 1
GYRO_XOUT_H = 0x43
GYRO_XOUT_L = 0x44
GYRO_YOUT_H = 0x45
GYRO_YOUT_L = 0x46
GYRO_ZOUT_H = 0x47
GYRO_ZOUT_L = 0x48
PWR_MGMT_1 = 0x6B
GYRO_CONFIG = 0x1B

class AOCSArUcoDocking:
    def __init__(self, communication_port=8888):
        self.current_angle = 0.0
        self.target_angle = 0.0
        self.gyro_bias = 0.0
        self.is_moving = False
        self.is_docking = False
        self.communication_port = communication_port

        # Docking parameters
        self.docking_tolerance = 1.0  # degrees
        self.docking_max_speed = 25   # slower speed for precision
        self.correction_interval = 1.0  # seconds between corrections

        # Control parameters - more conservative for docking
        self.Kp = 0.8
        self.Ki = 0.02
        self.Kd = 0.1

        # PID variables
        self.error_sum = 0
        self.last_error = 0

        # Filter parameters
        self.alpha = 0.85
        self.filtered_gyro = 0.0

        # Communication variables
        self.vision_data = {"angle_error": 0.0, "distance": 0.0, "detected": False}
        self.last_vision_update = 0

        # Initialize hardware
        self.setup_gpio()
        self.setup_i2c()
        self.initialize_mpu9250()
        self.load_initialization_data()

        # Start communication thread
        self.comm_thread = threading.Thread(target=self.communication_handler, daemon=True)
        self.comm_thread.start()

    def setup_gpio(self):
        """Setup GPIO pins for motor control"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ENA, GPIO.OUT)
        GPIO.setup(IN1, GPIO.OUT)
        GPIO.setup(IN2, GPIO.OUT)

        self.pwm = GPIO.PWM(ENA, 1000)
        self.pwm.start(0)

        # Ensure motor is stopped
        self.stop_motor()

    def setup_i2c(self):
        """Setup I2C communication"""
        self.bus = smbus.SMBus(I2C_BUS)

    def initialize_mpu9250(self):
        """Initialize the MPU9250 IMU"""
        self.bus.write_byte_data(MPU9250_ADDR, PWR_MGMT_1, 0x00)
        self.bus.write_byte_data(MPU9250_ADDR, GYRO_CONFIG, 0x00)
        time.sleep(0.1)

    def load_initialization_data(self):
        """Load initialization data from Stage 1"""
        try:
            with open("aocs_init_data.json", 'r') as f:
                init_data = json.load(f)
                self.gyro_bias = init_data.get("gyro_bias", 0.0)
                print(f"Loaded gyro bias: {self.gyro_bias:.3f} deg/s")
        except Exception as e:
            print(f"Warning: Could not load initialization data: {e}")
            self.gyro_bias = 0.0

    def read_gyro_data(self):
        """Read gyroscope data"""
        try:
            data = self.bus.read_i2c_block_data(MPU9250_ADDR, GYRO_XOUT_H, 6)

            gyro_z = (data[4] << 8) | data[5]
            if gyro_z > 32767:
                gyro_z -= 65536

            gyro_z = gyro_z / 131.0 - self.gyro_bias
            return gyro_z
        except Exception as e:
            print(f"Error reading gyroscope: {e}")
            return 0.0

    def set_motor_direction(self, direction):
        """Set motor direction: 1=forward, -1=reverse, 0=stop"""
        if direction > 0:
            GPIO.output(IN1, GPIO.HIGH)
            GPIO.output(IN2, GPIO.LOW)
        elif direction < 0:
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.HIGH)
        else:
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.LOW)

    def set_motor_speed(self, speed):
        """Set motor speed (0-100%)"""
        speed = max(0, min(100, abs(speed)))
        self.pwm.ChangeDutyCycle(speed)

    def stop_motor(self):
        """Stop the motor"""
        self.set_motor_direction(0)
        self.set_motor_speed(0)

    def normalize_angle(self, angle):
        """Normalize angle to [-180, 180] range"""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle

    def update_current_angle(self, dt):
        """Update current angle based on gyroscope integration"""
        gyro_z = self.read_gyro_data()

        # Apply complementary filter
        self.filtered_gyro = self.alpha * self.filtered_gyro + (1 - self.alpha) * gyro_z

        # Integrate to get angle (simple integration)
        self.current_angle += self.filtered_gyro * dt

        # Normalize angle
        self.current_angle = self.normalize_angle(self.current_angle)

        return self.filtered_gyro

    def communication_handler(self):
        """Handle communication with vision system"""
        try:
            # Create socket server to receive vision data
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', self.communication_port))
            server_socket.listen(1)

            print(f"Listening for vision system on port {self.communication_port}")

            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    print(f"Vision system connected from {addr}")

                    while True:
                        # Receive data: angle_error (float), distance (float), detected (bool)
                        data = client_socket.recv(13)  # 4 + 4 + 1 bytes
                        if not data:
                            break

                        # Unpack data
                        angle_error, distance, detected_byte = struct.unpack('ffB', data)
                        detected = bool(detected_byte)

                        # Update vision data
                        self.vision_data = {
                            "angle_error": angle_error,
                            "distance": distance,
                            "detected": detected
                        }
                        self.last_vision_update = time.time()

                        # Send acknowledgment
                        ack = struct.pack('B', 1)
                        client_socket.send(ack)

                except Exception as e:
                    print(f"Communication error: {e}")
                    time.sleep(1)

        except Exception as e:
            print(f"Communication handler error: {e}")

    def rotate_360_degrees(self, angular_velocity=20):
        """
        Rotate 360 degrees at specified angular velocity (slower for ArUco detection)
        angular_velocity: desired rotation speed in deg/s
        """
        print(f"Starting 360° rotation at {angular_velocity} deg/s for ArUco detection")

        start_angle = self.current_angle
        target_total_rotation = 360.0
        total_rotation = 0.0

        # Determine direction (positive angular velocity = forward)
        direction = 1 if angular_velocity > 0 else -1
        target_gyro = abs(angular_velocity)

        dt = 0.02  # 50Hz control loop
        self.is_moving = True

        # Store detected ArUco positions during rotation
        aruco_detections = []

        try:
            while total_rotation < target_total_rotation and self.is_moving:
                start_time = time.time()

                # Update angle
                current_gyro = self.update_current_angle(dt)

                # Check for ArUco detection
                if self.vision_data["detected"]:
                    detection_info = {
                        "angle": self.current_angle,
                        "angle_error": self.vision_data["angle_error"],
                        "distance": self.vision_data["distance"],
                        "timestamp": time.time()
                    }
                    aruco_detections.append(detection_info)
                    print(f"ArUco detected at angle {self.current_angle:.1f}°, "
                          f"error: {self.vision_data['angle_error']:.1f}°")

                # Calculate total rotation
                angle_change = abs(self.current_angle - start_angle)
                if angle_change > 180:
                    angle_change = 360 - angle_change
                total_rotation = angle_change

                # Speed control using gyroscope feedback
                gyro_error = target_gyro - abs(current_gyro)

                # Simple proportional control for speed
                speed_adjustment = gyro_error * 2.0
                base_speed = 30  # Slower base speed for ArUco detection
                motor_speed = max(20, min(60, base_speed + speed_adjustment))

                self.set_motor_direction(direction)
                self.set_motor_speed(motor_speed)

                print(f"Rotation: {total_rotation:.1f}°/{target_total_rotation}°, "
                      f"Gyro: {current_gyro:.1f} deg/s, ArUco: {self.vision_data['detected']}")

                # Maintain loop timing
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("360° rotation interrupted")
        finally:
            self.stop_motor()
            self.is_moving = False
            print(f"360° rotation completed. ArUco detections: {len(aruco_detections)}")

            # Return detection data
            return aruco_detections

    def move_to_angle_vision_assisted(self, target_angle, max_speed=40):
        """
        Move to specific angle with vision assistance
        target_angle: target angle in degrees
        max_speed: maximum motor speed (0-100%)
        """
        self.target_angle = self.normalize_angle(target_angle)
        print(f"Moving to angle: {self.target_angle:.1f}° with vision assistance")

        dt = 0.02  # 50Hz control loop
        self.is_moving = True
        self.error_sum = 0
        self.last_error = 0

        tolerance = self.docking_tolerance
        settled_count = 0
        required_settled_count = 25  # Must be settled longer for precision

        try:
            while self.is_moving:
                start_time = time.time()

                # Update current angle
                self.update_current_angle(dt)

                # Calculate error from gyroscope
                gyro_error = self.target_angle - self.current_angle
                gyro_error = self.normalize_angle(gyro_error)

                # Use vision correction if available and recent
                final_error = gyro_error
                if (self.vision_data["detected"] and
                    time.time() - self.last_vision_update < 0.5):
                    # Combine gyro and vision errors
                    vision_error = self.vision_data["angle_error"]
                    # Weight more heavily on vision when close
                    vision_weight = min(1.0, abs(gyro_error) / 10.0)
                    final_error = vision_weight * vision_error + (1 - vision_weight) * gyro_error
                    print(f"Vision-assisted: Gyro error: {gyro_error:.1f}°, "
                          f"Vision error: {vision_error:.1f}°, Final: {final_error:.1f}°")

                # Check if we're within tolerance
                if abs(final_error) < tolerance:
                    settled_count += 1
                    if settled_count >= required_settled_count:
                        print(f"Target reached! Current angle: {self.current_angle:.1f}°")
                        break
                else:
                    settled_count = 0

                # PID control with more conservative parameters
                self.error_sum += final_error * dt
                self.error_sum = max(-30, min(30, self.error_sum))  # Anti-windup

                error_rate = (final_error - self.last_error) / dt if dt > 0 else 0
                self.last_error = final_error

                control_output = (self.Kp * final_error +
                                self.Ki * self.error_sum +
                                self.Kd * error_rate)

                # Convert to motor commands
                if abs(control_output) < 3:
                    # Smaller dead zone for precision
                    self.stop_motor()
                else:
                    direction = 1 if control_output > 0 else -1
                    speed = min(abs(control_output), max_speed)

                    # Reduce speed when very close to target
                    if abs(final_error) < 5:
                        speed = max(speed * 0.5, 15)  # Minimum speed for movement

                    self.set_motor_direction(direction)
                    self.set_motor_speed(speed)

                print(f"Current: {self.current_angle:.1f}°, Target: {self.target_angle:.1f}°, "
                      f"Error: {final_error:.1f}°, Speed: {speed:.0f}%")

                # Maintain loop timing
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("Movement interrupted")
        finally:
            self.stop_motor()
            self.is_moving = False

    def real_time_docking(self, max_corrections=50):
        """
        Real-time docking with continuous vision feedback
        max_corrections: maximum number of correction attempts
        """
        print("Starting real-time docking procedure...")
        self.is_docking = True
        correction_count = 0

        try:
            while self.is_docking and correction_count < max_corrections:
                start_time = time.time()

                # Wait for fresh vision data
                if not self.vision_data["detected"]:
                    print("Waiting for ArUco detection...")
                    time.sleep(0.1)
                    continue

                # Check if vision data is recent
                if time.time() - self.last_vision_update > 2.0:
                    print("Vision data too old, waiting for update...")
                    time.sleep(0.1)
                    continue

                angle_error = self.vision_data["angle_error"]
                distance = self.vision_data["distance"]

                print(f"Docking correction {correction_count + 1}: "
                      f"Angle error: {angle_error:.2f}°, Distance: {distance:.2f}")

                # Check if we're close enough to consider docked
                if abs(angle_error) < self.docking_tolerance and distance < 5.0:
                    print("Docking successful! Target aligned.")
                    break

                # Calculate required movement
                if abs(angle_error) > self.docking_tolerance:
                    # Make small correction movement
                    correction_angle = angle_error * 0.8  # Reduce overshoot

                    print(f"Making correction: {correction_angle:.2f}°")

                    # Use vision-assisted movement for precision
                    self.move_to_angle_vision_assisted(
                        self.current_angle + correction_angle,
                        self.docking_max_speed
                    )

                    correction_count += 1

                    # Wait a moment for system to settle
                    time.sleep(0.5)
                else:
                    # Angle is good, just waiting for distance
                    print("Angle aligned, monitoring distance...")
                    time.sleep(0.2)

                # Maintain correction interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.correction_interval - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("Docking interrupted")
        finally:
            self.stop_motor()
            self.is_docking = False

            if correction_count >= max_corrections:
                print(f"Docking failed: Maximum corrections ({max_corrections}) reached")
                return False
            else:
                print("Docking procedure completed")
                return True

    def process_command(self, command):
        """
        Process movement command for Stage 3
        """
        try:
            if command["type"] == "rotate_360":
                speed = command.get("speed", 20)  # Slower default for ArUco
                detections = self.rotate_360_degrees(speed)
                return {"status": "completed", "detections": len(detections),
                       "detection_data": detections}

            elif command["type"] == "move_to_angle":
                angle = command["angle"]
                speed = command.get("speed", 40)
                self.move_to_angle_vision_assisted(angle, speed)
                return {"status": "completed", "final_angle": self.current_angle}

            elif command["type"] == "dock":
                max_corrections = command.get("max_corrections", 50)
                success = self.real_time_docking(max_corrections)
                return {"status": "completed" if success else "failed",
                       "docked": success}

            else:
                return {"status": "error", "message": "Unknown command type"}

        except Exception as e:
            self.stop_motor()
            return {"status": "error", "message": str(e)}

    def get_current_status(self):
        """Get comprehensive status information"""
        return {
            "current_angle": self.current_angle,
            "target_angle": self.target_angle,
            "is_moving": self.is_moving,
            "is_docking": self.is_docking,
            "gyro_reading": self.filtered_gyro,
            "vision_data": self.vision_data,
            "vision_age": time.time() - self.last_vision_update if self.last_vision_update > 0 else float('inf')
        }

    def emergency_stop(self):
        """Emergency stop function"""
        self.is_moving = False
        self.is_docking = False
        self.stop_motor()
        print("Emergency stop activated")

    def cleanup(self):
        """Clean up resources"""
        self.emergency_stop()
        if hasattr(self, 'pwm'):
            self.pwm.stop()
        GPIO.cleanup()
        print("Cleanup completed")

def main():
    aocs = AOCSArUcoDocking()

    try:
        print("=== AOCS Stage 3: ArUco Tracking and Docking ===")
        print("Commands:")
        print("1. '360 [speed]' - Rotate 360 degrees for ArUco detection")
        print("2. 'move [angle] [speed]' - Move to specific angle with vision")
        print("3. 'dock [max_corrections]' - Real-time docking procedure")
        print("4. 'status' - Show current status including vision data")
        print("5. 'stop' - Emergency stop")
        print("6. 'quit' - Exit program")
        print("\nNote: Make sure vision system is connected on port 8888")
        print()

        while True:
            try:
                user_input = input("Enter command: ").strip().lower()

                if user_input == 'quit':
                    break
                elif user_input == 'status':
                    status = aocs.get_current_status()
                    print(f"Current angle: {status['current_angle']:.1f}°")
                    print(f"Target angle: {status['target_angle']:.1f}°")
                    print(f"Moving: {status['is_moving']}")
                    print(f"Docking: {status['is_docking']}")
                    print(f"Gyro: {status['gyro_reading']:.1f} deg/s")
                    print(f"ArUco detected: {status['vision_data']['detected']}")
                    if status['vision_data']['detected']:
                        print(f"  Angle error: {status['vision_data']['angle_error']:.2f}°")
                        print(f"  Distance: {status['vision_data']['distance']:.2f}")
                        print(f"  Data age: {status['vision_age']:.1f}s")
                elif user_input == 'stop':
                    aocs.emergency_stop()
                elif user_input.startswith('360'):
                    parts = user_input.split()
                    speed = float(parts[1]) if len(parts) > 1 else 20
                    command = {"type": "rotate_360", "speed": speed}
                    result = aocs.process_command(command)
                    print(f"Result: {result}")
                elif user_input.startswith('move'):
                    parts = user_input.split()
                    if len(parts) >= 2:
                        angle = float(parts[1])
                        speed = float(parts[2]) if len(parts) > 2 else 40
                        command = {"type": "move_to_angle", "angle": angle, "speed": speed}
                        result = aocs.process_command(command)
                        print(f"Result: {result}")
                    else:
                        print("Usage: move [angle] [optional_speed]")
                elif user_input.startswith('dock'):
                    parts = user_input.split()
                    max_corrections = int(parts[1]) if len(parts) > 1 else 50
                    command = {"type": "dock", "max_corrections": max_corrections}
                    result = aocs.process_command(command)
                    print(f"Result: {result}")
                else:
                    print("Unknown command")

            except ValueError:
                print("Invalid number format")
            except KeyboardInterrupt:
                print("\nOperation interrupted")
                break

    except Exception as e:
        print(f"Error: {e}")
    finally:
        aocs.cleanup()

if __name__ == "__main__":
    main()