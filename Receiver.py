'''
Receiver: Uses the receiving services of this TCP-like protocol to reconstruct the file.
Receives data on the listening_port, writes it to filename and sends ACKs to the remote host 
at sender_ip and sender_port.

Handles in network packet loss, packet corruption, packet duplication and packet 
reordering and copes with dynamic network delays.

@author: Emily Pakulski
'''

from sys import argv, stdout
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from TCP_Segment import TCP_Segment
from struct import Struct
import datetime

class Receiver:
    IP_ADDR = '127.0.0.1'
    BACKLOG = 1 # max number of concurrent connections

    # logs when you sent the packet
    def log_data(self, timestamp, sequence_no, ack_no, FIN):
        with open(self.logfile, "a") as logfile:
            logfile.write('Timestamp: ' + str(timestamp) + ', ' \
                          + 'Source: ' + str(self.IP_ADDR) + ':' + str(self.listening_port) + ', ' \
                          + 'Destination: ' + str(self.sender_ip) + ':' + str(self.sender_port) + ', ' \
                          + 'Sequence number: ' + str(sequence_no) + ', '  \
                          + 'ACK number: ' + str(ack_no) + ', ' \
                          + 'FIN: ' + str(FIN) + '\n')

    def send_recv_segments(self, ack_sock, file_sock_UDP):           
        with open(self.filename, 'wb') as output:
            
            # get first segment
            packed_segment = file_sock_UDP.recv(TCP_Segment.PACKET_SIZE)
            unpacked_segment = TCP_Segment.unpack_segment(packed_segment)
            
            print 'current FIN bit ' + str(unpacked_segment.FIN)

            next_expected_sequence_no = 0
            while (unpacked_segment.FIN == 0):
                print 'received a packet. '
                stdout.flush() 

                # check for corrupt packet: checksum

                # check if correct segment was sent
                #if (unpacked_segment.data == next_expected_sequence_no):
                # this is the correct packet

                next_expected_sequence_no += len(unpacked_segment.data)   
                output.write(unpacked_segment.data)
            
                print 'Received in-order packet: ' + str(unpacked_segment.sequence_no)
                stdout.flush()

                # ACK reception
                ack_sock.sendall(str(unpacked_segment.ACK_no))
                recv_time = datetime.datetime.now()
                #self.log_data(recv_time, unpacked_segment.sequence_no, unpacked_segment.ACK_no, unpacked_segment.FIN)
                
                packed_segment = file_sock_UDP.recv(TCP_Segment.PACKET_SIZE)
                unpacked_segment = TCP_Segment.unpack_segment(packed_segment)

            # write final segment with FIN == 1
            output.write(unpacked_segment.data)
            next_expected_sequence_no += len(unpacked_segment.data)
            
            print 'Total bytes read to ' + self.filename + ': ' + str(next_expected_sequence_no)

    def open_sockets(self):
    	print 'Opening TCP connection for sending ACKs on port ' + str(self.sender_port) + '...'
        ack_sock = socket(AF_INET, SOCK_STREAM) 
        ack_sock.connect((self.sender_ip, self.sender_port))
            
        file_sock_UDP = socket(AF_INET, SOCK_DGRAM)
        file_sock_UDP.bind((self.IP_ADDR, self.listening_port))
        print 'Receiver listening on port ' + str(self.listening_port) + '...\n'
        stdout.flush()

        return (ack_sock, file_sock_UDP)

    def __init__(self, argv):
        self.filename = argv[1]
        self.listening_port = int(argv[2]) 
        self.sender_ip = argv[3]
        self.sender_port = int(argv[4]) # ACKs port
        self.logfile = argv[5]
        
        ack_sock, file_sock = self.open_sockets()

        # need two separate sockets because one is TCP and one is UDP
        self.send_recv_segments(ack_sock, file_sock)
  
def main(argv):
    Receiver(argv)
    
main(argv)