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
    # HEADER_FORMAT explanation: source_port == 2 bytes, dest_port == 2 bytes, 
    # seq_no == 4 bytes, ack_no == 4 bytes, header_len == 2 bytes, FIN == 1 byte, 
    # ACK == 1 byte, checksum == 2 bytes and data
    HEADER_FORMAT = 'H H I I H b b 2s ' + str(MSS) + 's'
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
        checksum = TCP_Segment.checksum_function(self)

        # format data correctly
        data_padding = self.MSS - len(self.data)
        self.data += ' ' * data_padding

        return struct.pack(self.HEADER_FORMAT, 
                        self.source_port, self.dest_port, 
                        self.sequence_no, self.ACK_no, 
                        self.HEADER_SIZE, self.FIN, self.ACK,
                        str(checksum), str(self.data))
    

    # instantiates a TCP_Segment with the passed in string form of a packed 
    # segment.
    @classmethod
    def unpack_segment(self, packed_segment):
        (self.source_port, self.dest_port, self.sequence_no, 
            self.ACK_no, header_size, self.FIN, self.ACK, self.checksum, 
            self.data) = struct.unpack(TCP_Segment.HEADER_FORMAT, packed_segment)
        return self


    # returns true if checksum is good, false if bad
    @staticmethod
    def is_corrupted(instance):
        return (instance.checksum == TCP_Segment.checksum_function(instance))


    # uses header values (except checksum) and data to calculate checksum.
    #
    # based loosely on the UDP checksum described in the textbook:
    # "UDP at the sender side performs the 1s complement of the sum of all 
    # the 16-bit words in the segment, with any overflow encountered during
    # the sum being wrapped around." (pg. 202)
    #
    @staticmethod
    def checksum_function(instance):
        # instead of concat 16-bit words, we use data that is a multiple of 16
        # (i.e. 576, the whole segment)
        all_text = str(instance.source_port) + str(instance.dest_port) + str(instance.sequence_no) \
            + str(instance.ACK_no) + str(instance.HEADER_SIZE) + str(instance.FIN) + str(instance.ACK) \
            + instance.data

        sum = 0
        for i in range((0), len(all_text) - 1, 2):
            # get unicode/byte values of operands
            first_operand = ord(all_text[i])
            second_operand = ord(all_text[i+1]) << 8

            # add
            current_sum = first_operand + second_operand
            
            # add and wrap around
            sum = ((sum + current_sum) & 0xffff) + ((sum + current_sum) >> 16)

        return sum
