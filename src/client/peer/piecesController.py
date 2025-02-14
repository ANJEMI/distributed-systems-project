import math
import os
from typing import List
from threading import Lock

from client.peer.block import Block, BLOCK_SIZE, State
from client.peer.piece import Piece
from torrents.torrent_info import TorrentInfo

class PieceController:
    def __init__(self, torrent: TorrentInfo, path: str):
        self.torrent = torrent
        self.pieces: List[Piece] = []
        self.number_of_pieces = int(math.ceil(torrent.length / torrent.piece_length))
        self.bitfield = [False] * self.number_of_pieces
        self.output_path = path
        self.lock = Lock()
        
        self._generate_pieces()
        
    def _generate_pieces(self):
        
        for i in range(self.number_of_pieces):
            start = i * 40
            end = start + 40
            
            if i == self.number_of_pieces - 1:
                piece_size = self.torrent.length - (self.torrent.piece_length * i)
                self.pieces.append(Piece(i, piece_size, self.torrent.pieces[start:], self.torrent.piece_length))
                
            else:
                self.pieces.append(Piece(i, self.torrent.piece_length, self.torrent.pieces[start:end], self.torrent.piece_length))
                
        return self.pieces
    
    def is_complete(self) -> bool:
        return all([piece.is_downloaded for piece in self.pieces])
    
    def receive_block(self, piece_index: int, block_index: int, data: bytes):
        with self.lock:
            self.pieces[piece_index].set_block(block_index, data)

            if self.pieces[piece_index].is_complete():
                self.pieces[piece_index].is_downloaded = True
            
    def get_empty_block(self, piece_index):
        with self.lock:
            for i, block in enumerate(self.pieces[piece_index].blocks):
                if block.state == State.EMPTY:
                    # block.state = State.DOWNLOADING
                    return piece_index, i, block
        return None
    