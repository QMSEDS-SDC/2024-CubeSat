import socket
import json
import os

# Load configuration from env_values.json
config_path = os.path.join(os.path.dirname(__file__), '..', 'env_values.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Auto-detect server's own IPv4 address


def get_local_ip():
    # Create a temporary socket to determine local IP
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a remote address (doesn't actually send data)
        temp_socket.connect(('8.8.8.8', 80))
        local_ip = temp_socket.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'  # fallback to localhost
    finally:
        temp_socket.close()
    return local_ip


HOST = get_local_ip()
PORT = config['SEND_PORT']

print(f"Server starting on {HOST}:{PORT}")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
conn, addr = s.accept()
print('Connected by', addr)
while True:
    data = conn.recv(1024)
    if not data:
        break
    conn.sendall(data)
conn.close()
