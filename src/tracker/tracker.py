import json
import os
import socket
import struct
import threading

class Tracker:
    # TRACKER_DIRECTORY = "src/tracker/database"  make dinamic
    TRACKER_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
    TRACKER_FILE_NAME = "tracker_data.json"

    def create_initial_tracker(self):
        """
        Creates an initial empty tracker data structure and saves it as a JSON
        file in the specified directory.
        
        Returns:
            None
        """
        def create_empty_tracker_data():
            return {
                "torrents": []
            }

        empty_tracker_data = create_empty_tracker_data()
        empty_tracker_json = json.dumps(empty_tracker_data, indent=4)

        os.makedirs(self.TRACKER_DIRECTORY, exist_ok=True)
        file_path = os.path.join(self.TRACKER_DIRECTORY, self.TRACKER_FILE_NAME)

        with open(file_path, 'w') as json_file:
            json_file.write(empty_tracker_json)

    def update_tracker(self, torrent_metadata, peer_info):
        """
        Updates the tracker's JSON file with the metadata of a new torrent
        and the information of the client (peer).

        Args:
            torrent_metadata (dict): Metadata of the torrent to be registered.
            peer_info (dict): Information about the client registering the torrent.
        Returns:
            None
        """
        print("Executing update_tracker...")

        file_path = os.path.join(self.TRACKER_DIRECTORY, self.TRACKER_FILE_NAME)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The tracker file '{file_path}' does not exist.")

        # Load existing tracker data
        with open(file_path, 'r') as file:
            tracker_data = json.load(file)

        # Check if the torrent already exists in the tracker
        existing_torrent = next((torrent for torrent in tracker_data["torrents"]
                                if torrent["info_hash"] == torrent_metadata["info_hash"]), None)

        if existing_torrent:
            peer_entry = {
                "ip": peer_info["ip"],
                "port": peer_info["port"],
                "peer_id": peer_info["peer_id"]
            }
            if peer_entry not in existing_torrent["peers"]:
                existing_torrent["peers"].append(peer_entry)
                existing_torrent["seeders"] += 1
        else:
            # Create a new torrent entry if it does not exist
            new_torrent = {
                "info_hash": torrent_metadata["info_hash"],
                "name": torrent_metadata["name"],
                "size": torrent_metadata["size"],
                "piece_size": torrent_metadata["piece_size"],
                "pieces": torrent_metadata["pieces"],
                "seeders": 1,
                "leechers": 0,
                "peers": [
                    {
                        "ip": peer_info["ip"],
                        "port": peer_info["port"],
                        "peer_id": peer_info["peer_id"]
                    }
                ]
            }
            tracker_data["torrents"].append(new_torrent)

        with open(file_path, 'w') as file:
            json.dump(tracker_data, file, indent=4)
        print("Tracker successfully updated.")

    def get_torrent_info(self, info_hash):
        """
        Retrieves the information of a torrent from the tracker's JSON file.

        Args:
            info_hash (str): ID of the torrent to retrieve.
        Returns:
            dict: Information of the torrent.
        """
        file_path = os.path.join(self.TRACKER_DIRECTORY, self.TRACKER_FILE_NAME)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The tracker file '{file_path}' does not exist.")

        with open(file_path, 'r') as file:
            tracker_data = json.load(file)

        torrent_info = next((torrent for torrent in tracker_data["torrents"]
                            if torrent["info_hash"] == info_hash), None)

        if not torrent_info:
            raise ValueError(f"The torrent was not found in the tracker.")
        
        message = json.dumps(torrent_info).encode()
        
        header = struct.pack("!I", len(message))
        
        message = header + message
        
        return message
        
    def handle_client(self, client_socket):
        try:
            while True:
                # Recibir el encabezado
                header = client_socket.recv(4)
                if not header:
                    break
                data_len = struct.unpack("!I", header)[0]
                data = client_socket.recv(data_len)

                # Procesar el mensaje
                message = json.loads(data.decode())
                print("Received message:")
                print(f"{message}")

                if message["type"] == "register_torrent":
                    torrent_metadata = message["torrent_metadata"]
                    peer_info = message["peer_info"]
                    self.update_tracker(torrent_metadata, peer_info)
                    message = "Torrent successfully registered.".encode()
                    header = struct.pack("!I", len(message))
                    
                    client_socket.sendall(header + message)

                elif message["type"] == "get_torrent":
                    info_hash = message["info_hash"]
                    try:
                        torrent_info = self.get_torrent_info(info_hash)
                        client_socket.sendall(torrent_info)
                    except Exception as e:
                        print(f"Error getting torrent info: {e}")
                        message = f"ERROR: Torrent not found in the tracker.".encode()
                        header = struct.pack("!I", len(message))
                        client_socket.sendall(header + message)
                else:
                    print("Invalid message type.")
                    client_socket.sendall(b"Invalid message type.")
        except Exception as e:
            print(f"Error processing client request: {e}")
        finally:
            print("Closing connection with: ", client_socket.getpeername())
            client_socket.close()

    def start_tracker(self, host="0.0.0.0", port=8080):
        """
        Starts the tracker server. Receives messages from clients and sends
        The message format (JSON) possibles are:
        - Register a new torrent: {"type": "register_torrent", "torrent_metadata": {...}, "peer_info": {...}}
        - Get torrent info: {"type": "get_torrent", "info_hash": "..."}

        Args:
            host (str): IP address to bind the server to (default is 0.0.0.0.)
            port (int): Port to bind the server to (default is 8000)
        Returns:
            None
        """
        server =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(5)
        print(f"Tracker server started at {host}:{port}")
        
        while True:
            client_socket, addr = server.accept()
            print(f"Connection from {addr}")
            
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True)
            client_thread.start()
