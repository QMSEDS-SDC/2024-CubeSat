import socket
import json
import os

# Load configuration from env_values.json
config_path = os.path.join(os.path.dirname(__file__), '..', 'env_values.json')
with open(config_path, 'r') as f:
    config = json.load(f)

HOST = config['GROUND_HOST']
PORT = config['SEND_PORT']

print(f"Client connecting to {HOST}:{PORT}")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

while True:
    s.sendall(b'Hello, world')
    data = s.recv(1024)
    print('Received', repr(data))
s.close()