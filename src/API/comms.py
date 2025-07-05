"""
Server comms

TODO: Integrate all the APIs (also use stuff in AOCS to make the API for it)
"""

import socket
import json
import os
import threading
import logging
from datetime import datetime
from RPiAPI.status import status


class Server_Comms:
    """
    To send data Ground
    """

    def __init__(self):
        """
        Inits and open the server socket for listening
        """
        # config logging - builtin_func
        self._setup_logging()

        env_path = os.path.join(os.path.dirname(__file__), "env_values.json")
        with open(env_path, "r") as f:
            self.env = json.load(f)

        send_port = self.env["MAIN_PORT"]
        local_ip = "0.0.0.0"  # as needs to accept from all interfaces
        self.status_monitor = status()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # uses TCP, for IPv4 protocol
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((local_ip, send_port))
        self.running = True  # for the persistent loop

        self.logger.info(f"Server init on {local_ip}:{send_port}")  # adds proof that it initialised

    def _setup_logging(self):
        """
        Configures the logging for the server side conn
        """
        # creates the file
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)  # if not exists then only change

        # creates logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # File handler for all logs
            log_file = os.path.join(log_dir, f"server_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)

            # Add handlers to logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def handle_client_connection(self, client_socket, addr):
        """
        Manages client connection for a single client persistently (supports JSON).
        """
        client_id = f"{addr[0]}:{addr[1]}"
        self.logger.info(f"New client connected: {client_id}")

        try:
            client_socket.settimeout(10)
            buffer = ""
            message_count = 0

            while self.running:
                try:
                    chunk = client_socket.recv(1024).decode("utf-8")
                    if not chunk:
                        self.logger.info(f"Client {client_id} disconnected")
                        break

                    self.logger.debug(f"Received data from {client_id}: {len(chunk)} bytes")
                    buffer += chunk

                    while "\n" in buffer:
                        msg, buffer = buffer.split("\n", 1)
                        if msg.strip():
                            message_count += 1
                            self.logger.debug(f"Processing message #{message_count} from {client_id}: {msg.strip()[:100]}...")

                            try:
                                json_message = json.loads(msg.strip())
                                self.logger.info(f"Received {json_message.get('type', 'unknown')} message from {client_id}")

                                response = self.process_json_message(json_message, addr)
                                self._send_json(client_socket, response)

                                self.logger.debug(f"Sent response to {client_id}: {response.get('type', 'unknown')}")

                                if json_message.get("type") == "disconnect":
                                    self.logger.info(f"Client {client_id} requested disconnect")
                                    return

                            except json.JSONDecodeError as e:
                                self.logger.warning(f"Invalid JSON from {client_id}: {e}")
                                error_response = {
                                    "type": "error",
                                    "message": "Not JSON",
                                    "received_data": msg
                                }
                                self._send_json(client_socket, error_response)

                except socket.timeout:
                    self.logger.debug(f"Timeout waiting for data from {client_id}")
                    continue
                except ConnectionResetError:
                    self.logger.warning(f"Connection reset by {client_id}")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error handling {client_id}: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Error in client handler for {client_id}: {e}")
        finally:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
                self.logger.info(f"Closed connection to {client_id}")
            except Exception as e:
                self.logger.error(f"Error closing connection to {client_id}: {e}")

    def process_json_message(self, json_message, client_addr):
        """
        Process JSON Message from Ground and provide appropriate info
        """
        client_id = f"{client_addr[0]}:{client_addr[1]}"
        message_type = json_message.get("type", "NA")

        self.logger.debug(f"Processing \"{message_type}\" message from {client_id}")

        try:
            if message_type == "status":
                if message_type == "status":
                    sensors = json_message.get("message", [])
                    self.logger.info(f"Status request from {client_id} for sensors: {sensors}")

                    response = self._get_system_status(sensors)

                    self.logger.debug(f"Returning status data for {len(response)} sensors to {client_id}")
                    return {
                        "type": "status",
                        "message": response
                    }

            elif message_type == "init":
                phase = json_message.get("message", -1)
                self.logger.info(f"Init request from {client_id} for phase {phase}")
    
                if phase == -1:
                    self.logger.warning(f"Invalid phase in init request from {client_id}")
                    return {
                        "type": "Error",
                        "message": "Invalid phase number"
                    }
    
                # Use FSM to initiate phase
                if hasattr(self, 'fsm'):
                    try:
                        if phase == 1:
                            # Start phase 1 in a separate thread
                            phase_thread = threading.Thread(target=self.fsm.phase1, daemon=True)
                            phase_thread.start()
                            init_success = True
                        elif phase == 2:
                            phase_thread = threading.Thread(target=self.fsm.phase2, daemon=True)
                            phase_thread.start()
                            init_success = True
                        elif phase == 3:
                            phase_thread = threading.Thread(target=self.fsm.phase3, daemon=True)
                            phase_thread.start()
                            init_success = True
                        else:
                            init_success = False
                    except Exception as e:
                        self.logger.error(f"Error initiating phase {phase}: {e}")
                        init_success = False
                else:
                    init_success = False
    
                if init_success:
                    self.logger.info(f"Successfully initialized phase {phase} for {client_id}")
                    return {
                        "type": "response",
                        "message": 1
                    }
                else:
                    self.logger.error(f"Failed to initialize phase {phase} for {client_id}")
                    return {
                        "type": "Error",
                        "message": "Initialization failed"
                    }
    
            elif message_type == "telemetry":
                # New message type for getting telemetry data
                if hasattr(self, 'fsm'):
                    telemetry_data = self.fsm.get_telemetry_data()
                    return {
                        "type": "telemetry",
                        "message": telemetry_data
                    }
                else:
                    return {
                        "type": "Error",
                        "message": "FSM not available"
                    }

            elif message_type == "p2_info":
                request = json_message.get("message", "")
                self.logger.info(f"P2 info request from {client_id}: {request}")

                if request != "get":
                    self.logger.warning(f"Invalid P2 info request from {client_id}: {request}")
                    return {
                        "type": "Error",
                        "message": "Invalid request format"
                    }

                # TODO: Replace with actual function call
                response = {
                    0: 0, 1: 0, 2: 0, 3: 0, 4: 0,
                    5: 0, 6: 0, 7: 0, 8: 0, 9: 0,
                }

                self.logger.debug(f"Returning P2 info to {client_id}")
                return {
                    "type": "p2_info",
                    "message": response
                }

            elif message_type == "p2_cmd":
                targets = json_message.get("message", [])
                self.logger.info(f"P2 command from {client_id} for targets: {targets}")

                if not isinstance(targets, list):
                    self.logger.warning(f"Invalid P2 command format from {client_id}")
                    return {
                        "type": "Error",
                        "message": "Targets must be a list"
                    }

                response = {}
                # TODO: Replace with actual command execution
                for target in targets:
                    # it should continuously update through its respective functions
                    command_success = True  # Replace with actual command execution
                    response[target] = 1 if command_success else 0
                    self.logger.debug(f"P2 command for target {target}: {'success' if command_success else 'failed'}")

                self.logger.info(f"P2 command completed for {client_id}: {len(response)} targets processed")
                return {
                    "type": "p2_cmd",
                    "message": response
                }

            elif message_type == "p3_info":
                request = json_message.get("message", "")
                self.logger.info(f"P3 info request from {client_id}: {request}")

                if request != "get":
                    self.logger.warning(f"Invalid P3 info request from {client_id}: {request}")
                    return {
                        "type": "Error",
                        "message": "Invalid request format"
                    }

                # TODO: Replace with actual function call
                response = {
                    "init": [],  # Replace with actual initial data
                    "final": []  # Replace with actual final data
                }

                self.logger.debug(f"Returning P3 info to {client_id}")
                return {
                    "type": "p3_info",
                    "message": response
                }

            elif message_type == "img":
                request = json_message.get("message", "")
                self.logger.info(f"Image request from {client_id}: {request}")

                if request != "get":
                    self.logger.warning(f"Invalid image request from {client_id}: {request}")
                    return {
                        "type": "Error",
                        "message": "Invalid request format"
                    }

                # TODO: Replace with actual image capture/retrieval function
                img = []  # Replace with actual image data (base64 encoded or file path)

                self.logger.info(f"Returning image data to {client_id} (size: {len(img)})")
                return {
                    "type": "img",
                    "message": img
                }

            elif message_type == "shutdown":
                seconds = json_message.get("message", -1)
                self.logger.warning(f"Shutdown request from {client_id} with delay: {seconds} seconds")

                if seconds == -1 or not isinstance(seconds, (int, float)) or seconds < 0:
                    self.logger.error(f"Invalid shutdown delay from {client_id}: {seconds}")
                    return {
                        "type": "Error",
                        "message": "Invalid shutdown delay"
                    }

                # TODO: Implement actual shutdown logic
                # Schedule shutdown after specified seconds
                self.logger.critical(f"Shutdown scheduled in {seconds} seconds by {client_id}")

                return {
                    "type": "response",
                    "message": 1
                }

            elif message_type == "optional":
                feature = json_message.get("message", "")
                self.logger.info(f"Optional feature request from {client_id}: {feature}")

                if feature == "live":
                    self.logger.info(f"Live feature requested by {client_id}")
                    # TODO: Implement live data streaming
                    pass
                elif feature == "manual":
                    self.logger.info(f"Manual mode requested by {client_id}")
                    # TODO: Implement manual control mode
                    pass
                else:
                    self.logger.warning(f"Unknown optional feature from {client_id}: {feature}")
                    return {
                        "type": "Error",
                        "message": f"Unknown feature: {feature}"
                    }

                return {
                    "type": "response",
                    "message": 0
                }

            elif message_type == "disconnect":
                self.logger.info(f"Disconnect request from {client_id}")
                return {
                    "type": "response",
                    "message": "Disconnecting"
                }

            else:
                self.logger.warning(f"Unknown message type from {client_id}: {message_type}")
                return {
                    "type": "Error",
                    "message": f"Unknown message type: {message_type}"
                }

        except Exception as e:
            self.logger.error(f"Error processing message from {client_id}: {e}")
            return {
                "type": "Error",
                "message": f"Internal server error: {str(e)}"
            }

    def _get_system_status(self, requested_sensors=None):
        """
        Get comprehensive system status using RPiAPI
        """
        status_data = {}
        
        try:
            # Power Subsystem
            status_data["power"] = {
                "battery_voltage": self.status_monitor.GetVoltage(),
                "battery_current": self.status_monitor.GetCurrent(),
                "battery_power": self.status_monitor.GetPower(),
                "status": "NOMINAL" if self.status_monitor.GetVoltage() > 3.0 else "CRITICAL"
            }
            
            # Thermal Subsystem
            cpu_temp = self.status_monitor.pi_temp()
            status_data["thermal"] = {
                "cpu_temperature": cpu_temp,
                "status": "OK" if isinstance(cpu_temp, (int, float)) and cpu_temp < 70 else "WARNING"
            }
            
            # Communication Subsystem
            wifi_strength = self.status_monitor.pi_wifi_strength()
            wifi_freq = self.status_monitor.pi_wifi_freq()
            wifi_bitrate = self.status_monitor.pi_wifi_tx_bitrate()
            wifi_quality = self.status_monitor.pi_wifi_quality()
            
            status_data["communication"] = {
                "wifi_strength": wifi_strength,
                "wifi_frequency": wifi_freq,
                "wifi_bitrate": wifi_bitrate,
                "wifi_quality": wifi_quality,
                "status": "OK" if isinstance(wifi_quality, (int, float)) and wifi_quality > 50 else "WARNING"
            }
            
            # Command and Data Handling
            cpu_usage = self.status_monitor.pi_use()
            disk_usage = self.status_monitor.pi_disk()
            used_ram = self.status_monitor.pi_used_ram()
            free_ram = self.status_monitor.pi_free_ram()
            
            status_data["cdh"] = {
                "cpu_usage": cpu_usage,
                "disk_usage": disk_usage,
                "memory_used": used_ram,
                "memory_free": free_ram,
                "status": "OK" if isinstance(cpu_usage, (int, float)) and cpu_usage < 80 else "WARNING"
            }
            
            # Camera/Payload status
            status_data["payload"] = {
                "camera_available": True,  # Will be updated by FSM
                "status": "OK"
            }
            
            # ADCS - placeholder for now (to be integrated with AOCS)
            status_data["adcs"] = {
                "gyroscope": {"x": 0, "y": 0, "z": 0},
                "orientation": {"x": 0, "y": 0, "z": 0},
                "sun_sensor": False,
                "reaction_wheel_rpm": 0,
                "status": "NOT OK"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            status_data["error"] = str(e)
        
        return status_data

    def _send_json(self, client_socket, data):
        """
        Manages JSON sending
        """
        try:
            json_string = json.dumps(data) + "\n"
            client_socket.sendall(json_string.encode("utf-8"))
            self.logger.debug(f"Sent JSON response: {len(json_string)} bytes")
        except Exception as e:
            self.logger.error(f"Error sending JSON: {e}")

    def start_listening(self, size_client_queue=5):
        """starts listening, and manages the clients appropriately using threading"""
        self.server_socket.listen(size_client_queue)
        self.logger.info(f"Server listening with queue size {size_client_queue}")

        try:
            while self.running:
                try:
                    self.logger.debug("Waiting for client connections...")
                    client_socket, addr = self.server_socket.accept()

                    client_thread = threading.Thread(
                        target=self.handle_client_connection,
                        args=(client_socket, addr),
                        name=f"Client-{addr[0]}:{addr[1]}"
                    )
                    client_thread.daemon = True
                    client_thread.start()

                    self.logger.info(f"Started thread for client {addr[0]}:{addr[1]}")

                except socket.error as e:
                    self.logger.error(f"Socket error: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.logger.info("Server stopped listening")
