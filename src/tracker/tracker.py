import json
import os
import socket
import struct
import threading
import sys
import select
import hashlib
import math
from threading import Timer
from common.logs import log_message

class Node(object):
    """ 
    Class that represents a node in the CHORD protocol.
    
    Attributes:
    - ip_address: str, the IP address of the node.
    - m: int, the number of bits of the hash function.
    - finger_table: list, the finger table of the node.
    - id: int, the identifier of the node.
    - successor: Node, the successor of the node.
    - predecessor: Node, the predecessor of the node.
    """
    def __init__(self, ip_address, m=6, port=8080):
        self.ip_address = ip_address
        self.m = m
        self._id = None
        self.port = port
        self.keys = {} #Esto es nuestro dataset json
        
        # Estructuras Chord
        self.finger_table = []
        self.predecessor = None
        self.successors = []  # Sucesores, k=2
        self.stabilizer = None  # Para el proceso periódico de estabilización
        
        # conexión
        self.server_socket = None

    @property
    def id(self):
        if self._id is None:
            self._id = self.hash_function(self.ip_address, self.m)
        return self._id

    def join(self, existing_node_ip=None):
        """Une el nodo a la red Chord"""
        if existing_node_ip:
            
            socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket.connect((existing_node_ip, self.port))

            r = self.send_message(socket, {"type": "find_successor", "data": self.id})
            
            self.successors = [r["ip"], r["sucessors"][0]]
            self.predecessor = None
            
            self.create_finger_table()
            
            self.update_others()
            
            self.schedule_stabilize()
        else:
            self.successors = [self]
            self.predecessor = self
            self.create_finger_table()

    # def leave(self):
    #     if self.successors:
    #         self.successors[0].keys.update(self.keys)
    #     if self.predecessor:
    #         self.predecessor.successors = [
    #             s if s.id != self.id else self.successors[0] 
    #             for s in self.predecessor.successors
    #         ]
            
    #     if self.stabilizer:
    #         self.stabilizer.cancel()

    def create_finger_table(self):
        self.finger_table = []
        for i in range(1, self.m + 1):
            start = (self.id + 2**(i-1)) % 2**self.m
            successor = self.find_successor(start)
            self.finger_table.append(successor)

    def find_successor(self, key_id):
        """Encuentra el sucesor de una clave usando la finger table"""
        if self == self.successors[0]:  # Caso de 1 solo nodo
            return self
            
        # Verificar si la clave está entre nosotros y el primer sucesor
        if self._is_between(key_id, self.id, self.successors[0].id):
            return self.successors[0]
        else:
            # Encontrar el nodo más cercano en la finger table
            closest = self.closest_preceding_node(key_id)
            
            socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket.connect((closest["ip_address"], self.port))
            
            r = self.send_message(socket, {"type": "find_successor", "data": key_id})
            
            return r["successor"]
        
    def closest_preceding_node(self, key_id):
        """Encuentra el nodo más cercano en la finger table que precede a la clave"""
        for node in reversed(self.finger_table):
            if self._is_between(node.id, self.id, key_id):
                return node
        return self

    def update_others(self):
        """Actualiza los finger tables de otros nodos afectados
        Esta función está muy cuestionable aún
        """
        for i in range(1, self.m + 1):
            predecessor = self.find_predecessor((self.id - 2**(i-1)) % 2**self.m)
            predecessor.update_finger_table(self, i)

    def update_finger_table(self, node, i):
        """Actualiza la entrada i-ésima de la finger table si node es relevante"""
        start = (self.id + 2**(i-1)) % 2**self.m
        if self._is_between(node.id, start, self.finger_table[i-1].id):
            self.finger_table[i-1] = node
            predecessor = self.predecessor
            predecessor.update_finger_table(node, i)

    def schedule_stabilize(self):
        """Programa la estabilización periódica"""
        self.stabilize()
        self.stabilizer = Timer(5.0, self.schedule_stabilize)
        self.stabilizer.start()

    def stabilize(self):
        """Corrige sucesores y predecesores
        A esta función se le pueden añadir otras cosas como verificar la permanencia aún en la red
        del sucesor
        """
        successor = self.successors[0]
        predecessor = successor.get_predecessor()
        
        if predecessor and self._is_between(predecessor.id, self.id, successor.id):
            self.successors = [predecessor, *successor.successors[:1]]
        
        successor.notify(self)
        
        self.successors = [successor, *successor.successors[:1]]

    def notify(self, node):
        """Notifica a este nodo que 'node' podría ser su predecesor"""
        if not self.predecessor or self._is_between(node.id, self.predecessor.id, self.id):
            self.predecessor = node

    def _is_between(self, value, start, end):
        """Determina si value está en el intervalo (start, end] circular"""
        if start < end:
            return start < value <= end
        else:
            return value > start or value <= end

    def get_predecessor(self):
        return self.predecessor

    def set_predecessor(self, node):
        self.predecessor = node

    def dict(self):
        return {
            'ip': self.ip_address,
            'id': self.id,
            'successors': [s.id for s in self.successors],
            'predecessor': self.predecessor.id if self.predecessor else None
        }

    def __repr__(self):
        return f"Node({self.id}, {self.ip_address})"
    
    def send_message(self, socket, message):
        """
        Sends a message to a socket.

        Args:
            socket (socket.socket): The socket to send the message to.
            message (dict): The message to send.
        Returns:
            dict: The response received from the socket.
            
        Message format:
        {
            "type": str,    #(normalmente es el nombre de la función a llamar)
            ...
        }
        
        """
        message = json.dumps(message).encode()
        header = struct.pack("!I", len(message))
        
        socket.sendall(header + message)
        
        header = socket.recv(4)
        data_len = struct.unpack("!I", header)[0]
        
        data = socket.recv(data_len)
        
        return json.loads(data.decode())
    def hash_function(key, m):
        # Hash SHA-1 truncado a m bits (ej: m=6 → 0-63)
        hash_bytes = hashlib.sha1(key.encode()).digest()
        hash_int = int.from_bytes(hash_bytes, byteorder='big')
        return hash_int % (2**m)

    
class Tracker(Node):
    def __init__(self, ip_address="0.0.0.0", m=6):
        super().__init__(ip_address, m)
    
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
        
        if os.path.exists(os.path.join(self.TRACKER_DIRECTORY, self.TRACKER_FILE_NAME)):
            return
        
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
                elif message["type"] == "find_successor":
                    key_id = message["data"]
                    successor = self.find_successor(key_id)
                    response = {"successor": successor.dict()}
                    header = struct.pack("!I", len(json.dumps(response).encode()))
                    
                    message = header + json.dumps(response).encode()
                    client_socket.sendall(message)
                    
                else:
                    print("Invalid message type.")
                    client_socket.sendall(b"Invalid message type.")
        except Exception as e:
            print(f"Error processing client request: {e}")
        finally:
            print("Closing connection with: ", client_socket.getpeername())
            client_socket.close()

    def start_tracker(self, host=None, port=None):
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
        if host is None:
            host = self.ip_address
            
        if port is None:
            port = self.port
        
        self.create_initial_tracker()
        
        self.server_socket =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"Tracker server started at {host}:{port}")
        
        while True:
            # Check for keyboard input or incoming connections
            readable, _, _ = select.select([self.server_socket, sys.stdin], [], [], 0.1)
            for r in readable:
                if r is sys.stdin:
                    user_input = sys.stdin.read(1)  # Read a single character
                    if user_input.strip().lower() == "q":  # Exit on 'q'
                        print("Exiting tracker server...")
                        self.server_socket.close()
                        return

                if r is self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    print(f"Connection from {addr}")

                    try:
                        client_thread = threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True)
                        client_thread.start()
                    except Exception as e:
                        print(f"Error handling client {addr}: {e}")