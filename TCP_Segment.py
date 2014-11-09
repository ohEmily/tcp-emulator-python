'''
TCP segment class. Packs data into TCP header and data fields.
Left out certain fields such as receive window as this model does not require them.
Based on page 234 of Kurose and Ross.
@author: Emily Pakulski
'''

import struct
import sys
from sys import stdout

class TCP_Segment:
    HEADER_SIZE = 20
    MSS = 556 # maximum segment size; the max of the data
    # format: source_port == 2 bytes, dest_port == 2 bytes, 
    # seq_no == 4 bytes, ack_no == 4 bytes, header_len == 2 bytes, 
    # FIN == 1 byte, ACK == 1 byte, checksum == 2 bytes and data
    HEADER_FORMAT = 'H H I I H 2s b b 2s ' + str(MSS) + 's'
    PACKET_SIZE = HEADER_SIZE + MSS # should be 576
    
    # constructor for an unpacked TCP_segment
    def __init__(self, source_port, dest_port, sequence_no, ack_no, FIN, data):
        self.source_port = source_port
        self.dest_port = dest_port
        self.sequence_no = sequence_no
        self.ACK_no = ack_no
        # header len is set to constnat
        self.ACK = 1
        self.FIN = FIN
        self.data = data
    
    # fits fields into segment of the right size for sending
    def pack_segment(self):
        checksum = self.checksum_function()
        return struct.pack(self.HEADER_FORMAT, 
                        self.source_port, self.dest_port, 
                        self.sequence_no, self.ACK_no, 
                        self.HEADER_SIZE, self.ACK, self.FIN,  
                        str(checksum), str(self.data))
    
    # instantiates a TCP_Segment with the passed in string form of a packed 
    # segment.
    @classmethod
    def unpack_segment(self, packed_segment):
        (self.source_port, self.dest_port, self.sequence_no, 
            self.ACK_no, header_size, self.ACK, self.FIN, self.checksum, 
            self.data) = struct.unpack(TCP_Segment.HEADER_FORMAT, packed_segment)
        return self

    def checksum_function(self):
        return 0
