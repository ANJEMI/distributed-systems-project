import socket
import struct
from client.messages import *
from typing import List, Optional

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
            self.socket.settimeout(5)
            print(f"log comenzo conexion con peer {self.id}")
            self.socket.connect((self.ip, self.port))
            print(f"log Connected to peer {self.id} at {self.ip}:{self.port}")
        except socket.timeout:
            raise TimeoutError(f"Connection to peer {self.id} timed out")
        except Exception as e:
            raise ConnectionError(f"Error connecting to peer {self.id}: {e}")
        
    def receive_message(self) -> Optional[bytes]:
        """
        Receive a message from the peer.
        """
        try:
            header = self.socket.recv(4)
            if not header:
                return None
            
            payload_len = struct.unpack(">I", header)[0]
            message = self.socket.recv(payload_len)
            return header + message
        except Exception as e:
            raise IOError(f"Error receiving message from peer {self.id}: {e}")
        
    def send_message(self, message):
        """
        Send a message to the peer.
        """
        try:
            self.socket.send(message)
            print(f"Message sent to peer {self.id}")
        except Exception as e:
            raise IOError(f"Error sending message to peer {self.id}: {e}")

    def request_piece(self, index: int, begin: int, length: int):
        """
        Request a piece from the peer.
        
        Response format: <len=0009+X><id=7><index><begin><block>
        """
        try:
            # Formato del mensaje request: <len=0013><id=6><index><begin><length>
            message = Request(index, begin, length).to_bytes()
            self.socket.send(message)
            
            response = self.receive_message()
            
            if not response:
                raise ConnectionError(f"Peer {self.id} closed the connection")
            
            piece_index, block_offset, block = Piece.from_bytes(response)
            
            if piece_index != index or block_offset != begin:
                raise IOError(f"Invalid piece received from peer {self.id}")
            
            return block
            
        except Exception as e:
            raise IOError(f"Error requesting piece {index} from peer {self.id}: {e}")
    


    def close(self):
        """
        Close the connection with the peer.
        """
        if self.socket:
            self.socket.close()
            print(f"Connection closed with peer {self.id}")
