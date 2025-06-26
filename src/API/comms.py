import socket
import json
import os
import threading


class Server_Comms:
    """
    To send data Ground
    """

    def __init__(self):
        """
        Inits and open the server socket for listening
        """
        env_path = os.path.join(os.path.dirname(__file__), "env_values.json")
        with open(env_path, "r") as f:
            self.env = json.load(f)

        send_port = self.env["SEND_PORT"]
        local_ip = "127.0.0.1"

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # uses TCP, for IPv4 protocol
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((local_ip, send_port))
        self.running = True  # for the persistent loop

    def handle_client_connection(self, client_socket, addr):
        """
        Manages client connection for a single client persistently (supports JSON)
        """
        try:
            # Persistency
            while self.running:
                try:
                    # Should receive JSON - request from client
                    data = client_socket.recv(1024).decode("utf-8")

                    if not data:  # for disconnects
                        break

                    # parse message and send response
                    try:
                        json_message = json.loads(data)
                        response = self.process_json_message(json_message, addr)
                        self._send_json(client_socket, response)

                        # should terminate if sent a disconnect command (will need to implement)
                        if json_message.get("type") == "disconnect":
                            break

                    except json.JSONDecodeError:  # if not JSON
                        error_response = {
                            "type": "error",
                            "message": "Not JSON",
                            "received_data": data
                        }
                        self._send_json(client_socket, error_response)

                except socket.timeout:  # continue as long as should
                    continue
                except ConnectionResetError:  # break if connection reset error is triggered
                    break

        except Exception:  # if something else, close socket
            pass
        finally:
            client_socket.close()

    def process_json_message(self, json_message, client_addr):
        """
        Process JSON Message from Ground and provide appropriate info
        """
        
        message_type = json_message.get("type", "NA")

        if message_type == "status":
            sensors = json_message.get("message", [])

            for sensor in sensors:
                response = []  # here put code to fetch the sensor info and forword it back to them

            return {
                "type": "status",
                "message": response
            }

        elif message_type == "init":
            phase = json_message.get("message", -1)
            if phase == -1:
                if phase == -1:
                    return {
                        "type": "Error",
                        "message": -1
                    }
            # first initiate code then do this, else return 0
            return {
                    "type": "response",
                    "message": 1
                }

        elif message_type == "p2_info":
            request = json_message.get("message", "")
            if request != "get":
                return {
                    "type": "Error",
                    "message": -1
                }
            
            # do this using the function but for now
            response = {
                0: 0,
                1: 0,
                2: 0,
                3: 0,
                4: 0,
                5: 0,
                6: 0,
                7: 0,
                8: 0,
                9: 0,
            }

            return {
                "type": "p2_info",
                "message": response
            }

        elif message_type == "p2_cmd":
            targets = json_message.get("message", [])
            response = {}

            # it should continuously update through its respective functions
            for target in targets:
                response[target] = 1
            return {
                "type": "p2_cmd",
                "message": response
            }

        elif message_type == "p3_info":
            request = json_message.get("message", "")
            if request != "get":
                return {
                    "type": "Error",
                    "message": -1
                }

            # again it should be through a function
            response = {
                "init": [],
                "final": []
            }

            return {
                "type": "p3_info",
                "message": response
            }

        elif message_type == "img":
            request = json_message.get("message", "")
            if request != "get":
                return {
                    "type": "Error",
                    "message": -1
                }

            # should use the functions
            img = []

            return {
                "type": "img",
                "message": img
            }

        elif message_type == "shutdown":
            seconds = json_message.get("message", -1)
            if seconds == -1:
                return {
                    "type": "Error",
                    "message": -1
                }

            return {
                "type": "response",
                "message": 1
            }
            
        elif message_type == "optional":  # will take care about it later
            feature = json_message.get("message", "")

            if feature == "live":
                pass
            elif feature == "manual":
                pass
            else:
                return {
                    "type": "Error",
                    "message": -1
                }

            return {
                "type": "response",
                "message": 0
            }

        else:
            return {
                "type": "Error",
                "message": -1
            }

    def _send_json(self, client_socket, data):
        """
        Manages JSON sending
        """
        try:
            # Remove newline delimiter - send pure JSON
            json_string = json.dumps(data)
            client_socket.sendall(json_string.encode("utf-8"))
        except Exception:
            pass

    def start_listening(self, size_client_queue=5):
        """starts listening, and manages the clients appropriately using threading"""
        self.server_socket.listen(size_client_queue)

        try:
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()

                    # each client - different thread = concurrency achieved
                    client_thread = threading.Thread(
                        target=self.handle_client_connection,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.error:
                    break

        except Exception:
            pass
