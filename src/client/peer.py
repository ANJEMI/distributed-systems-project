import socket
import struct
from typing import List

class Peer:
    def __init__(self, peer_id, ip, port):
        self.peer_id = peer_id
        self.ip = ip
        self.port = port
        self.socket = None

    def connect(self):
        """
        Connect to the peer using the IP and port.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.port))
            print(f"Connected to peer {self.peer_id} at {self.ip}:{self.port}")
        except Exception as e:
            raise ConnectionError(f"Error connecting to peer {self.peer_id}: {e}")

    def request_piece(self, index: int, begin: int, length: int):
        """
        Request a piece from the peer.
        """
        try:
            # Formato del mensaje request: <len=0013><id=6><index><begin><length>
            message = struct.pack(">IbIII", 13, 6, index, begin, length)
            self.socket.send(message)
            print(f"Requested piece {index} (offset: {begin}, length: {length})")
        except Exception as e:
            raise IOError(f"Error requesting piece {index} from peer {self.peer_id}: {e}")
    
    def receive_piece(self, length: int) -> bytes:
        """
        Receive a piece from the peer.
        """
        try:
            data = b""
            while len(data) < length:
                chunk = self.socket.recv(length - len(data))
                if not chunk:
                    raise IOError("Connection closed by peer.")
                data += chunk
            return data
        except Exception as e:
            raise IOError(f"Error receiving piece from peer {self.peer_id}: {e}")

    def close(self):
        """
        Close the connection with the peer.
        """
        if self.socket:
            self.socket.close()
            print(f"Connection closed with peer {self.peer_id}")
