import json
import os
import socket

class Tracker:
    TRACKER_DIRECTORY = "src/tracker/database"
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
        file_path = os.path.join(self.TRACKER_DIRECTORY, self.TRACKER_FILE_NAME)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The tracker file '{file_path}' does not exist.")

        # Load existing tracker data
        with open(file_path, 'r') as file:
            tracker_data = json.load(file)

        # Check if the torrent already exists in the tracker
        existing_torrent = next((torrent for torrent in tracker_data["torrents"]
                                if torrent["torrent_id"] == torrent_metadata["torrent_id"]), None)

        if existing_torrent:
            peer_entry = {
                "ip": peer_info["ip"],
                "port": peer_info["port"],
                "client_id": peer_info["client_id"]
            }
            if peer_entry not in existing_torrent["peers"]:
                existing_torrent["peers"].append(peer_entry)
                existing_torrent["seeders"] += 1
        else:
            # Create a new torrent entry if it does not exist
            new_torrent = {
                "torrent_id": torrent_metadata["torrent_id"],
                "name": torrent_metadata["name"],
                "size": torrent_metadata["size"],
                "pieces": torrent_metadata["pieces"],
                "seeders": 1,
                "leechers": 0,
                "peers": [
                    {
                        "ip": peer_info["ip"],
                        "port": peer_info["port"],
                        "client_id": peer_info["client_id"]
                    }
                ]
            }
            tracker_data["torrents"].append(new_torrent)

        with open(file_path, 'w') as file:
            json.dump(tracker_data, file, indent=4)

    def get_torrent_info(self, torrent_id):
        """
        Retrieves the information of a torrent from the tracker's JSON file.

        Args:
            torrent_id (str): ID of the torrent to retrieve.
        Returns:
            dict: Information of the torrent.
        """
        file_path = os.path.join(self.TRACKER_DIRECTORY, self.TRACKER_FILE_NAME)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The tracker file '{file_path}' does not exist.")

        with open(file_path, 'r') as file:
            tracker_data = json.load(file)

        torrent_info = next((torrent for torrent in tracker_data["torrents"]
                            if torrent["torrent_id"] == torrent_id), None)

        if not torrent_info:
            raise ValueError(f"The torrent with ID '{torrent_id}' was not found in the tracker.")
        
        return torrent_info
    
    def start_tracker(self, host="0.0.0.0", port=8080):
        """
        Starts the tracker server. Receives messages from clients and sends
        The message format (JSON) is: 
        {
            "torrent_id": "hash"
        }

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

            try:
                data = client_socket.recv(1024)
                message = json.loads(data.decode())
                print(f"Received message: {message}")

                torrent_id = message["torrent_id"]
                torrent_info = self.get_torrent_info(torrent_id)
                print(f"Sending torrent info: {torrent_info}")

                client_socket.sendall(json.dumps(torrent_info).encode())
            except Exception as e:
                print(f"Error processing client request: {e}")
            finally:
                client_socket.close()

