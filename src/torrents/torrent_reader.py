from typing import Dict, List
import bencodepy
from torrents.torrent_info import TorrentInfo
import hashlib

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
        
        return TorrentInfo(
            announce=torrent_data.get(b"announce", b"").decode("utf-8"),
            info_hash=info.get(b"info_hash", b"").hex(),
            name=info.get(b"name", b"").decode("utf-8"),
            piece_length=info.get(b"piece length", 0),
            length=info.get(b"length", 0),
            pieces=info.get(b"pieces", b"").hex()
        )