import json
import os
import socket

class Tracker:

    def create_initial_tracker(self, directory="."):
        """
        Creates an initial empty tracker data structure and saves it as a JSON
        file.
        
        This method constructs a dictionary representing the tracker with
        default values, serializes it to JSON, prints it for testing, and saves
        it to 'tracker_data.json'.

        Returns:
            None
        """
        
        def create_empty_tracker_data():
            tracker_data = {
                "torrents": [
                    {
                        "torrent_id": "",  # Torrent ID (hash)
                        "name": "",        # File name
                        "size": 0,        # Size in bytes
                        "pieces": [],     # List of pieces (initially empty)
                        "seeders": 0,     # Number of seeders
                        "leechers": 0,    # Number of leechers
                        "peers": []       # List of peers (initially empty)
                    }
                ]
            }
            
            return tracker_data

        empty_tracker_data = create_empty_tracker_data()

        empty_tracker_json = json.dumps(empty_tracker_data, indent=4)

        os.makedirs(directory, exist_ok=True)

        file_path = os.path.join(directory, 'tracker_data.json')
        print(f"Saving JSON to: {file_path}")

        with open(file_path, 'w') as json_file:
            json_file.write(empty_tracker_json)


    def update_tracker(self, torrent_metadata, peer_info, tracker_file="tracker_data.json"):
        """
        Updates the tracker's JSON file with the metadata of a new torrent
        and the information of the client (peer).

        Args:
            torrent_metadata (dict): Metadata of the torrent to be registered.
            peer_info (dict): Information about the client registering the torrent.
            tracker_file (str): Path to the tracker's JSON file (default is 'tracker_data.json').
        Returns:
            None
        """

        if not os.path.exists(tracker_file):
            raise FileNotFoundError(f"The tracker file '{tracker_file}' does not exist.")

        # Load existing tracker data
        with open(tracker_file, 'r') as file:
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

        
        with open(tracker_file, 'w') as file:
            json.dump(tracker_data, file, indent=4)
        print(f"Tracker successfully updated in {tracker_file}")

    def get_torrent_info(self, torrent_id, tracker_file="tracker_data.json"):
        """
        Retrieves the information of a torrent from the tracker's JSON file.

        Args:
            torrent_id (str): ID of the torrent to retrieve.
            tracker_file (str): Path to the tracker's JSON file (default is 'tracker_data.json').
        Returns:
            dict: Information of the torrent.
        """
        
        # TODO Etso con los directorios es un parche xq no me funcionaba bien
        
        actual_folder = os.path.dirname(os.path.abspath(__file__))
        tracker_file = os.path.join(actual_folder, os.path.join("database", tracker_file))

        if not os.path.exists(tracker_file):
            raise FileNotFoundError(f"The tracker file '{tracker_file}' does not exist.")

        with open(tracker_file, 'r') as file:
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
        # print(os.path.abspath(__file__))
           
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
            
            
            
             