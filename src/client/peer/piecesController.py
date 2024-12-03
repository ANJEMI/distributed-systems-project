import math
import os
from typing import List

from client.peer.block import Block, BLOCK_SIZE, State
from client.peer.piece import Piece
from torrents.torrent_info import TorrentInfo

class PieceController:
    def __init__(self, torrent: TorrentInfo, path: str):
        self.torrent = torrent
        self.pieces: List[Piece] = []
        self.number_of_pieces = math.ceil(torrent.length / torrent.piece_length)
        self.bitfield = [False] * self.number_of_pieces
        self.output_path = path
        
        self._generate_pieces()
        
    def _generate_pieces(self):
        for i in range(self.number_of_pieces):
            start = i * 20
            end = start + 20
            
            if i == self.number_of_pieces - 1:
                piece_size = self.torrent.length % self.torrent.piece_length
                self.pieces.append(Piece(i, piece_size, self.torrent.pieces[start:end]))
                
            else:
                self.pieces.append(Piece(i, self.torrent.piece_length, self.torrent.pieces[start:end]))
                
        return self.pieces
    
    def is_complete(self) -> bool:
        return all([piece.is_downloaded for piece in self.pieces])
    
    def receive_block(self, piece_index: int, block_offset: int, data: bytes):
        self.pieces[piece_index].set_block(block_offset, data)
        
        if self.pieces[piece_index].is_complete():
            self._write_piece(piece_index)
