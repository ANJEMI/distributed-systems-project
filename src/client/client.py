import socket
import json

class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        
    def connect_to_tracker(self, tracker_ip, tracker_port):
        """
        Connects to the tracker server.

        Args:
            tracker_ip (str): IP address of the tracker server.
            tracker_port (int): Port number of the tracker server.
        Returns:
            None
        """
    
        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.tracker_socket.connect((tracker_ip, tracker_port))
        
        print(f"Connected to tracker at {tracker_ip}:{tracker_port}")

    def request_torrent_data(self, torrent_id):
        """
        Sends a request (JSON) to the tracker server for the torrent data.
        Receives the torrent data from the tracker server.
        
        Request format:
        {
            "torrent_id": "hash"
        }
        
        
        Args:
            torrent_id (str): ID of the torrent to request.
        Returns:
            None
        """

        request = {
            "torrent_id": torrent_id
        }
        
        request = json.dumps(request)
        
        self.tracker_socket.send(request.encode())
        
        response = self.tracker_socket.recv(1024).decode()
        
        print(response)

        
