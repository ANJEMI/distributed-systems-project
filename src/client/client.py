import os
import threading
import struct
import socket
import json
import random
import hashlib
import random
import hashlib
import shutil
import subprocess
import readline
from typing import Dict, List


from client.peer.peer import Peer
from client.peer.block import BLOCK_SIZE
from torrents.torrent_creator import TorrentCreator
from torrents.torrent_reader import TorrentReader
from client.peer.piecesController import PieceController
from client.peer.piece import Piece
from torrents.torrent_info import TorrentInfo
from client.messages import *

class Client:
    def __init__(self, client_id: int, listen_port = 6881):
        hostname = socket.gethostname()
        self.client_id = client_id
        self.tracker_socket = None
        self.client_ip = socket.gethostbyname(hostname) 
        self.download_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"downloads/client_{client_id}")
        self.upload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"uploads/client_{client_id}")
        self.torrents_path = os.path.join(self.upload_path, "torrents")
        self.data_path = os.path.join(self.upload_path, "data")
        
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        if not os.path.exists(self.upload_path):
            os.makedirs(self.upload_path)
        os.makedirs(self.torrents_path, exist_ok=True)
        os.makedirs(self.data_path, exist_ok=True)
            
        # self.listen_port = listen_port + self.client_id
        self.listen_port = listen_port
        self.server_socket = None
        
        self.uploaded_files = {}
        self.find_uploaded_files()
        
    def find_uploaded_files(self):
        """
        Find the files that the client has uploaded.
        """
        
        for file_name in os.listdir(self.torrents_path):
            if file_name.endswith(".torrent"):
                name_file = file_name.split(".")[0]
                
                torrent_file_path = os.path.join(self.torrents_path, file_name)
                torrent_data = TorrentReader.read_torrent(torrent_file_path)
                torrent_info : TorrentInfo = TorrentReader.extract_info(torrent_data)
                
                data = {
                    "torrent_file_path": torrent_file_path,
                    "torrent_info": torrent_info
                }
                
                self.uploaded_files[name_file] = data
        
        for file_name in os.listdir(self.data_path):
            name_file = file_name.split(".")[0]
            print(name_file)
            if name_file not in self.uploaded_files:
                pass
            else:
                self.uploaded_files[name_file]["data_file_path"] = os.path.join(self.data_path, file_name)
                    
        print("The following files have been uploaded:")
        for file_name in self.uploaded_files:
            print(file_name, end=" ")
            print()
            
                    
    def start_peer_mode(self):
        """
        Start the client in peer mode to handle incoming requests.
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.client_ip, self.listen_port))
            self.server_socket.listen(5)
            print(f"Client {self.client_id} listening on port {self.listen_port} and IP {self.client_ip}")

            while True:
                try:
                    conn, addr = self.server_socket.accept()
                    print(f"Incoming connection from {addr}")
                    # Thread para manejar cada conexión
                    threading.Thread(target=self.handle_connection, args=(conn, addr), daemon=True).start()
                except Exception as e:
                    print(f"Error accepting connection: {e}")

        except Exception as e:
            raise RuntimeError(f"Error starting peer mode: {e}")

    def handle_connection(self, conn, addr):
        try:
            handshake = conn.recv(Handshake.LENGTH)
            
            print("LLEGA AQUI")
            info_hash, peer_id = Handshake.from_bytes(handshake)
            
            print(f"Info hash: {info_hash}")
            
            
            info_hash = info_hash.hex()
            
            data = self.find_info_hash(info_hash)
            
            if not data:
                print(f"Info hash {info_hash} not found")
                return
            
            while True:
                message = conn.recv(4)
                if not message:
                    break
                
                length = struct.unpack("!I", message)[0]
                message = message + conn.recv(length)
                
                piece_index, block_offset, block_length = Request.from_bytes(message)
                
                f = open(data["data_file_path"], "rb")
                
                f.seek(piece_index * data["torrent_info"].piece_length + block_offset)
                block = f.read(block_length)
                f.close()
                
                response = Piece(piece_index, block_offset, block).to_bytes()
                
                conn.send(response)
            
            
        except Exception as e:
            print(f"Error handling connection from {addr}: {e}")

    def find_info_hash(self, info_hash):
        """
        Find the info hash in the uploaded files.
        
        data = {
                    "torrent_file_path": torrent_file_path,
                    "torrent_info": torrent_info,
                    "data_file_path": data_file_path
                }
        
        Args:
            info_hash (str): The info hash to find.
        Returns:
            data: The data of the file with the info hash.
        """
        for file_name in self.uploaded_files:
            if self.uploaded_files[file_name]["torrent_info"].info_hash == info_hash:
                return self.uploaded_files[file_name]
        
        return None
        
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

        """
        
        if not self.tracker_socket:
            raise ConnectionError("The client is not connected to the tracker.")
        
        try:
            request = {
                "type": "get_torrent",
                "info_hash": info_hash
            }

            request = json.dumps(request)
            
            message = request.encode()
            header = struct.pack('>I', len(message))
            
            message = header + message

            self.tracker_socket.send(message)
            
            header = self.tracker_socket.recv(4)
            data_len = struct.unpack("!I", header)[0]
            
            print(f"Data length: {data_len}")
            response = self.tracker_socket.recv(data_len).decode()
            print(f"Response: {response}")
            
            # response = """{"in""" + response
            if "ERROR" in response:
                print(response)
                return None
            
            response = json.loads(response)
            

            # todo delete?
            # self.torrents_downloading[info_hash] = response
            
            print(f"Torrent data received. Info hash: {info_hash}")

            return response
        
        except Exception as e:
            raise ConnectionError(f"Error requesting torrent data: {e}")
     
    def get_free_peers(self, peers_connected):
        """
        Get the peers that are not blocked.
        
        Args:
            peers_connected (List[Peer]): The list of peers connected.
        Returns:
            free_peers (List[Peer]): The list of free peers.
        """
        free_peers = []
        for peer in peers_connected:
            if not peer.blocked:
                free_peers.append(peer)
                
        return free_peers   

    def download_piece(self, piece: Piece, peers_connected, pieces_controller: PieceController, output_path):
        while not piece.is_complete():
            data = pieces_controller.get_empty_block(piece.piece_index)
            if not data:
                continue

            piece_index, block_index, block = data
            
            block_offset = block_index * BLOCK_SIZE
            
            free_peers: List[Peer] = self.get_free_peers(peers_connected)
            if not free_peers:
                continue
            
            random_peer: Peer = random.choice(free_peers)

            try:
                block_data = random_peer.request_piece(piece_index, block_offset, block.block_size)
                pieces_controller.receive_block(piece_index=piece_index, block_index=block_index, data=block_data)
            except Exception as e:
                print(f"Error downloading block: {e}")

        if piece.set_total_data():
            piece.save_piece(output_path)
            print(f"Piece {piece.piece_index} downloaded from peer: {random_peer.id}")

    def start_download(self, torrent_data):
        print("Log: comenzó la descarga")

        data = TorrentInfo(
            announce="",
            info_hash=torrent_data["info_hash"],
            name=torrent_data["name"],
            piece_length=torrent_data["piece_size"],
            length=torrent_data["size"],
            pieces=torrent_data["pieces"]
        )

        peers = torrent_data["peers"]
        peers_connected = []
        for peer in peers:
            p = Peer(peer["peer_id"], peer["ip"], peer["port"])
            try:
                p.connect()
                hash_bytes = bytes.fromhex(torrent_data["info_hash"])
                p.send_message(Handshake(info_hash=hash_bytes).to_bytes())
                peers_connected.append(p)
            except Exception as e:
                print(f"Error connecting to peer {peer['peer_id']}: {e}")
            
        if len(peers_connected) == 0:
            print("No se pudo conectar a ningún peer")
            return

        output_path = os.path.join(self.download_path, torrent_data["name"])
        pieces_controller = PieceController(data, output_path)

        print("Log: comenzó la descarga")

        threads = []
        for piece in pieces_controller.pieces:
            if not pieces_controller.bitfield[piece.piece_index]:
                t = threading.Thread(target=self.download_piece, args=(piece, peers_connected, pieces_controller, output_path))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        print("Log: descarga completada")

                
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
            
            
        torrent_creator = TorrentCreator(tracker_url="www.thepiratebay.org")
        
        
        output_path = torrent_creator.create_torrent(file_path=str(file_path))
        shutil.copy(output_path, self.torrents_path)
        shutil.copy(file_path, self.data_path)
        self.find_uploaded_files()
        
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
                "ip": str(self.client_ip),
                "port": self.listen_port 
            }    
        }
        
        
        request = json.dumps(request)
        
        try:
            message = request.encode()
            header = struct.pack('>I', len(message))
            
            message = header + message
            
            self.tracker_socket.send(message)
            header = self.tracker_socket.recv(4)
            data_len = struct.unpack("!I", header)[0]
            response = self.tracker_socket.recv(data_len).decode()
            print(f"Tracker response: {response}")
            self.uploaded_files 
        except Exception as e:
            raise ConnectionError(f"Error uploading torrent file: {e}")
    

    def Run(self):
        """
        Run the client console application.
        """

        RESET = "\033[0m"
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"

        COMMANDS = [
            "connect_tr",
            "drop_tracker",
            "get_torrent",
            "start_seeding",
            "download",
            "create_torrent",
            "upload_torrent",
            "exit"
        ]

        # shell util
        def completer(text, state):
            options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
            if state < len(options):
                return options[state]
            else:
                return None
        def print_commands():
            readline.set_completer(completer)
            readline.parse_and_bind("tab: complete")

            print(f"{BLUE}Client console application{RESET}")
            print(f"{YELLOW}Commands:{RESET}")
            print("1. connect_tr")
            print("2. get_torrent <info_hash>")
            print("3. download <info_hash>")
            print("4. create_torrent <file_path>")
            print("5. upload_torrent <torrent_file_path>")
            print("6. drop_tracker")
            print("7. start_seeding")
            print("8. help")
            print("9. exit")
        
        print_commands()

        while True:
            command = input(f"{GREEN}Enter a command: {RESET}")
            command = command.split()
            
            try:
                if command[0] == "connect_tr":
                    self.connect_to_tracker("10.0.11.2", 8080)
                elif command[0] == "drop_tracker":
                    self.close()
                elif command[0] == "get_torrent":
                    self.request_torrent_data(command[1])
                elif command[0] == "start_seeding":
                    self.start_peer_mode()
                elif command[0] == "download":
                    r = self.request_torrent_data(command[1])
                    if r:
                        self.start_download(r)
                elif command[0] == "create_torrent":
                    self.create_torrent_file(file_path=str(command[1]))
                elif command[0] == "upload_torrent":
                    self.upload_torrent_file(command[1])
                elif command[0] == "help":
                    print_commands()
                elif command[0] == "exit":
                    break
                else:
                    print(f"{RED}Unknown command. Please try again.{RESET}")
                    # Intentar ejecutar el comando como un comando de Bash
                    try:
                        result = subprocess.run(command, capture_output=True, text=True, check=True)
                        print(result.stdout)  # Mostrar la salida del comando
                    except subprocess.CalledProcessError as e:
                        print(f"{RED}Error executing command: {e}{RESET}")
                    except FileNotFoundError:
                        print(f"{RED}Command not found: {command[0]}{RESET}")
            except IndexError:
                print(f"{RED}Error: Missing arguments. Please check your command.{RESET}")
            except ValueError:
                print(f"{RED}Error: Invalid value. Please check your input.{RESET}")
            except Exception as e:
                print(f"{RED}An error occurred: {e}{RESET}")

