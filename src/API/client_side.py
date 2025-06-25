import socket
import json
import os

# Load hostname and port from env_values.json
env_path = os.path.join(os.path.dirname(__file__), 'env_values.json')
with open(env_path, 'r') as f:
    env = json.load(f)
receive_host = env['GROUND_HOST']
receive_port = env['RECEIVE_PORT']

print(f"Connecting to server at {receive_host}:{receive_port}")
hostname = receive_host
receive_port = receive_port

# Create a socket and connect to the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((hostname, receive_port))
    message = "Hello from client!"
    s.sendall(message.encode())
    data = s.recv(1024)
    print('Received from server:', data.decode())
