import socket
import json
from typing import Dict, List
from client.peer import Peer
from torrents.torrent_creator import TorrentCreator
from torrents.torrent_reader import TorrentReader
from torrents.torrent_info import TorrentInfo
import os
import threading
import struct

class Client:
    def __init__(self, client_id: int, listen_port = 6881):
        self.client_id = client_id
        self.tracker_socket = None
        self.torrents_downloading = {}
        # Dict[info_hash, List[bool]] where the index of the list represents a piece
        self.pieces_downloaded: Dict[str,List[bool]]  = {}
        
        # Path is the actual path of this file concatenated with the download folder
        # and client_id
        self.download_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"downloads/client_{client_id}")
        self.upload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"uploads/client_{client_id}")
        # print(self.download_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        if not os.path.exists(self.upload_path):
            os.makedirs(self.upload_path)
            
        self.listen_port = listen_port
        self.server_socket = None
        
        # Dict[info_hash, Dict[piece_index, piece_data]]
        self.uploaded_files = {}
        self.find_uploaded_files()
        
    def find_uploaded_files(self):
        # TODO
        """
        Find the files that the client has uploaded.
        """
        torrents_path = os.path.join(self.upload_path, "torrents")
        if not os.path.exists(torrents_path):
            os.makedirs(torrents_path)
        data_path = os.path.join(self.upload_path, "data")
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            
        for file_name in os.listdir(torrents_path):
            if file_name.endswith(".torrent"):
                torrent_name = file_name.split(".")[0]
                torrent_json_data = os.path.join(torrents_path,torrent_name + ".json")
                if os.path.exists(torrent_json_data):
                    with open(torrent_json_data, "r") as file:
                        torrent_data = json.load(file)
                        path = os.path.join(data_path, torrent_data["name"])
                        if os.path.exists(path):
                            self.uploaded_files[torrent_name] = path
                            print(f"Found uploaded file {torrent_data['name']} with name {torrent_name}")
                    
                
    
    def start_peer_mode(self):
        # TODO
        """
        Start the client in peer mode to handle incoming requests. 
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ip = '0.0.0.' + str(self.client_id)
            self.server_socket.bind((ip, self.listen_port))
            self.server_socket.listen(5)
            print(f"Client {self.client_id} listening on port {self.listen_port}")

            # Thread para aceptar múltiples conexiones entrantes
            threading.Thread(target=self.handle_incoming_connections, daemon=True).start()
        except Exception as e:
            raise RuntimeError(f"Error starting peer mode: {e}")
    

    def handle_incoming_connections(self):
        """
        Handle incoming connections from other peers.
        """
        while True:
            conn, addr = self.server_socket.accept()
            print(f"Incoming connection from {addr}")
            # Thread para manejar cada conexión
            
            threading.Thread(target=self.handle_connection, args=(conn, addr), daemon=True).start()
            
    def handle_connection(self, conn, addr):
        # TODO
        """
        Handle a connection from a peer.
        """
        try:
            data = conn.recv(1024).decode()

            if not data:
                return
            
            # process request message
            request = struct.unpack(">IbIII", data) # <len=0013><id=6><index><begin><length>
            _, message_id, index, begin, length = request
            
            if message_id == 6:  # ID de mensaje 'request'
                piece_data = self.files.get(index, b"")[begin:begin + length]

                # Enviar respuesta (mensaje 'piece')
                # Formato: <len=0009+X><id=7><index><begin><block>
                response = struct.pack(">IbII", 9 + len(piece_data), 7, index, begin) + piece_data
                conn.send(response)
                print(f"Sent piece {index} (offset: {begin}, length: {length})")
                
        except Exception as e:
            print(f"Error handling connection from {addr}: {e}")
        finally:
            conn.close()
            
        
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

    def request_torrent_data(self, info_hash):
        """
        Sends a request (JSON) to the tracker server for the torrent data.
        Receives the torrent data from the tracker server.
        
        Request format:
        {
            "type": "get_torrent",
            "info_hash": "hash"
        }
        
        
        Args:
            info_hash (str): The info hash of the torrent.
        Returns:
            response: The torrent data from the tracker server.
        
        Example response:
            {
              "info_hash": "hash",
              "name": "Torrent de prueba",
              "size": 1024,
              "pieces": "hash1hash2hash3",
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
                "type": "get_torrent",
                "info_hash": info_hash
            }

            request = json.dumps(request)

            self.tracker_socket.send(request.encode())

            response = self.tracker_socket.recv(1024).decode()

            response = json.loads(response)

            self.torrents_downloading[info_hash] = response
            
            length = int(response["size"]) // int(response["piece_size"])
            
            self.pieces_downloaded[info_hash] = [False] * length

            return response
        
        except Exception as e:
            raise ConnectionError(f"Error requesting torrent data: {e}")
        
    def start_download(self, info_hash):
        # TODO
        """
        Start downloading the torrent data from peers.
        """
        torrent_data = self.torrents_downloading.get(info_hash)

        if not torrent_data:
            raise ValueError(f"The torrent with ID '{info_hash}' was not found in the client.")
        
        pieces = torrent_data["pieces"]
        peers = torrent_data["peers"]
        piece_size = torrent_data["piece_size"]
        
        for peer_info in peers:
            peer = Peer(peer_info["peer_id"], peer_info["ip"], peer_info["port"])
            peer.connect()
            for piece_index, piece_hash in enumerate(pieces):
                peer = Peer(peer_info["peer_id"], peer_info["ip"], peer_info["port"])
                try:
                    peer.connect()
                    
                    for index, piece_hash in enumerate(pieces):
                        if self.pieces_downloaded[info_hash][index]:
                            continue
                        
                        peer.request_piece(index,0,piece_size)
                        data = peer.receive_piece(piece_size)
                        
                        self.pieces_downloaded[info_hash][index] = True
                        print(f"Downloaded piece {index} from peer {peer.id}")

                        # save data in download folder
                        file_path = os.path.join(self.download_path, f"{info_hash}_{index}")
                        with open(file_path, "wb") as file:
                            file.write(data)
                        # self.files[info_hash] = self.files.get(info_hash, {})
                        # self.files[info_hash][index] = data
                        
                    peer.close()
                    break
            
                except Exception as e:
                    print(f"Error downloading piece from peer {peer.id}: {e}")
                    peer.close()
                    continue
        
        # build the file
        self.build_file(info_hash)
        print("Download torrent "+ info_hash + " completed")
        
    def build_file(self,info_hash):
        # TODO
        """
        Build the file from the pieces downloaded.
        """
        pieces = self.torrents_downloading[info_hash]["pieces"]
        piece_size = self.torrents_downloading[info_hash]["piece_size"]
        
        file_path = os.path.join(self.download_path, f"{info_hash}.txt")
        
        with open(file_path, "wb") as file:
            for index, piece_hash in enumerate(pieces):
                piece_file_path = os.path.join(self.download_path, f"{info_hash}_{index}")
                with open(piece_file_path, "rb") as piece_file:
                    file.write(piece_file.read())
        
        print(f"File {file_path} built")
                
    def close(self):
        """
        Close the connection with the tracker.
        """
        if self.tracker_socket:
            self.tracker_socket.close()
            print("Connection closed with tracker")
            
        if self.server_socket:
            self.server_socket.close()
            print("Server socket closed")
    
    def create_torrent_file(self, file_path, tracker_ip=None, tracker_port=None, output_path=None):
        """
        Create a torrent file for a given file.
        
        Args:
            file_path (str): The path to the file to create the torrent for.
            tracker_ip (str): IP address of the tracker server.
            tracker_port (int): Port number of the tracker server.
            output_path (str): The path to save the torrent file.
        Returns:
            None
        """
        
        if not tracker_ip or not tracker_port:
            tracker_ip = self.tracker_socket.getsockname()[0]
            tracker_port = self.tracker_socket.getsockname()[1]
            
            
        torrent_creator = TorrentCreator(tracker_ip, tracker_port)
        
        
        output_path = torrent_creator.create_torrent(file_path=str(file_path), output_path=output_path)
        
        return output_path
    
    def upload_torrent_file(self, torrent_file_path):
        """
        Upload a torrent file to the tracker server.
        
        Args:
            torrent_file_path (str): The path to the torrent file to upload.
        Returns:
            None
        """
        torrent_data = TorrentReader.read_torrent(torrent_file_path)
        torrent_info = TorrentReader.extract_info(torrent_data)
        

        request = {
            "type": "register_torrent",
            "torrent_metadata": 
                {
                    "info_hash": torrent_info.info_hash,
                    "name": torrent_info.name,
                    "size": torrent_info.length,
                    "piece_size": torrent_info.piece_length,
                    "pieces": torrent_info.pieces,
                },
            "peer_info": {
                "peer_id": self.client_id,
                "ip": "0.0.0." + str(self.client_id),
                "port": self.listen_port
            }    
        }
        
        
        request = json.dumps(request)
        
        try:
            message = request.encode()
            header = struct.pack('>I', len(message))
            
            message = header + message
            
            self.tracker_socket.send(message)
            
            response = self.tracker_socket.recv(1024).decode()
            print(f"Tracker response: {response}")
        except Exception as e:
            raise ConnectionError(f"Error uploading torrent file: {e}")
    
    def Run(self):
        """
        Run the client console application.
        """
        print("Client console application")
        print("Commands:")
        print("1. connect <tracker_ip> <tracker_port>")
        print("2. get_torrent <info_hash>")
        print("3. download <info_hash>")
        print("4. create_torrent <file_path>")
        print("5. upload_torrent <torrent_file_path>")
        print("6. exit")
        
        while True:
            command = input("Enter a command: ")
            command = command.split()
            
            if command[0] == "connect":
                self.connect_to_tracker(command[1], int(command[2]))
            elif command[0] == "get_torrent":
                self.request_torrent_data(command[1])
            elif command[0] == "download":
                self.start_download(command[1])
            elif command[0] == "create_torrent":
                self.create_torrent_file(file_path=str(command[1]))
            elif command[0] == "upload_torrent":
                self.upload_torrent_file(command[1])
            elif command[0] == "exit":
                self.close()
                break