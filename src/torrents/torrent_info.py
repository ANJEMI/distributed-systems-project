from dataclasses import dataclass
from typing import List

@dataclass
class TorrentInfo:
    announce: str
    info_hash: str
    name: str
    piece_length: int
    length: int
    pieces: str