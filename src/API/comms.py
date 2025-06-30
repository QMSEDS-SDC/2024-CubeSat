import socket
import json
import os
import threading
import logging
from datetime import datetime


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

        # format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # file handler for the console logs
        log_file = os.path.join(log_dir, f"server_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # file handler for the error logs
        error_file = os.path.join(log_dir, f"server_errors_{datetime.now().strftime('%Y%m%d')}.log")
        error_handler = logging.FileHandler(error_file)

        # adds them to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)

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
                sensors = json_message.get("message", [])
                self.logger.info(f"Status request from {client_id} for sensors: {sensors}")

                response = []
                # TODO: Replace with actual sensor reading functions
                for sensor in sensors:
                    # Placeholder: here put code to fetch the sensor info and forward it back
                    sensor_data = {
                        "sensor_id": sensor,
                        "value": 0,  # Replace with actual reading
                        "status": "ok",
                        "timestamp": datetime.now().isoformat()
                    }
                    response.append(sensor_data)

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

                # TODO: Replace with actual initialization code
                # first initiate code then do this, else return 0
                init_success = True  # Replace with actual initialization logic

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
