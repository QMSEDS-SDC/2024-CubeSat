"""
Runs the Comms
"""

from comms import Server_Comms

server = Server_Comms()
server.start_listening(size_client_queue=5)
