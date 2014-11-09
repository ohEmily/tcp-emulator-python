'''
Sender: Reads data from a file and uses the sending services of the TCP-like 
protocol to deliver it to the remote host.

Handles in network packet loss, packet corruption, packet duplication and packet 
reordering and copes with dynamic network delays.

@author: Emily Pakulski
'''

from sys import argv, stdout
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, timeout
from threading import Timer, current_thread
from TCP_Segment import TCP_Segment
import datetime
import time

class Sender:
	IP_ADDR = '127.0.0.1'
	ACK_BUFF = 16 # integer
	BACKLOG = 1 # max number of concurrent connections
	INITIAL_TIMEOUT = 1
	
	# constants concerning RTT
	INITIAL_RTT = 1
	RTT_ALPHA = 0.125
	RTT_BETA = 0.25 

	def log(self, text):
		with open(self.logfile, "a") as logfile:
			logfile.write(text)
	
	# logs when you sent the packet
	def log_data(self, timestamp, sequence_no, ack_no, FIN):
		self.log('Timestamp: ' + str(timestamp) + ', ' \
						  + 'Source: ' + str(self.IP_ADDR) + ':' + str(self.ack_port_num) + ', ' \
						  + 'Destination: ' + str(self.remote_ip) + ':' + str(self.remote_port) + ', ' \
						  + 'Sequence number: ' + str(sequence_no) + ', '  \
						  + 'ACK number: ' + str(ack_no) + ', ' \
						  + 'FIN: ' + str(FIN) + '\n')
	
	# calls all the relevant RTT functions to update things
	def update_RTT_vars(self, sample_RTT):
		self.update_deviation_RTT(sample_RTT)
		self.update_estimated_RTT(sample_RTT)
	
	# tracks how long packet transmission should take
	def update_estimated_RTT(self, sample_RTT):
		# first packet transmitted
		if (self.estimated_RTT == self.INITIAL_RTT):
			self.estimated_RTT = sample_RTT
		else: # formula on page 239 
			self.estimated_RTT = (1 - self.RTT_ALPHA) * self.estimated_RTT \
				+ self.RTT_ALPHA * sample_RTT
	
	# tracks the variability of RTT
	def update_deviation_RTT(self, sample_RTT):
		self.deviation_RTT = (1 - self.RTT_BETA) * self.deviation_RTT + \
			self.RTT_BETA * abs(sample_RTT - self.estimated_RTT)

	def send_and_receive(self, unpacked_segment, ack_sock, file_sock):
		packed_segment = unpacked_segment.pack_segment()
		
		print 'sending packet number ' + str(self.segment_count) \
			+ ' with fin bit ' + str(unpacked_segment.FIN)
	
		file_sock.sendto(packed_segment, (self.remote_ip, self.remote_port))

		# try to send; if timeout, retransmit
		try:
			ack_sock.settimeout(self.INITIAL_TIMEOUT)
			ack_sock.recv(self.ACK_BUFF)
		except timeout:
			self.send_and_receive(unpacked_segment, ack_sock, file_sock)

		# check if out-of-order: if the wrong segment was ACK'd, retransmit

	# create TCP-segments with all fields filled in.
	def read_file(self):
		self.file_send_buffer = []
		
		with open(self.filename, "rb") as f:
			current_chunk = f.read(TCP_Segment.MSS)
			sequence_no = 0
			
			# create each TCP segment and append it to the array
			while current_chunk != '':
				sequence_no += len(current_chunk)
				previous_chunk = current_chunk
				current_chunk = f.read(TCP_Segment.MSS)
				expected_ACK = sequence_no + len(current_chunk)

				if (len(current_chunk) == 0): # is last segment -- FIN == 1
					current_segment = TCP_Segment(self.ack_port_num, \
											self.remote_port, sequence_no, \
											expected_ACK, 1, previous_chunk)
					self.file_send_buffer.append(current_segment)
				else: # is not last segment -- FIN == 0
					current_segment = TCP_Segment(self.ack_port_num, \
											self.remote_port, sequence_no, \
											expected_ACK, 0, previous_chunk)
					self.file_send_buffer.append(current_segment)
	
	def open_sockets(self):
		# open ACK-reception socket    
		print 'Listening on port ' + str(self.ack_port_num) + ' for ACKs...\n'   
		ack_sock = socket(AF_INET, SOCK_STREAM)
		ack_sock.bind((self.IP_ADDR, self.ack_port_num))
		ack_sock.listen(self.BACKLOG)
		ack_connection, ack_addr = ack_sock.accept()
		
		# open file transmission (sending) socket
		print 'Connecting to remote at ' + self.remote_ip + ':' + str(self.remote_port) + '...\n'
		stdout.flush()
		file_sock = socket(AF_INET, SOCK_DGRAM)
		file_sock.bind((self.IP_ADDR, self.ack_port_num))
		
		return (ack_connection, file_sock)
	
	# constructor
	def __init__(self, argv):
		self.filename = argv[1]
		self.remote_ip = argv[2]
		self.remote_port = int(argv[3])
		self.ack_port_num = int(argv[4])
		self.logfile = argv[5]
		if (argv[6]):
			self.window_size = int(argv[6])
		else:
			self.window_size = 1
		
		# prepare array with TCP-segments
		self.read_file()
		
		# initialize values
		self.segment_count = 0
		self.byte_count = 0
		self.estimated_RTT = self.INITIAL_RTT
		self.deviation_RTT = 0

		ack_sock, file_sock = self.open_sockets()

		while (self.segment_count < len(self.file_send_buffer)):
			print ('sending segment number ' + str(self.segment_count))
			stdout.flush()

			this_segment = self.file_send_buffer[self.segment_count]
			self.send_and_receive(this_segment, ack_sock, file_sock)
			
			self.byte_count += len(this_segment.data.strip())
			self.segment_count += 1

		# output data for completed transmission
		print 'Total bytes sent = ' + str(self.byte_count)
		print 'Segments sent = ' + str(self.segment_count)
		print 'Segments retransmitted = ' 
		stdout.flush()

def main(argv):       
	Sender(argv)
	
main(argv)