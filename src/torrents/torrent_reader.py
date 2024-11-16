from typing import Dict, List
import bencodepy

class TorrentReader:
    @staticmethod
    def read_torrent(file_path: str) -> Dict:
        """ 
        Read a torrent file and return the decoded data
        
        :param file_path: The path to the torrent file
        :return torrent_data: The decoded torrent data
        """
        
        with open(file_path, "rb") as f:
            torrent_data = bencodepy.decode(f.read())
        return torrent_data

    @staticmethod
    def extract_info(torrent_data: Dict) -> Dict:
        """
        Extract the info from the torrent data
        
        :param torrent_data: The decoded torrent data
        :return info: The info from the torrent data 
        """
        
        info = torrent_data.get(b"info", {})
        return {
            "announce": torrent_data.get(b"announce", b"").decode("utf-8"),
            "name": info.get(b"name", b"").decode("utf-8"),
            "pieceLength": info.get(b"piece length", 0),
            "length": info.get(b"length", 0),
            "numberPieces": len(info.get(b"pieces", b"")) // 32,  # Cada hash SHA-256 es de 32 bytes
        }
    
    @staticmethod
    def extract_pieces(torrent_data: Dict) -> List:
        """
        Extract the pieces from the torrent data
        
        :param torrent_data: The decoded torrent data
        :return pieces: The pieces from the torrent data 
        """
        
        info = torrent_data.get(b"info", {})
        pieces = info.get(b"pieces", b"")
        return [pieces[i:i+32].hex() for i in range(0, len(pieces), 32)]
      