import json
import os

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


    def update_tracker(torrent_metadata, peer_info, tracker_file="tracker_data.json"):
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
