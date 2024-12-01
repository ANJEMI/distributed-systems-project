import enum

BLOCK_SIZE = 2**14

class State(enum.Enum):
    """State of the block"""
    EMPTY = 0
    DOWNLOADING = 1
    DOWNLOADED = 2
    
class Block:
    def __init__(self, state=State.EMPTY, data= None, block_size=BLOCK_SIZE):
        self.state = state
        self.data = data
        self.block_size = block_size
    