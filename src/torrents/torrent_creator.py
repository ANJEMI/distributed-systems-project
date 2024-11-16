import os
import hashlib
from typing import List, Dict
import bencodepy

class TorrentCreator:
    def __init__(self, 
                tracker_url: str = "localhost", 
                piece_length: int = 256 * 1024):
        """
        Create a new torrent creator object
        
        :param tracker_url: The URL of the tracker
        :param piece_length: The length of each piece in bytes 
        """
        self.tracker_url = tracker_url
        self.piece_length = piece_length
        
    def generate_pieces(self, file_path: str) -> List[bytes]:
        """
        Generate the pieces of the torrent file
        
        :param file_path: The path to the file to generate the pieces for
        :return pieces: A list of pieces
        """
        pieces = []
        
        with open(file_path, "rb") as f:
            while True:
                piece = f.read(self.piece_length)
                if not piece:
                    break
                pieces.append(piece)
        
        return pieces
    
    def encode_pieces(self, pieces) -> bytes:
        """
        Encode the pieces into a single string
        
        :param pieces: A list of pieces
        :return encoded_pieces: A single string of encoded pieces
        """
        encoded_pieces = b""
        for piece in pieces:
            encoded_pieces += hashlib.sha256(piece).digest()
        
        return encoded_pieces
    
    def create_torrent(self, file_path: str) -> str:
        """
        Create a torrent file
        
        :param file_path: The path to the file to create the torrent for
        :return output_path: The path to the created torrent file
        """
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        output_path = os.path.join(os.path.dirname(file_path), os.path.splitext(file_name)[0] + ".torrent")
        
        pieces = self.generate_pieces(file_path)
        encoded_pieces = self.encode_pieces(pieces)
        
        torrent_data = {
            "announce": self.tracker_url,
            "info": {
                "name": file_name,
                "piece length": self.piece_length,
                "length": file_size,
                "pieces": encoded_pieces
            }
        }
    
        with open(output_path, "wb") as f:
            f.write(bencodepy.encode(torrent_data))
        
        return output_path
