import os
import sys
from torrents.torrent_creator import TorrentCreator
from torrents.torrent_reader import TorrentReader
from torrents.torrent_info import TorrentInfo
from tracker.tracker import Tracker
from client.client import Client

base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")

def main():
    file_path = os.path.join(base_path, "bigfile.txt")
    
    tracker = Tracker()
    tracker.create_initial_tracker()

    torrent_creator = TorrentCreator(
        tracker_url="localhost", 
        piece_length=256 * 1024)
    
    output_path= torrent_creator.create_torrent(
        file_path= file_path)
    
    print(f"Torrent file created at: {output_path}")
    
    torrent_data = TorrentReader.read_torrent(output_path)
    info = TorrentReader.extract_info(torrent_data)
    pieces = TorrentReader.extract_pieces(torrent_data)
    
    torrent_info = TorrentInfo(
        announce=info["announce"],
        name=info["name"],
        piece_length=info["pieceLength"],
        length=info["length"],
        pieces=pieces)
    
    print(torrent_info)
    
def create_torrents(file_path, tracker_url):

    torrent_creator = TorrentCreator(
        tracker_url=tracker_url, 
        piece_length=256 * 1024)
    
    output_path= torrent_creator.create_torrent(
        file_path= file_path)
    
    print(f"Torrent file created at: {output_path}")
    
    torrent_data = TorrentReader.read_torrent(output_path)
    info = TorrentReader.extract_info(torrent_data)
    
    torrent_info = TorrentInfo(
        announce=info["announce"],
        name=info["name"],
        piece_length=info["pieceLength"],
        length=info["length"],
        pieces=info["pieces"])
    
    print(torrent_info)
    
def test_server():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "tests/bigfile.torrent")
    
    info = TorrentReader.extract_info(file_path)
    
    tracker = Tracker()

    torrent_metadata = {
        "torrent_id": "1",
        "name": "Torrent de prueba",
        "size": 1024,
        "piece_size": 256,  # Example piece size in bytes
        "pieces": ["a", "b", "c"],  # List of pieces
        "number_of_pieces": 3  # Example number of pieces
    }

    peer_info = {
        "ip": "192.168.1.2",
        "port": 6882,
        "client_id": "2"
    }

    tracker.update_tracker(torrent_metadata, peer_info)

    # Call the update_tracker method
    tracker.start_tracker()



def test_client():
    client = Client(client_id=1)
    client.connect_to_tracker(tracker_ip="0.0.0.0", tracker_port=8080)
    client.request_torrent_data(torrent_id="1")

def main():
    """
    Main entry point for the program. Handles running the server or client based on the input argument.
    
    # Example usage:
    # python main.py server
    # python main.py client
    
    """
    if len(sys.argv) < 2:
        print("Usage: python script_name.py [server|client]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "server":
        test_server()
    elif mode == "client":
        test_client()
    else:
        print("Invalid argument. Use 'server' or 'client'.")
        sys.exit(1)

if __name__ == '__main__':
    # main()
    create_torrents(file_path= os.path.join(base_path, "bigfile.txt"), tracker_url="0.0.0.0")
