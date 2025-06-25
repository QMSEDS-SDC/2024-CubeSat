import socket
import json
import os


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


# Load ports from env_values.json
env_path = os.path.join(os.path.dirname(__file__), 'env_values.json')
with open(env_path, 'r') as f:
    env = json.load(f)
send_port = env['SEND_PORT']

local_ip = get_local_ip()
print(f"Server will bind to IP: {local_ip}, Port: {send_port}")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((local_ip, send_port))
server_socket.listen(5)
print("Server listening...")

while True:
    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")
    client_socket.sendall(b"Hello from server!\n")
    client_socket.close()
