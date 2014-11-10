'''
Sender: Reads data from a file and uses the sending services of the TCP-like 
protocol to deliver it to the remote host.

Handles in network packet loss, packet corruption, packet duplication and packet 
reordering and copes with dynamic network delays.

@author: Emily Pakulski
'''

from sys import argv, stdout, exit
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, timeout
from threading import Timer, current_thread
from TCP_Segment import TCP_Segment
import datetime

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
						  + 'FIN: ' + str(FIN) + ', ' \
						  + 'Estimated RTT: ' + str(self.estimated_RTT) + '\n')
	
	# calls all the relevant RTT functions to update things
	def update_timeout_and_RTT(self, sample_RTT):
		self.update_deviation_RTT(sample_RTT)
		self.update_estimated_RTT(sample_RTT)
		self.update_tiemout_interval(sample_RTT)
	
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

	def update_tiemout_interval(self, sample_RTT):
		self.timeout_interval = self.estimated_RTT + 4 * self.deviation_RTT

	def send_and_receive(self, unpacked_segment, ack_sock, file_sock):
		packed_segment = unpacked_segment.pack_segment()
	
		file_sock.sendto(packed_segment, (self.remote_ip, self.remote_port))
		send_time = datetime.datetime.now() # save sendtime for logging

		# try to send; if timeout, retransmit
		try:
			ack_sock.settimeout(self.timeout_interval)
			ack_no = ack_sock.recv(self.ACK_BUFF)

			# if successful, log and update RTTs
			recv_time = datetime.datetime.now()

			self.update_timeout_and_RTT((recv_time - send_time).total_seconds())
			self.log_data(send_time, unpacked_segment.sequence_no, ack_no, unpacked_segment.FIN)
		except timeout:
			self.retransmit_count += 1
			self.send_and_receive(unpacked_segment, ack_sock, file_sock)

	# create TCP-segments with all fields filled in.
	def read_file(self):
		self.file_send_buffer = []

		with open(self.filename, "rb") as f:
			current_chunk = f.read(TCP_Segment.MSS)
			sequence_no = 0
			expected_ACK = sequence_no + len(current_chunk)
			
			# create each TCP segment and append it to the array
			while current_chunk != '':
				previous_chunk = current_chunk
				current_chunk = f.read(TCP_Segment.MSS)

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
				sequence_no += len(previous_chunk)
				expected_ACK = sequence_no + len(current_chunk) # for stop and wait, expected_ACK == sequence_no
			
			self.byte_count += sequence_no # collecting transmission statistics

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
		
		# initialize instance vars
		self.segment_count = 0
		self.byte_count = 0
		self.retransmit_count = 0
		self.estimated_RTT = self.INITIAL_RTT
		self.timeout_interval = self.INITIAL_TIMEOUT
		self.deviation_RTT = 0

		# explain that only window size of 1 is supported
		if (self.window_size != 1):
			print 'Sorry, this is a stop-and-go implementation of TCP, ',
			print 'and as such a window size of greater than 1 is not supported.'
			stdout.flush()
			exit(0)

		try:
			# prepare array with TCP-segments
			self.read_file()
		except:
			print 'Error: file \'' + self.filename + '\' not found.',
			print 'Please check the filename and try again. '
			stdout.flush()
			exit(0)

		# open both sockets
		ack_sock, file_sock = self.open_sockets()

		start_transmission_time = datetime.datetime.now()
		while (self.segment_count < len(self.file_send_buffer)):
			this_segment = self.file_send_buffer[self.segment_count]
			self.send_and_receive(this_segment, ack_sock, file_sock)
			self.segment_count += 1

		# output data for completed transmission
		print 'Delivery completed successfully.'
		print 'Total bytes sent = ' + str(self.byte_count)
		print 'Segments sent [successfully] = ' + str(self.segment_count)
		print 'Segments retransmitted = ' + str(self.retransmit_count)
		print 'Segments sent [including retransmissions] = ' + str(self.segment_count + self.retransmit_count)

		# output additional statistics
		total_seconds = (datetime.datetime.now() - start_transmission_time).total_seconds()
		print '\nTotal delivery time = ' + str(total_seconds) + ' seconds. '
		print 'Average bytes per second = ' + str(total_seconds / self.byte_count) + ' B/s. '
		stdout.flush()


def main(argv):       
	Sender(argv)
	
main(argv)