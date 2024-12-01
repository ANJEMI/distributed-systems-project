from client.peer.block import Block, BLOCK_SIZE, State
import math
from typing import List
import hashlib

class Piece:
    def __init__(self, piece_index, piece_size, piece_hash):
        self.piece_index = piece_index
        self.piece_size = piece_size
        self.piece_hash = piece_hash
        self.is_downloaded = False
        self.raw_data: bytes = b""
        
        self.num_blocks: int = int(math.ceil(piece_size / BLOCK_SIZE))
        self.blocks: List[Block] = []
        
        self._init_blocks()
        
    def _init_blocks(self):
        for i in range(self.num_blocks):
            self.blocks.append(Block())
            
        if self.piece_size % BLOCK_SIZE != 0:
            self.blocks[-1].block_size = self.piece_size % BLOCK_SIZE
        
        if self.num_blocks == 1:
            self.blocks[0].block_size = self.piece_size
        
        
    # def get_block(self, block_index: int) -> Block:
    #     return self.blocks[block_index]
    
    # def get_block_raw_data(self, block_offset: int, block_length: int) -> bytes:
    #     return self.raw_data[block_offset:block_offset + block_length]
    
    def set_block(self, offset: int, data: bytes):
        block_index = offset // BLOCK_SIZE
        
        if not self.is_downloaded and not self.blocks[block_index].state == State.DOWNLOADED:
            self.blocks[block_index].data = data
            self.blocks[block_index].state = State.DOWNLOADED
    
    def get_empty_block(self):
        if self.is_downloaded:
            return None
        
        for index, block in enumerate(self.blocks):
            if block.state == State.EMPTY:
                return self.piece_index, index, block
            
        return None
    
    def is_complete(self) -> bool:
        return all([block.state == State.DOWNLOADED for block in self.blocks])
    
    def _merge_blocks(self) -> bytes:
        return b"".join([block.data for block in self.blocks])
    
    def _validate_piece(self) -> bool:
        hash_piece = hashlib.sha1(self.raw_data).digest()
        
        if hash_piece == self.piece_hash:
            return True
        
        print(f"Piece {self.piece_index} is corrupted")
        return False
    
    def set_total_data(self):
        data = self._merge_blocks()
        
        if not self._validate_piece():
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
        
        f.seek(self.piece_index * self.piece_size)
        f.write(self.raw_data)
        f.close()

        