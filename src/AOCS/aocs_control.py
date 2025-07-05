"""
Unified AOCS Control System for CubeSat
Combines health check, positioning, and ArUco docking functionality
"""

import time
import smbus
import RPi.GPIO as GPIO
import numpy as np
import json
import threading
import socket
import struct


class AOCSController:
    def __init__(self, constants=None, logger=None):
        """
        Initialise AOCS Controller with constants
        constants: dict containing hardware pins, addresses, and control parameters
        logger: function to handle log messages, signature: logger(level, message)
                levels: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
        """
        # Default constants
        self.constants = {
            "PINS": {
                "INA1": 17,
                "INA2": 27,
                "ENA": 18
            },
            "Address": {
                "MPU9250_ADDR": 0x68,
                "I2C_BUS": 1
            },
            "Gyro": {
                "GYRO_XOUT_H": 0x43,
                "GYRO_YOUT_H": 0x45,
                "GYRO_YOUT_L": 0x46,
                "GYRO_ZOUT_H": 0x47,
                "GYRO_ZOUT_L": 0x48,
                "PWR_MGMT_1": 0x6B,
                "GYRO_CONFIG": 0x1B,
                "GYRO_XOUT_L": 0x44
            },
            "PID": {
                "Kp": 1.2,
                "Ki": 0.05,
                "Kd": 0.15
            },
            "CONTROL": {
                "docking_tolerance": 1.0,
                "docking_max_speed": 25,
                "position_tolerance": 2.0,
                "detumbling_deadzone": 5,
                "filter_alpha": 0.8
            }
        }
        
        # Set up logging
        self.logger = logger if logger else self._default_logger
        
        # Update with provided constants
        if constants:
            self._update_constants(constants)
        
        # Extract frequently used constants
        self.IN1 = self.constants["PINS"]["INA1"]
        self.IN2 = self.constants["PINS"]["INA2"]
        self.ENA = self.constants["PINS"]["ENA"]
        self.MPU9250_ADDR = self.constants["Address"]["MPU9250_ADDR"]
        self.I2C_BUS = self.constants["Address"]["I2C_BUS"]
        
        # State variables
        self.current_angle = 0.0
        self.target_angle = 0.0
        self.gyro_bias = 0.0
        self.is_moving = False
        self.is_docking = False
        self.status = 0  # -1: failed, 0: ready, 1: initialised
        
        # Control parameters
        self.Kp = self.constants["PID"]["Kp"]
        self.Ki = self.constants["PID"]["Ki"]
        self.Kd = self.constants["PID"]["Kd"]
        
        # PID variables
        self.error_sum = 0
        self.last_error = 0
        
        # Filter parameters
        self.alpha = self.constants["CONTROL"]["filter_alpha"]
        self.filtered_gyro = 0.0
        
        # Vision communication
        self.communication_port = 8888
        self.vision_data = {"angle_error": 0.0, "distance": 0.0, "detected": False}
        self.last_vision_update = 0
        
        # Initialise hardware
        self.setup_gpio()
        self.setup_i2c()

    def _default_logger(self, level, message):
        """Default logger that does nothing - prevents errors if no logger provided"""
        pass

    def _update_constants(self, new_constants):
        """Recursively update constants dictionary"""
        for key, value in new_constants.items():
            if key in self.constants and isinstance(self.constants[key], dict) and isinstance(value, dict):
                self.constants[key].update(value)
            else:
                self.constants[key] = value

    def setup_gpio(self):
        """Setup GPIO pins for motor control"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.ENA, GPIO.OUT)
            GPIO.setup(self.IN1, GPIO.OUT)
            GPIO.setup(self.IN2, GPIO.OUT)

            self.pwm = GPIO.PWM(self.ENA, 1000)
            self.pwm.start(0)

            # Ensure motor is stopped
            self.stop_motor()
            self.logger('INFO', 'GPIO setup successful')
            return True
        except Exception as e:
            self.logger('ERROR', f'GPIO setup failed: {e}')
            return False

    def setup_i2c(self):
        """Setup I2C communication"""
        try:
            self.bus = smbus.SMBus(self.I2C_BUS)
            self.logger('INFO', 'I2C setup successful')
            return True
        except Exception as e:
            self.logger('ERROR', f'I2C setup failed: {e}')
            return False

    def initialise_mpu9250(self):
        """Initialise the MPU9250 IMU"""
        try:
            self.bus.write_byte_data(self.MPU9250_ADDR, self.constants["Gyro"]["PWR_MGMT_1"], 0x00)
            self.bus.write_byte_data(self.MPU9250_ADDR, self.constants["Gyro"]["GYRO_CONFIG"], 0x00)
            time.sleep(0.1)
            self.logger('INFO', 'MPU9250 IMU initialised successfully')
            return True
        except Exception as e:
            self.logger('ERROR', f'Failed to initialise MPU9250 IMU: {e}')
            return False

    def read_gyro_data(self):
        """Read gyroscope data"""
        try:
            data = self.bus.read_i2c_block_data(self.MPU9250_ADDR, self.constants["Gyro"]["GYRO_XOUT_H"], 6)

            gyro_x = (data[0] << 8) | data[1]
            gyro_y = (data[2] << 8) | data[3]
            gyro_z = (data[4] << 8) | data[5]

            if gyro_x > 32767: gyro_x -= 65536
            if gyro_y > 32767: gyro_y -= 65536
            if gyro_z > 32767: gyro_z -= 65536

            gyro_x = gyro_x / 131.0
            gyro_y = gyro_y / 131.0
            gyro_z = gyro_z / 131.0 - self.gyro_bias

            return {'x': gyro_x, 'y': gyro_y, 'z': gyro_z}
        except Exception as e:
            self.logger('ERROR', f'Error reading gyroscope: {e}')
            return {'x': 0, 'y': 0, 'z': 0}

    def set_motor_direction(self, direction):
        """Set motor direction: 1=forward, -1=reverse, 0=stop"""
        if direction > 0:
            GPIO.output(self.IN1, GPIO.HIGH)
            GPIO.output(self.IN2, GPIO.LOW)
        elif direction < 0:
            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.HIGH)
        else:
            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.LOW)

    def set_motor_speed(self, speed):
        """Set motor speed (0-100%)"""
        speed = max(0, min(100, abs(speed)))
        self.pwm.ChangeDutyCycle(speed)

    def stop_motor(self):
        """Stop the motor"""
        self.set_motor_direction(0)
        self.set_motor_speed(0)

    def normalise_angle(self, angle):
        """Normalise angle to [-180, 180] range"""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle

    def update_current_angle(self, dt):
        """Update current angle based on gyroscope integration"""
        gyro_data = self.read_gyro_data()
        gyro_z = gyro_data['z']

        # Apply complementary filter
        self.filtered_gyro = self.alpha * self.filtered_gyro + (1 - self.alpha) * gyro_z

        # Integrate to get angle
        self.current_angle += self.filtered_gyro * dt
        self.current_angle = self.normalise_angle(self.current_angle)

        return self.filtered_gyro

    # ==== STAGE 1: HEALTH CHECK AND INITIALISATION ====
    
    def calibrate_gyroscope(self, samples=100):
        """Calibrate gyroscope by calculating bias"""
        self.logger('INFO', f'Calibrating gyroscope with {samples} samples...')
        self.logger('INFO', 'Please keep the CubeSat stationary during calibration...')

        gyro_sum = 0.0
        valid_samples = 0

        for i in range(samples):
            gyro_data = self.read_gyro_data()
            if gyro_data is not None:
                gyro_sum += gyro_data['z']
                valid_samples += 1
                if (i + 1) % 20 == 0:  # Log progress every 20 samples
                    self.logger('DEBUG', f'Calibration progress: {i+1}/{samples}')
            time.sleep(0.01)

        if valid_samples > samples * 0.8:
            self.gyro_bias = gyro_sum / valid_samples
            self.logger('INFO', f'Gyroscope calibration complete. Bias: {self.gyro_bias:.3f} deg/s')
            return True
        else:
            self.logger('ERROR', f'Gyroscope calibration failed. Only {valid_samples}/{samples} valid samples')
            return False

    def motor_health_check(self):
        """Test motor functionality"""
        self.logger('INFO', 'Testing motor functionality...')
        try:
            # Test forward direction
            GPIO.output(self.IN1, GPIO.HIGH)
            GPIO.output(self.IN2, GPIO.LOW)
            self.pwm.ChangeDutyCycle(30)
            time.sleep(0.5)

            # Test reverse direction
            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.HIGH)
            time.sleep(0.5)

            # Stop motor
            self.stop_motor()
            self.logger('INFO', 'Motor health check passed')
            return True
        except Exception as e:
            self.logger('ERROR', f'Motor health check failed: {e}')
            return False

    def system_health_check(self):
        """Comprehensive system health check"""
        self.logger('INFO', '=== AOCS Health Check Started ===')

        if not self.initialise_mpu9250():
            self.status = -1
            return self.status

        # Check gyroscope readings
        gyro_test_count = 0
        for _ in range(10):
            gyro_data = self.read_gyro_data()
            if gyro_data is not None:
                gyro_test_count += 1
            time.sleep(0.1)

        if gyro_test_count < 8:
            self.logger('ERROR', 'Gyroscope readings unstable')
            self.status = -1
            return self.status

        if not self.motor_health_check():
            self.status = -1
            return self.status

        if not self.calibrate_gyroscope():
            self.status = -1
            return self.status

        self.logger('INFO', '=== All Health Checks Passed ===')
        self.status = 0
        return self.status

    def initialise_reference_position(self):
        """Initialise the current position as reference (0 degrees)"""
        self.logger('INFO', 'Initialising reference position...')

        angle_readings = []
        for _ in range(50):
            gyro_data = self.read_gyro_data()
            if gyro_data is not None:
                corrected_gyro = gyro_data['z']
                angle_readings.append(corrected_gyro)
            time.sleep(0.02)

        if len(angle_readings) > 40:
            gyro_std = np.std(angle_readings)
            if gyro_std < 2.0:
                self.current_angle = 0.0
                self.logger('INFO', f'Reference position initialised. Gyro stability: ±{gyro_std:.2f} deg/s')
                self.status = 1
                return self.status
            else:
                self.logger('ERROR', f'System not stable enough for initialisation. Gyro std: {gyro_std:.2f} deg/s')
                self.status = -1
                return self.status
        else:
            self.logger('ERROR', 'Insufficient readings for initialisation')
            self.status = -1
            return self.status

    # ==== STAGE 2: POSITIONING CONTROL ====

    def rotate_360_degrees(self, angular_velocity=30):
        """Rotate 360 degrees at specified angular velocity"""
        self.logger('INFO', f'Starting 360° rotation at {angular_velocity} deg/s')

        start_angle = self.current_angle
        target_total_rotation = 360.0
        total_rotation = 0.0

        direction = 1 if angular_velocity > 0 else -1
        target_gyro = abs(angular_velocity)

        dt = 0.02
        self.is_moving = True

        try:
            while total_rotation < target_total_rotation and self.is_moving:
                start_time = time.time()

                current_gyro = self.update_current_angle(dt)

                angle_change = abs(self.current_angle - start_angle)
                if angle_change > 180:
                    angle_change = 360 - angle_change
                total_rotation = angle_change

                gyro_error = target_gyro - abs(current_gyro)
                speed_adjustment = gyro_error * 2.0
                base_speed = 40
                motor_speed = max(25, min(80, base_speed + speed_adjustment))

                self.set_motor_direction(direction)
                self.set_motor_speed(motor_speed)

                if int(total_rotation) % 90 == 0 and int(total_rotation) != 0:  # Log progress every 90 degrees
                    self.logger('INFO', f'Rotation: {total_rotation:.1f}°/{target_total_rotation}°, '
                                      f'Gyro: {current_gyro:.1f} deg/s, Speed: {motor_speed:.0f}%')

                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            self.logger('ERROR', f'360° rotation interrupted: {e}')
        finally:
            self.stop_motor()
            self.is_moving = False
            self.logger('INFO', f'360° rotation completed. Total rotation: {total_rotation:.1f}°')

    def move_to_angle(self, target_angle, max_speed=50):
        """Move to specific angle using PID control"""
        self.target_angle = self.normalise_angle(target_angle)
        self.logger('INFO', f'Moving to angle: {self.target_angle:.1f}°')

        dt = 0.02
        self.is_moving = True
        self.error_sum = 0
        self.last_error = 0

        tolerance = self.constants["CONTROL"]["position_tolerance"]
        settled_count = 0
        required_settled_count = 10

        try:
            while self.is_moving:
                start_time = time.time()

                self.update_current_angle(dt)

                error = self.target_angle - self.current_angle
                error = self.normalise_angle(error)

                if abs(error) < tolerance:
                    settled_count += 1
                    if settled_count >= required_settled_count:
                        self.logger('INFO', f'Target reached! Current angle: {self.current_angle:.1f}°')
                        break
                else:
                    settled_count = 0

                # PID control
                self.error_sum += error * dt
                self.error_sum = max(-50, min(50, self.error_sum))

                error_rate = (error - self.last_error) / dt if dt > 0 else 0
                self.last_error = error

                control_output = (self.Kp * error + self.Ki * self.error_sum + self.Kd * error_rate)

                deadzone = self.constants["CONTROL"]["detumbling_deadzone"]
                if abs(control_output) < deadzone:
                    self.stop_motor()
                else:
                    direction = 1 if control_output > 0 else -1
                    speed = min(abs(control_output), max_speed)

                    self.set_motor_direction(direction)
                    self.set_motor_speed(speed)

                # Log progress periodically
                if settled_count % 5 == 0 or abs(error) > 10:
                    self.logger('DEBUG', f'Current: {self.current_angle:.1f}°, Target: {self.target_angle:.1f}°, '
                                       f'Error: {error:.1f}°, Control: {control_output:.1f}')

                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            self.logger('ERROR', f'Movement interrupted: {e}')
        finally:
            self.stop_motor()
            self.is_moving = False

    # ==== STAGE 3: ARUCO TRACKING AND DOCKING ====

    def start_vision_communication(self):
        """Start communication thread with vision system"""
        self.comm_thread = threading.Thread(target=self.communication_handler, daemon=True)
        self.comm_thread.start()

    def communication_handler(self):
        """Handle communication with vision system"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', self.communication_port))
            server_socket.listen(1)

            self.logger('INFO', f'Listening for vision system on port {self.communication_port}')

            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    self.logger('INFO', f'Vision system connected from {addr}')

                    while True:
                        data = client_socket.recv(13)  # 4 + 4 + 1 bytes
                        if not data:
                            break

                        angle_error, distance, detected_byte = struct.unpack('ffB', data)
                        detected = bool(detected_byte)

                        self.vision_data = {
                            "angle_error": angle_error,
                            "distance": distance,
                            "detected": detected
                        }
                        self.last_vision_update = time.time()

                        ack = struct.pack('B', 1)
                        client_socket.send(ack)

                except Exception as e:
                    self.logger('WARNING', f'Communication error: {e}')
                    time.sleep(1)

        except Exception as e:
            self.logger('ERROR', f'Communication handler error: {e}')

    def move_to_angle_vision_assisted(self, target_angle, max_speed=40):
        """Move to specific angle with vision assistance"""
        self.target_angle = self.normalise_angle(target_angle)
        self.logger('INFO', f'Moving to angle: {self.target_angle:.1f}° with vision assistance')

        dt = 0.02
        self.is_moving = True
        self.error_sum = 0
        self.last_error = 0

        tolerance = self.constants["CONTROL"]["docking_tolerance"]
        settled_count = 0
        required_settled_count = 25

        try:
            while self.is_moving:
                start_time = time.time()

                self.update_current_angle(dt)

                gyro_error = self.target_angle - self.current_angle
                gyro_error = self.normalise_angle(gyro_error)

                final_error = gyro_error
                if (self.vision_data["detected"] and
                    time.time() - self.last_vision_update < 0.5):
                    vision_error = self.vision_data["angle_error"]
                    vision_weight = min(1.0, abs(gyro_error) / 10.0)
                    final_error = vision_weight * vision_error + (1 - vision_weight) * gyro_error

                if abs(final_error) < tolerance:
                    settled_count += 1
                    if settled_count >= required_settled_count:
                        self.logger('INFO', f'Target reached! Current angle: {self.current_angle:.1f}°')
                        break
                else:
                    settled_count = 0

                # PID control with conservative parameters
                self.error_sum += final_error * dt
                self.error_sum = max(-30, min(30, self.error_sum))

                error_rate = (final_error - self.last_error) / dt if dt > 0 else 0
                self.last_error = final_error

                control_output = (self.Kp * final_error +
                                self.Ki * self.error_sum +
                                self.Kd * error_rate)

                if abs(control_output) < 3:
                    self.stop_motor()
                else:
                    direction = 1 if control_output > 0 else -1
                    speed = min(abs(control_output), max_speed)

                    if abs(final_error) < 5:
                        speed = max(speed * 0.5, 15)

                    self.set_motor_direction(direction)
                    self.set_motor_speed(speed)

                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            self.logger('ERROR', f'Movement interrupted: {e}')
        finally:
            self.stop_motor()
            self.is_moving = False

    def real_time_docking(self, max_corrections=50):
        """Real-time docking with continuous vision feedback"""
        self.logger('INFO', 'Starting real-time docking procedure...')
        self.is_docking = True
        correction_count = 0

        try:
            while self.is_docking and correction_count < max_corrections:
                start_time = time.time()

                if not self.vision_data["detected"]:
                    self.logger('DEBUG', 'Waiting for ArUco detection...')
                    time.sleep(0.1)
                    continue

                if time.time() - self.last_vision_update > 2.0:
                    self.logger('WARNING', 'Vision data too old, waiting for update...')
                    time.sleep(0.1)
                    continue

                angle_error = self.vision_data["angle_error"]
                distance = self.vision_data["distance"]

                self.logger('INFO', f'Docking correction {correction_count + 1}: '
                                  f'Angle error: {angle_error:.2f}°, Distance: {distance:.2f}')

                tolerance = self.constants["CONTROL"]["docking_tolerance"]
                if abs(angle_error) < tolerance and distance < 5.0:
                    self.logger('INFO', 'Docking successful! Target aligned.')
                    break

                if abs(angle_error) > tolerance:
                    correction_angle = angle_error * 0.8

                    self.logger('DEBUG', f'Making correction: {correction_angle:.2f}°')

                    self.move_to_angle_vision_assisted(
                        self.current_angle + correction_angle,
                        self.constants["CONTROL"]["docking_max_speed"]
                    )

                    correction_count += 1
                    time.sleep(0.5)
                else:
                    self.logger('DEBUG', 'Angle aligned, monitoring distance...')
                    time.sleep(0.2)

                elapsed = time.time() - start_time
                sleep_time = max(0, 1.0 - elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            self.logger('ERROR', f'Docking interrupted: {e}')
        finally:
            self.stop_motor()
            self.is_docking = False

            if correction_count >= max_corrections:
                self.logger('ERROR', f'Docking failed: Maximum corrections ({max_corrections}) reached')
                return False
            else:
                self.logger('INFO', 'Docking procedure completed')
                return True

    # ==== DETUMBLING CONTROL ====

    def detumbling_control(self, stop_condition=None):
        """
        Implements detumbling control to bring angular velocity to zero
        stop_condition: callable that returns True when detumbling should stop
        """
        self.logger('INFO', 'Starting detumbling control mode...')

        dt = 0.01
        error_sum = 0
        last_error = 0
        filtered_gyro_z = 0
        loop_count = 0

        try:
            while True:
                start_time = time.time()

                # Check stop condition if provided
                if stop_condition and stop_condition():
                    break

                gyro_data = self.read_gyro_data()
                current_gyro_z = gyro_data['z']

                # Apply complementary filter
                filtered_gyro_z = self.alpha * filtered_gyro_z + (1 - self.alpha) * current_gyro_z

                # Calculate error (desired angular velocity is zero)
                error = 0 - filtered_gyro_z

                # Update integral term with anti-windup
                error_sum += error * dt
                error_sum = max(-50, min(50, error_sum))

                # Calculate derivative term
                error_rate = (error - last_error) / dt if dt > 0 else 0
                last_error = error

                # PID control output
                control_output = self.Kp * error + self.Ki * error_sum + self.Kd * error_rate

                # Determine motor direction and speed
                deadzone = self.constants["CONTROL"]["detumbling_deadzone"]
                if abs(control_output) < deadzone:
                    self.stop_motor()
                    speed = 0
                else:
                    direction = 1 if control_output > 0 else -1
                    speed = min(abs(control_output), 100)
                    self.set_motor_direction(direction)
                    self.set_motor_speed(speed)

                # Log progress every 50 loops to avoid spam
                if loop_count % 50 == 0:
                    self.logger('DEBUG', f'Angular Velocity: {filtered_gyro_z:.2f} deg/s, '
                                       f'Control Output: {control_output:.2f}, PWM: {speed:.1f}%')

                loop_count += 1
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            self.logger('ERROR', f'Detumbling control error: {e}')
        finally:
            self.stop_motor()
            self.logger('INFO', 'Detumbling control stopped')

    # ==== UTILITY FUNCTIONS ====

    def save_initialisation_data(self, filename="aocs_init_data.json"):
        """Save initialisation data to file"""
        init_data = {
            "timestamp": time.time(),
            "initial_angle": self.current_angle,
            "gyro_bias": self.gyro_bias,
            "status": self.status
        }

        try:
            with open(filename, 'w') as f:
                json.dump(init_data, f, indent=2)
            self.logger('INFO', f'Initialisation data saved to {filename}')
            return True
        except Exception as e:
            self.logger('ERROR', f'Failed to save initialisation data: {e}')
            return False

    def load_initialisation_data(self, filename="aocs_init_data.json"):
        """Load initialisation data from file"""
        try:
            with open(filename, 'r') as f:
                init_data = json.load(f)
                self.gyro_bias = init_data.get("gyro_bias", 0.0)
                self.logger('INFO', f'Loaded gyro bias: {self.gyro_bias:.3f} deg/s')
                return True
        except Exception as e:
            self.logger('WARNING', f'Could not load initialisation data: {e}')
            self.gyro_bias = 0.0
            return False

    def get_current_status(self):
        """Get comprehensive status information"""
        return {
            "current_angle": self.current_angle,
            "target_angle": self.target_angle,
            "is_moving": self.is_moving,
            "is_docking": self.is_docking,
            "gyro_reading": self.filtered_gyro,
            "vision_data": self.vision_data,
            "vision_age": time.time() - self.last_vision_update if self.last_vision_update > 0 else float('inf'),
            "status": self.status
        }

    def emergency_stop(self):
        """Emergency stop function"""
        self.is_moving = False
        self.is_docking = False
        self.stop_motor()
        self.logger('WARNING', 'Emergency stop activated')

    def cleanup(self):
        """Clean up resources"""
        self.emergency_stop()
        if hasattr(self, 'pwm'):
            self.pwm.stop()
        GPIO.cleanup()
        self.logger('INFO', 'Cleanup completed')


# Example usage with custom logger
def example_logger(level, message):
    """Example logger function"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {level}: {message}')


if __name__ == "__main__":
    # Load constants from file or use defaults
    try:
        with open("constants.json", 'r') as f:
            constants = json.load(f)
        print("Loaded constants from constants.json")
    except Exception:
        print("Using default constants")
        constants = None

    # Create AOCS controller with logger
    aocs = AOCSController(constants, logger=example_logger)

    try:
        print("=== Unified AOCS Control System ===")
        print("Commands:")
        print("1. 'health' - Run health check and initialisation")
        print("2. '360 [speed]' - Rotate 360 degrees")
        print("3. 'move [angle] [speed]' - Move to specific angle")
        print("4. 'vision_move [angle]' - Move with vision assistance")
        print("5. 'dock [max_corrections]' - Start docking procedure")
        print("6. 'detumble' - Start detumbling control")
        print("7. 'start_vision' - Start vision communication")
        print("8. 'status' - Show current status")
        print("9. 'stop' - Emergency stop")
        print("10. 'quit' - Exit programme")
        print()

        while True:
            try:
                user_input = input("Enter command: ").strip().lower()

                if user_input == 'quit':
                    break
                elif user_input == 'health':
                    status = aocs.system_health_check()
                    if status == 0:
                        status = aocs.initialise_reference_position()
                        if status == 1:
                            aocs.save_initialisation_data()
                            print("Health check and initialisation completed successfully")
                        else:
                            print("Initialisation failed")
                    else:
                        print("Health check failed")
                elif user_input == 'status':
                    status = aocs.get_current_status()
                    for key, value in status.items():
                        print(f"{key}: {value}")
                elif user_input == 'stop':
                    aocs.emergency_stop()
                elif user_input == 'detumble':
                    aocs.detumbling_control()
                elif user_input == 'start_vision':
                    aocs.start_vision_communication()
                    print("Vision communication started")
                elif user_input.startswith('360'):
                    parts = user_input.split()
                    speed = float(parts[1]) if len(parts) > 1 else 30
                    aocs.rotate_360_degrees(speed)
                elif user_input.startswith('move'):
                    parts = user_input.split()
                    if len(parts) >= 2:
                        angle = float(parts[1])
                        speed = float(parts[2]) if len(parts) > 2 else 50
                        aocs.move_to_angle(angle, speed)
                    else:
                        print("Usage: move [angle] [optional_speed]")
                elif user_input.startswith('vision_move'):
                    parts = user_input.split()
                    if len(parts) >= 2:
                        angle = float(parts[1])
                        aocs.move_to_angle_vision_assisted(angle)
                    else:
                        print("Usage: vision_move [angle]")
                elif user_input.startswith('dock'):
                    parts = user_input.split()
                    max_corrections = int(parts[1]) if len(parts) > 1 else 50
                    success = aocs.real_time_docking(max_corrections)
                    print(f"Docking {'successful' if success else 'failed'}")
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
