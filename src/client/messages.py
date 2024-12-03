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
    def from_bytes(self, message):
        raise NotImplementedError()
    
class Handshake(Message):
    """ Handshake message
    <pstrlen><pstr><reserved><info_hash><peer_id>
    
    pstrlen: string length of <pstr>, as a single raw byte  (19 in version 1)
    pstr: string identifier of the protocol          (b"BitTorrent protocol")
    reserved: eight (8) reserved bytes. 
    info_hash: 20-byte SHA1 hash of the info key in the metainfo file.
    peer_id: 20-byte string used as a unique ID for the client.
    
 
    """
    LENGTH = 68
    
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
    
    def to_bytes(self):
        return pack(">I", 0)
    
    @classmethod
    def from_bytes(self, message):
        payload_len = unpack(">I", message[:4])[0]
        
        if payload_len != 0:
            raise WrongMessageException("Not a KeepAlive Message")
        
        return self()
    
class MessageNoPayload(Message):
    """ 
    Message with no payload
        <len=0001><id=n>
        n=0 choke
        n=1 unchoke
        n=2 interested
        n=3 not interested
    """
    def __init__(self, message_id):
        super().__init__()

        self.message_id = message_id
        
    def to_bytes(self):
        return pack(">IB", 1, self.message_id)

    @classmethod
    def from_bytes(self, message):
        payload_len, message_id = unpack(">IB", message[:5])
        
        if payload_len != 1:
            raise WrongMessageException("Invalid MessageNoPayload length")
        
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
    """ HAVE message
    <length=5><message_id=4><piece_index>
    """

    def __init__(self, piece_index):
        super().__init__()
        
        self.piece_index = piece_index
    
    def to_bytes(self):
        return pack(">IBI", 5, 4, self.piece_index)
    
    def from_bytes(self,message):
        length, message_id, piece_index = unpack(">IBI", message[:9])
        
        if length != 5 or message_id != 4:
            raise WrongMessageException("Invalid Have message")
        
        return self(piece_index)

class BitField(Message):
    """ BitField message
    <length><message_id=5><bitfield>
    """
    
    def __init__(self, bitfield):
        super().__init__()
        self.bitfield = bitfield
    
    def to_bytes(self):
        bitfield_bytes = self.bitfield
        length = 1 + len(bitfield_bytes)
        return pack(">IB", length, 5) + bitfield_bytes
    
    @classmethod
    def from_bytes(self, message):
        length, message_id = unpack(">IB", message[:5])
        if message_id != 5:
            raise WrongMessageException("Invalid BitField message")
        bitfield = message[5:length + 4]
        return self(bitfield)
    
class Request(Message):
    """ Request message
    <length=13><message_id=6><piece_index><block_offset><block_length>
    """
    def __init__(self, piece_index, block_offset, block_length):
        super().__init__()
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length
    
    def to_bytes(self):
        return pack(">IBIII", 13, 6, self.piece_index, self.block_offset, self.block_length)
    
    @classmethod
    def from_bytes(self, message):
        length, message_id, piece_index, block_offset, block_length = unpack(">IBIII", message[:17])
        if length != 13 or message_id != 6:
            raise WrongMessageException("Invalid Request message")
        return self(piece_index, block_offset, block_length)


# ---

class Piece(Message):
    """
    PIECE = <length><message_id=7><piece_index><block_offset><block>
        - length = 9 + block length (4 bytes)
        - piece_index = zero-based piece index (4 bytes)
        - block_offset = zero-based of the requested block (4 bytes)
        - block = block as a bytestring or bytearray (block_length bytes)
    """
    def __init__(self, piece_index, block_offset, block):
        super().__init__()
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block = block
        self.block_length = len(block)

    def to_bytes(self):
        payload_len = 9 + self.block_length
        
        return pack(f">IBII{self.block_length}s",
                    payload_len,
                    7,  # message_id
                    self.piece_index,
                    self.block_offset,
                    self.block)

    @classmethod
    def from_bytes(self, message):
        payload_len, message_id = unpack(">IB", message[:5])
        block_length = payload_len - 9
        piece_index, block_offset, block = unpack(f">II{block_length}s", message[5:13 + block_length])
        
        if message_id != 7:
            raise WrongMessageException("Not a Piece message")
        
        return self(piece_index, block_offset, block)


class Cancel(Message):
    """
    CANCEL = <length=13><message_id=8><piece_index><block_offset><block_length>
        - piece_index = zero-based piece index (4 bytes)
        - block_offset = zero-based of the requested block (4 bytes)
        - block_length = length of the requested block (4 bytes)
    """
    def __init__(self, piece_index, block_offset, block_length):
        super().__init__()
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length

    def to_bytes(self):
        return pack(">IBIII",
                    13,  # payload_len
                    8,   # message_id
                    self.piece_index,
                    self.block_offset,
                    self.block_length)

    @classmethod
    def from_bytes(self, message):
        payload_len, message_id, piece_index, block_offset, block_length = unpack(">IBIII", message[:17])
        
        if payload_len != 13 or message_id != 8:
            raise WrongMessageException("Not a Cancel message")
        
        return self(piece_index, block_offset, block_length)


class Port(Message):
    """
    PORT = <length=5><message_id=9><port_number>
        - port_number = listen_port (4 bytes)
    """
    def __init__(self, listen_port):
        super().__init__()
        self.listen_port = listen_port

    def to_bytes(self):
        return pack(">IBI",
                    5,  # payload_len 
                    9,  # message_id
                    self.listen_port)

    @classmethod
    def from_bytes(self, message):
        payload_len, message_id, listen_port = unpack(">IBI", message[:9])
        if payload_len != 5 or message_id != 9:
            raise WrongMessageException("Not a Port message")
        return self(listen_port)
