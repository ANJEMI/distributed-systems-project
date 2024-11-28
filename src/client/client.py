import socket
import json
from typing import Dict, List
import os

class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.tracker_socket = None
        self.torrents_downloading = {}
        self.pieces_downloaded: Dict[str,List[bool]]  = {}
        # Path is the actual path of this file concatenated with the download folder
        # and client_id
        self.download_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"downloads/client_{client_id}")
        print(self.download_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
    def connect_to_tracker(self, tracker_ip, tracker_port):
        """
        Connects to the tracker server.

        Args:
            tracker_ip (str): IP address of the tracker server.
            tracker_port (int): Port number of the tracker server.
        Returns:
            None
        """
        try:
            self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.tracker_socket.connect((tracker_ip, tracker_port))

            print(f"Connected to tracker at {tracker_ip}:{tracker_port}")
        
        except Exception as e:
            raise ConnectionError(f"Error connecting to tracker: {e}")

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
            response: The torrent data from the tracker server.
        
        Example response:
            {
              "torrent_id": "1",
              "name": "Torrent de prueba",
              "size": 1024,
              "pieces": ["a", "b", "c"],
              "seeders": 1,
              "leechers": 0,
              "peers": [
                {
                  "peer_id": "1",
                  "ip": "",
                  "port": 6881
                }
              ]
            }
        """
        
        if not self.tracker_socket:
            raise ConnectionError("The client is not connected to the tracker.")
        
        try:
            request = {
                "torrent_id": torrent_id
            }

            request = json.dumps(request)

            self.tracker_socket.send(request.encode())

            response = self.tracker_socket.recv(1024).decode()

            response = json.loads(response)

            self.torrents_downloading[torrent_id] = response
            # TODO - No tener que hacer length y modificar el tracker para que devuelva el numero de piezas
            self.pieces_downloaded[torrent_id] = [False] * len(set(response["pieces"]))

            return response
        
        except Exception as e:
            raise ConnectionError(f"Error requesting torrent data: {e}")
        
    def start_download(self, torrent_id):
        """
        Starts downloading the torrent data from the peers.

        Args:
            torrent_id (str): ID of the torrent to download.
        Returns:
            None
        """
        torrent_data = self.torrents_downloading.get(torrent_id)

        if not torrent_data:
            raise ValueError(f"The torrent with ID '{torrent_id}' was not found in the client.")
        
        pieces = torrent_data["pieces"]
        number_of_pieces = len(pieces)
        piece_length = torrent_data["piece_length"]
        peers = torrent_data["peers"]
        
        