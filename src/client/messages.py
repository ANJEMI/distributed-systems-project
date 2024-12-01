from struct import pack, unpack


class WrongMessageException(Exception):
    pass

class Message:
    """ 
    Base class for all messages exchanged between peers.
    Peers communicate via an exchange of length-prefixed messages. The length-prefix is an integer.
    
    All messages have the following format:
        <length prefix><message ID><payload> 
    
    Except for the handshake message.
    
    """
    def to_bytes(self):
        raise NotImplementedError()
    
    @classmethod
    def from_bytes(cls, message):
        raise NotImplementedError()
    
class Handshake(Message):
    """ Handshake message
    <pstrlen><pstr><reserved><info_hash><peer_id>
    
    pstrlen: string length of <pstr>, as a single raw byte  (19 in version 1)
    pstr: string identifier of the protocol          (b"BitTorrent protocol")
    reserved: eight (8) reserved bytes. 
    info_hash: 20-byte SHA1 hash of the info key in the metainfo file.
    peer_id: 20-byte string used as a unique ID for the client.
    
    Length: =  68 bytes
 
    """
    def __init__(self, info_hash, peer_id, pstr=b"BitTorrent protocol", pstrlen=19):
        super().__init__()
        
        assert len(info_hash) == 20

        self.info_hash = info_hash
        self.peer_id = peer_id
        self.pstr = pstr
        self.pstrlen = pstrlen
        self.reserved = b"\x00" * 8
        
    def to_bytes(self):
        return pack(">B{}s8s20s20s".format(self.pstrlen), self.pstrlen, self.pstr, self.reserved, self.info_hash, self.peer_id)
    
    @classmethod
    def from_bytes(self, message):
        pstrlen = unpack(">B", message[:1])[0]
        pstr, _ , info_hash, peer_id = unpack(">{}s8s20s20s".format(pstrlen), message[1:])
        
        if pstr != b"BitTorrent protocol":
            raise ValueError("Invalid protocol string")
        
        return self(info_hash, peer_id)
    
class KeepAlive(Message):
    """ Keep alive message
    <len=0000>
    
    Length: =  4 bytes
    
    """
    
    def __init__(self):
        super().__init__()
        
        self.payload_len = 0
        self.length = 4
    
    def to_bytes(self):
        return pack(">I", self.payload_len)
    
    @classmethod
    def from_bytes(self, message):
        payload_len = unpack(">I", message[:self.length])
        
        if payload_len != self.payload_len:
            raise WrongMessageException("Not a KeepAlive Message")
        
        return self()
    
class MessageNoPayload(Message):
    """ 
        <len=0001><id=n>
        n=0 choke
        n=1 unchoke
        n=2 interested
        n=3 not interested
    """
    def __init__(self, message_id):
        super().__init__()
        
        self.payload_len = 1
        self.length = 5
        self.message_id = message_id
        
    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(self, message):
        payload_len, message_id = unpack(">IB", message[:self.total_length])
        
        if message_id != self.message_id:
            raise WrongMessageException("Incorrect message id")
        
        return self(message_id)
  
class Choke(MessageNoPayload):
    def __init__(self):
        super().__init__(0)
    
class Unchoke(MessageNoPayload):
    def __init__(self):
        super().__init__(1)
        
class Interested(MessageNoPayload):
    def __init__(self):
        super().__init__(2)
        
class NotInterested(MessageNoPayload):
    def __init__(self):
        super().__init__(3)

class Have(Message):
    """ HAVE 
    <length><message_id><piece_index>
    length = 5 (4 bytes)
    message_id = 4 (1 byte)
    piece_index = zero based index of the piece (4 bytes) 
    """

    def __init__(self, piece_index):
        super().__init__()
        
        self.piece_index = piece_index
        self.payload_len = 5
        self.message_id = 4
        self.length = 4 + self.payload_len
    
    def to_bytes(self):
        return super().to_bytes()
    
    def from_bytes():
        pass

class BitField(Message):
    """ BitField
    <length><message_id><bitfield>
    
    payload_len = 1 + bitfield_size (4 bytes)
    message id = 5 (1 byte)
    bitfield = bitfield representing downloaded pieces (bitfield_size bytes)
    """
    
    def __init__(self, bitfield):
        super().__init__()
        
        self.bitfield = bitfield
        self.bitfield_bytes = bitfield.tobytes()
        self.bitfield_length = len(self.bitfield_bytes)
        
        self.payload_len = 1 + self.bitfield_length
        self.length = 4 + self.payload_length

    def to_bytes(self):
        return super().to_bytes()
    
    def from_bytes(self):
        pass
    
class Request(Message):
    """ Request
    <length><message_id><piece_index><block_offset><block_length>
    payload_len = 13 (4 bytes)
    message_id = 6 (1 byte)
    piece_index = zero based piece index (4 bytes)
    block_offset = zero based of the requested block (4 bytes)
    block_length = length of the requested block (4 bytes)
    """
    
    def __init__(self, piece_index, block_offset, block_length):
        super().__init__()
        
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length
        
        self.payload_len = 13
        self.lenth = 4 + self.payload_len
        
    def to_bytes(self):
        return super().to_bytes()
    
    def from_bytes(self):
        pass
    