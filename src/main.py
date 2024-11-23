import os
from torrents.torrent_creator import TorrentCreator
from torrents.torrent_reader import TorrentReader
from torrents.torrent_info import TorrentInfo
from tracker.tracker import Tracker
from client.client import Client

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "tests/bigfile.txt")
    
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
        number_of_pieces=info["numberPieces"],
        pieces=pieces)
    
    print(torrent_info)
    
def test_server():
    tracker = Tracker()
    tracker.start_tracker()    

def test_client():
    client = Client(client_id="client1")
    client.connect_to_tracker(tracker_ip="0.0.0.0", tracker_port=8080)
    client.request_torrent_data(torrent_id="1")

if __name__ == '__main__':
    main()
    # ! Para probar el server y el cliente primero correr el server y luego el cliente
    # ! En dos terminales distintas
    # test_server()
    test_client() 