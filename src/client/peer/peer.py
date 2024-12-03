import socket
import struct
from client.messages import *
from typing import List

class Peer:
    def __init__(self, peer_id, ip, port):
        self.id = peer_id
        self.ip = ip
        self.port = port
        self.socket = None

    def connect(self):
        """
        Connect to the peer using the IP and port.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"log comenzo conexion con peer {self.id}")
            self.socket.connect((self.ip, self.port))
            print(f"log Connected to peer {self.id} at {self.ip}:{self.port}")
        except Exception as e:
            raise ConnectionError(f"Error connecting to peer {self.id}: {e}")

    def request_piece(self, index: int, begin: int, length: int):
        """
        Request a piece from the peer.
        
        Response format: <len=0009+X><id=7><index><begin><block>
        """
        try:
            # Formato del mensaje request: <len=0013><id=6><index><begin><length>
            message = struct.pack(">IbIII", 13, 6, index, begin, length)
            self.socket.send(message)
            print(f"Requested piece {index} (offset: {begin}, length: {length})")
        except Exception as e:
            raise IOError(f"Error requesting piece {index} from peer {self.id}: {e}")
    
    def receive_piece(self, length: int) -> bytes:
        """
        Receive a piece from the peer.
        
        Response format: <len=0009+X><id=7><index><begin><block>
        """
        try:
            data = self.socket.recv(length)
            _, message_id, index, begin = struct.unpack(">IbII", data[:13])
            print(f"Received piece {index} (offset: {begin}, length: {length - 9})")
            return data[13:]
        except Exception as e:
            raise IOError(f"Error receiving piece from peer {self.id}: {e}")

    def close(self):
        """
        Close the connection with the peer.
        """
        if self.socket:
            self.socket.close()
            print(f"Connection closed with peer {self.id}")
