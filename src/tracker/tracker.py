import json
import os
import socket as socket
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
    def __init__(self, ip_address, m=5, port=8080):
        self.ip_address = ip_address
        self.m = m
        self._id = None
        self.port = port
        self.keys = {} #Esto es nuestro dataset json
        
        # Estructuras Chord
        self.finger_table = []
        self.predecessor = None
        self.successors = [None,None]  # Sucesores, k=2
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
            print(f"Entro en join con {existing_node_ip}")
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((existing_node_ip, self.port))
            print(f"Conectado a {existing_node_ip}")
            
            r = self.send_message(s, {"type": "find_successor", "data": self.id})
            
            self.successors[0] = r["successor"]
            self.predecessor = None
            
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.connect((self.successors[0], self.port))
            self.send_message(s2, {"type": "notify", "data": self.ip_address})
            print(f"Enviado notify a {self.successors[0]}")
            
            self.create_finger_table()
            
            self.update_others()
            
            # self.schedule_stabilize()
        else:
            self.successors = [self.ip_address]
            self.predecessor = self.ip_address
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
        if self.ip_address == self.successors[0]:  # Caso de 1 solo nodo
            return self.ip_address
            
        
        successor_id = self.hash_function(self.successors[0], self.m)
        # Verificar si la clave está entre nosotros y el primer sucesor
        if self._is_between(key_id, self.id, successor_id):
            return self.successors[0]
        else:
            # Encontrar el nodo más cercano en la finger table
            closest = self.closest_preceding_node(key_id)
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((closest, self.port))
            
            r = self.send_message(s, {"type": "find_successor", "data": key_id})
            
            return r["successor"]
        
    def closest_preceding_node(self, key_id):
        """Encuentra el nodo más cercano en la finger table que precede a la clave"""
        for node in reversed(self.finger_table):
            node_id = self.hash_function(node, self.m)
            if self._is_between(node_id, self.id, key_id):
                return node
        return self.ip_address
            
    def find_predecessor(self, key_id):
        """Encuentra el predecesor de una clave"""
        if self.ip_address == self.successors[0]:
            return self.ip_address
        
        successor_id = self.hash_function(self.successors[0], self.m)
        if self._is_between(key_id, self.id, successor_id):
            return self.ip_address
        else:
            closest = self.closest_preceding_node(key_id)
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((closest, self.port))
            
            r = self.send_message(s, {"type": "find_predecessor", "data": key_id})
            
            return r["predecessor"]

    def schedule_stabilize(self):
        """Programa la estabilización periódica"""
        self.stabilize()
        self.stabilizer = Timer(5.0, self.schedule_stabilize)
        self.stabilizer.start()

    def notify(self, node):
        """Notifica a este nodo que 'node' podría ser su predecesor"""
        node_id = self.hash_function(node, self.m)
        p_id = self.hash_function(self.predecessor, self.m) if self.predecessor else None
        
        if not self.predecessor or self._is_between(node_id, p_id, self._id):
            self.predecessor = node

    def _is_between(self, value, start, end):
        """Determina si value está en el intervalo (start, end] circular"""
        if start is None or end is None:
            return False
        if start < end:
            return start < value <= end
        else:
            return value > start or value <= end

    def get_predecessor(self):
        return self.predecessor

    def set_predecessor(self, node):
        self.predecessor = node
    
    def stabilize(self):
        """Corrige sucesores y predecesores"""
        if not self.successors:
            return

        successor_ip = self.successors[0]

        # Obtener predecesor del sucesor
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((successor_ip, self.port))
                response = self.send_message(s, {"type": "get_predecessor"})
                predecessor_of_successor = response.get("predecessor", None)
        except Exception as e:
            print(f"Error al contactar al sucesor {successor_ip}: {e}")
            return

        # Verificar si el predecesor del sucesor debe ser nuestro nuevo sucesor
        if predecessor_of_successor:
            pred_id = self.hash_function(predecessor_of_successor, self.m)
            succ_id = self.hash_function(successor_ip, self.m)
            if self._is_between(pred_id, self.id, succ_id):
                self.successors[0] = predecessor_of_successor

        # Notificar al sucesor sobre nuestra existencia
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.successors[0], self.port))
                self.send_message(s, {"type": "notify", "data": self.ip_address})
        except Exception as e:
            print(f"Error al notificar al sucesor {self.successors[0]}: {e}")

        # Actualizar lista de sucesores con los del sucesor (k=2)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.successors[0], self.port))
                response = self.send_message(s, {"type": "get_successors"})
                new_successors = response.get("successors", [])
                if new_successors:
                    self.successors = [self.successors[0]] + new_successors[:1]
                else:
                    self.successors = [self.successors[0]]
        except Exception as e:
            print(f"Error al obtener sucesores de {self.successors[0]}: {e}")

    def update_others(self):
        """Actualiza los finger tables de otros nodos afectados"""
        for i in range(1, self.m + 1):
            predecessor_ip = self.find_predecessor((self.id - 2**(i-1)) % 2**self.m)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((predecessor_ip, self.port))
                    self.send_message(s, {
                        "type": "update_finger_table",
                        "node_ip": self.ip_address,
                        "index": i,
                        "origin": self.ip_address
                    })
            except Exception as e:
                print(f"Error al actualizar finger table de {predecessor_ip}: {e}")

    def update_finger_table(self, node_ip, i, origin=None):
        """Actualiza la entrada i-ésima de la finger table si node_ip es relevante"""
        if origin is None:
            origin = self.ip_address
            
        print(f"Updating finger table {i} with {node_ip} from {origin}")
        
        start = (self.id + 2**(i-1)) % 2**self.m
        current_entry_ip = self.finger_table[i-1] if i-1 < len(self.finger_table) else None
        current_entry_id = self.hash_function(current_entry_ip, self.m) if current_entry_ip else None
        node_id = self.hash_function(node_ip, self.m)

        if current_entry_id is None or self._is_between(node_id, start, current_entry_id):
            self.finger_table[i-1] = node_ip
            # Notificar al predecesor para actualizar su finger table
            if self.predecessor and self.predecessor != self.ip_address and self.predecessor != origin:
                try:
                    print(f"Updating finger table of {self.predecessor}")
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((self.predecessor, self.port))
                        self.send_message(s, {
                            "type": "update_finger_table",
                            "node_ip": node_ip,
                            "index": i,
                            "origin": self.ip_address
                        })
                except Exception as e:
                    print(f"Error al actualizar finger table del predecesor: {e}")



    def dict(self):
        return {
            'ip': self.ip_address,
            'id': self.id,
            'successors': [s.id for s in self.successors],
            'predecessor': self.predecessor.id if self.predecessor else None
        }

    def __repr__(self):
        return f"Node({self.id}, {self.ip_address})"
    
    def send_message(self, s, message):
        """
        Sends a message to a socket.

        Args:
            s (socket.socket): The socket to send the message to.
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
        
        print(f"Message sent: {message}")
        s.sendall(header + message)
        
        header = s.recv(4)
        data_len = struct.unpack("!I", header)[0]
        
        data = s.recv(data_len)
        print(f"Message received: {data}")
        return json.loads(data.decode())
    def hash_function(self, key, m):
        # Hash SHA-1 truncado a m bits (ej: m=6 → 0-63)
        hash_bytes = hashlib.sha1(key.encode()).digest()
        hash_int = int.from_bytes(hash_bytes, byteorder='big')
        return hash_int % (2**m)

    
class Tracker(Node):
    def __init__(self, ip_address= None, m=5):
        ip_address = self.get_ip()
        super().__init__(ip_address, m)
    
    # TRACKER_DIRECTORY = "src/tracker/database"  make dinamic
    TRACKER_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
    TRACKER_FILE_NAME = "tracker_data.json"

    def create_initial_tracker(self):
        """
        Creates an initial empty tracker data structure and saves it as a JSON
        file in the specified directory.
        received
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
    
    def get_ip(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

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
        # !Volver a poner el try
        # try:
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
                    response = {"successor": successor}
                    response_j = json.dumps(response).encode()
                    header = struct.pack("!I", len(response_j))

                    print(f"Sending response: {response}")
                    message = header + response_j
                    client_socket.sendall(message)
                
                elif message["type"] == "find_predecessor":
                    key_id = message["data"]
                    predecessor = self.find_predecessor(key_id)
                    response = {"predecessor": predecessor}
                    response_j = json.dumps(response).encode()
                    
                    header = struct.pack("!I", len(response_j))

                    print(f"Sending response: {response}")
                    message = header + response_j
                    client_socket.sendall(message)
                    
                elif message["type"] == "notify":
                    node_ip = message["data"]
                    self.notify(node_ip)
                    response = {"status": "ok"}
                    
                    print(f"Sending response: {response}")
                    response_j = json.dumps(response).encode()
                    header = struct.pack("!I", len(response_j))
                    
                    client_socket.sendall(header + response_j)
                    
                elif message["type"] == "get_predecessor":
                    response = {"predecessor": self.predecessor}
                    print(f"Sending response: {response}")
                    
                    response_j = json.dumps(response).encode()
                    header = struct.pack("!I", len(response_j))
                    client_socket.sendall(header + response_j)

                elif message["type"] == "get_successors":
                    response = {"successors": self.successors}
                    print(f"Sending response: {response}")
                    
                    response_j = json.dumps(response).encode()
                    header = struct.pack("!I", len(response_j))
                    client_socket.sendall(header + response_j)

                elif message["type"] == "update_finger_table":
                    node_ip = message["node_ip"]
                    i = message["index"]
                    origin = message.get("origin", None)
                    self.update_finger_table(node_ip, i, origin=str(origin))
                    response = {"status": "ok"}
                    
                    response_j = json.dumps(response).encode()
                    header = struct.pack("!I", len(response_j))
                    client_socket.sendall(header + response_j)
                    print(f"Sending response: {response}")
                    
                else:
                    print("Invalid message type.")
                    client_socket.sendall(b"Invalid message type.")
        # except Exception as e:
        #     print(f"Error processing client request: {e}")
        # finally:
        #     print("Closing connection with: ", client_socket.getpeername())
        #     client_socket.close()

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
                    user_input = input()
                    inputs = user_input.split()
                    
                    if user_input.strip().lower() == "q":  # Exit on 'q'
                        print("Exiting tracker server...")
                        self.server_socket.close()
                        return
                    
                    if user_input.strip().lower() == "print_table":
                        print(f"Finger table of the node with id {self.id}:")
                        for i, node in enumerate(self.finger_table):
                            print(f"{i+1}: {node}")
                    
                    if user_input.strip().lower() == "print_predecessor":
                        print(f"Predecessor: {self.predecessor}")
                        
                    if user_input.strip().lower() == "print_successors":
                        print(f"Successors: {self.successors}")
                        
                    if inputs[0].strip().lower() == "join":
                        if len(inputs) > 1:
                            existing_node_ip = inputs[1]
                            self.join(existing_node_ip)
                        else:
                            self.join()
                        
                    if user_input.strip().lower() == "help":
                        print("Commands:")
                        print("q: Exit the tracker server.")
                        print("print_table: Print the finger table of the node.")
                        print("print_predecessor: Print the predecessor of the node.")
                        print("print_successors: Print the successors of the node.")

                if r is self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    print(f"Connection from {addr}")

                    try:
                        client_thread = threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True)
                        client_thread.start()
                    except Exception as e:
                        print(f"Error handling client {addr}: {e}")