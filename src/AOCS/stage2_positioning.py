import time
import smbus
import RPi.GPIO as GPIO
import numpy as np
import json
import threading
from queue import Queue

# Pin Configuration (same as previous scripts)
IN1 = 17     # GPIO17 (Pin 11) - Motor direction pin 1
IN2 = 27     # GPIO27 (Pin 13) - Motor direction pin 2
ENA = 18     # GPIO18 (Pin 12) - PWM pin for controlling motor speed (EnA)

# MPU9250 I2C Configuration
MPU9250_ADDR = 0x68
I2C_BUS = 1

# MPU9250 Register Addresses
GYRO_XOUT_H = 0x43
GYRO_XOUT_L = 0x44
GYRO_YOUT_H = 0x45
GYRO_YOUT_L = 0x46
GYRO_ZOUT_H = 0x47
GYRO_ZOUT_L = 0x48
PWR_MGMT_1 = 0x6B
GYRO_CONFIG = 0x1B

class AOCSPositioning:
    def __init__(self):
        self.current_angle = 0.0
        self.target_angle = 0.0
        self.gyro_bias = 0.0
        self.is_moving = False
        self.command_queue = Queue()
        
        # Control parameters
        self.Kp = 1.2
        self.Ki = 0.05
        self.Kd = 0.15
        
        # PID variables
        self.error_sum = 0
        self.last_error = 0
        
        # Filter parameters
        self.alpha = 0.8
        self.filtered_gyro = 0.0
        
        # Initialize hardware
        self.setup_gpio()
        self.setup_i2c()
        self.initialize_mpu9250()
        self.load_initialization_data()
        
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
    
    def rotate_360_degrees(self, angular_velocity=30):
        """
        Rotate 360 degrees at specified angular velocity
        angular_velocity: desired rotation speed in deg/s
        """
        print(f"Starting 360° rotation at {angular_velocity} deg/s")
        
        start_angle = self.current_angle
        target_total_rotation = 360.0
        total_rotation = 0.0
        
        # Determine direction (positive angular velocity = forward)
        direction = 1 if angular_velocity > 0 else -1
        target_gyro = abs(angular_velocity)
        
        dt = 0.02  # 50Hz control loop
        self.is_moving = True
        
        try:
            while total_rotation < target_total_rotation and self.is_moving:
                start_time = time.time()
                
                # Update angle
                current_gyro = self.update_current_angle(dt)
                
                # Calculate total rotation (always positive)
                angle_change = abs(self.current_angle - start_angle)
                if angle_change > 180:
                    angle_change = 360 - angle_change
                total_rotation = angle_change
                
                # Speed control using gyroscope feedback
                gyro_error = target_gyro - abs(current_gyro)
                
                # Simple proportional control for speed
                speed_adjustment = gyro_error * 2.0
                base_speed = 40  # Base PWM speed
                motor_speed = max(25, min(80, base_speed + speed_adjustment))
                
                self.set_motor_direction(direction)
                self.set_motor_speed(motor_speed)
                
                print(f"Rotation: {total_rotation:.1f}°/{target_total_rotation}°, "
                      f"Gyro: {current_gyro:.1f} deg/s, Speed: {motor_speed:.0f}%")
                
                # Maintain loop timing
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("360° rotation interrupted")
        finally:
            self.stop_motor()
            self.is_moving = False
            print(f"360° rotation completed. Total rotation: {total_rotation:.1f}°")
    
    def move_to_angle(self, target_angle, max_speed=50):
        """
        Move to specific angle using PID control
        target_angle: target angle in degrees
        max_speed: maximum motor speed (0-100%)
        """
        self.target_angle = self.normalize_angle(target_angle)
        print(f"Moving to angle: {self.target_angle:.1f}°")
        
        dt = 0.02  # 50Hz control loop
        self.is_moving = True
        self.error_sum = 0
        self.last_error = 0
        
        tolerance = 2.0  # Position tolerance in degrees
        settled_count = 0
        required_settled_count = 10  # Must be settled for this many iterations
        
        try:
            while self.is_moving:
                start_time = time.time()
                
                # Update current angle
                self.update_current_angle(dt)
                
                # Calculate error
                error = self.target_angle - self.current_angle
                error = self.normalize_angle(error)  # Handle wrap-around
                
                # Check if we're within tolerance
                if abs(error) < tolerance:
                    settled_count += 1
                    if settled_count >= required_settled_count:
                        print(f"Target reached! Current angle: {self.current_angle:.1f}°")
                        break
                else:
                    settled_count = 0
                
                # PID control
                self.error_sum += error * dt
                self.error_sum = max(-50, min(50, self.error_sum))  # Anti-windup
                
                error_rate = (error - self.last_error) / dt if dt > 0 else 0
                self.last_error = error
                
                control_output = (self.Kp * error + 
                                self.Ki * self.error_sum + 
                                self.Kd * error_rate)
                
                # Convert to motor commands
                if abs(control_output) < 5:
                    # Dead zone
                    self.stop_motor()
                else:
                    direction = 1 if control_output > 0 else -1
                    speed = min(abs(control_output), max_speed)
                    
                    self.set_motor_direction(direction)
                    self.set_motor_speed(speed)
                
                print(f"Current: {self.current_angle:.1f}°, Target: {self.target_angle:.1f}°, "
                      f"Error: {error:.1f}°, Control: {control_output:.1f}")
                
                # Maintain loop timing
                elapsed = time.time() - start_time
                sleep_time = max(0, dt - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("Movement interrupted")
        finally:
            self.stop_motor()
            self.is_moving = False
    
    def process_command(self, command):
        """
        Process movement command
        command format: {"type": "rotate_360", "speed": 30} or 
                       {"type": "move_to_angle", "angle": 45, "speed": 50}
        """
        try:
            if command["type"] == "rotate_360":
                speed = command.get("speed", 30)
                self.rotate_360_degrees(speed)
                return {"status": "completed", "final_angle": self.current_angle}
                
            elif command["type"] == "move_to_angle":
                angle = command["angle"]
                speed = command.get("speed", 50)
                self.move_to_angle(angle, speed)
                return {"status": "completed", "final_angle": self.current_angle}
                
            else:
                return {"status": "error", "message": "Unknown command type"}
                
        except Exception as e:
            self.stop_motor()
            return {"status": "error", "message": str(e)}
    
    def get_current_position(self):
        """Get current position information"""
        return {
            "current_angle": self.current_angle,
            "target_angle": self.target_angle,
            "is_moving": self.is_moving,
            "gyro_reading": self.filtered_gyro
        }
    
    def emergency_stop(self):
        """Emergency stop function"""
        self.is_moving = False
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
    aocs = AOCSPositioning()
    
    try:
        print("=== AOCS Stage 2: Positioning Control ===")
        print("Commands:")
        print("1. '360 [speed]' - Rotate 360 degrees at specified speed")
        print("2. 'move [angle] [speed]' - Move to specific angle")
        print("3. 'status' - Show current position")
        print("4. 'stop' - Emergency stop")
        print("5. 'quit' - Exit program")
        print()
        
        while True:
            try:
                user_input = input("Enter command: ").strip().lower()
                
                if user_input == 'quit':
                    break
                elif user_input == 'status':
                    pos = aocs.get_current_position()
                    print(f"Current angle: {pos['current_angle']:.1f}°")
                    print(f"Target angle: {pos['target_angle']:.1f}°")
                    print(f"Moving: {pos['is_moving']}")
                    print(f"Gyro: {pos['gyro_reading']:.1f} deg/s")
                elif user_input == 'stop':
                    aocs.emergency_stop()
                elif user_input.startswith('360'):
                    parts = user_input.split()
                    speed = float(parts[1]) if len(parts) > 1 else 30
                    command = {"type": "rotate_360", "speed": speed}
                    result = aocs.process_command(command)
                    print(f"Result: {result}")
                elif user_input.startswith('move'):
                    parts = user_input.split()
                    if len(parts) >= 2:
                        angle = float(parts[1])
                        speed = float(parts[2]) if len(parts) > 2 else 50
                        command = {"type": "move_to_angle", "angle": angle, "speed": speed}
                        result = aocs.process_command(command)
                        print(f"Result: {result}")
                    else:
                        print("Usage: move [angle] [optional_speed]")
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
