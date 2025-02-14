from client.peer.block import Block, BLOCK_SIZE, State
import math
from typing import List
import hashlib

class Piece:
    def __init__(self, piece_index, piece_size, piece_hash, piece_torrent_size=None):
        self.piece_index = piece_index
        self.piece_size = piece_size
        self.piece_hash = piece_hash
        self.is_downloaded = False
        self.raw_data: bytes = b""
        
        # For the last piece
        self.piece_torrent_size = piece_torrent_size
        
        self.num_blocks: int = int(math.ceil(piece_size / BLOCK_SIZE))
        self.blocks: List[Block] = []
        
        self._init_blocks()
        
    def _init_blocks(self):
        for i in range(self.num_blocks):
            block_size = BLOCK_SIZE
            if i == self.num_blocks - 1:
                block_size = self.piece_size % BLOCK_SIZE
                if block_size == 0:
                    block_size = BLOCK_SIZE
                    
            self.blocks.append(Block(block_size=block_size))
        
        if self.num_blocks == 1:
            self.blocks[0].block_size = self.piece_size
            
    def set_block(self, block_index: int, data: bytes):
        # block_index = offset // BLOCK_SIZE
        if block_index >= len(self.blocks): 
            raise ValueError(f"Block index {block_index} out of range")
        # if len(data) > block.block_size:
        #     data = data[:block.block_size]

        
        if not self.is_downloaded and not self.blocks[block_index].state == State.DOWNLOADED:
            print(f"Setting block {block_index} with size {len(data)}, piece {self.piece_index}")
            self.blocks[block_index].data = data
            self.blocks[block_index].state = State.DOWNLOADED
                
    def is_complete(self) -> bool:
        return all([block.state == State.DOWNLOADED for block in self.blocks])
    
    def _merge_blocks(self) -> bytes:
        return b"".join([block.data for block in self.blocks])
    
    def _validate_piece(self, data) -> bool:
        hash_piece = hashlib.sha1(data).digest().hex()
        
        if hash_piece == self.piece_hash:
            print(f"Integrity check passed for piece {self.piece_index}")
            return True 
        
        print(f"Expected hash: {self.piece_hash}")
        print(f"Calculated hash: {hash_piece}")
        
        return False
    
    def set_total_data(self):
        data = self._merge_blocks()
        
        if not self._validate_piece(data):
            return False
        
        self.is_downloaded = True
        self.raw_data = data
        
        return True
        
    def save_piece(self, path):
        try:
            f = open(path, "r+b")
        except IOError:
            f = open(path, "wb")
        except Exception as e:
            print(f"Error saving piece {self.piece_index}: {e}")
            return False
        
        offset = self.piece_index * self.piece_torrent_size
        
        f.seek(offset)
            
        f.write(self.raw_data[:self.piece_size])
        f.close()

