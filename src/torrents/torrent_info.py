from dataclasses import dataclass
from typing import List

@dataclass
class TorrentInfo:
    announce: str
    name: str
    piece_length: int
    length: int
    pieces: str