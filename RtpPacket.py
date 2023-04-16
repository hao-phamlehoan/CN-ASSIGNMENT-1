import sys
from time import time
HEADER_SIZE = 12

class RtpPacket:	
	header = bytearray(HEADER_SIZE)
	
	def __init__(self):
		pass
		
	def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
		"""Encode the RTP packet with header fields and payload."""
		timestamp = int(time())
		header = bytearray(HEADER_SIZE)
		#--------------
		# TO COMPLETE
		#--------------
		# Fill the header bytearray with RTP header fields
		
		# header[0] = ...
		# ...
		
		header[0] = 0x00
		header[0] |= (version & 0b11) << 6
		header[0] |= (padding & 0b1) << 5
		header[0] |= (extension & 0b1) << 4
		header[0] |= (cc & 0b1111)

		header[1] = 0x00
		header[1] |= (marker & 0b1) << 7
		header[1] |= (pt & 0b1111111)

		header[2] |= (seqnum & 0xFFFF) >> 8
		header[3] |= (seqnum & 0xFF)

		header[4] |= (timestamp & 0xFFFFFFFF) >> (32 - 8 * 1)
		header[5] |= (timestamp & 0x00FFFFFF) >> (32 - 8 * 2)
		header[6] |= (timestamp & 0x0000FFFF) >> (32 - 8 * 3)
		header[7] |= (timestamp & 0x000000FF) >> (32 - 8 * 4)

		header[8]  |= (ssrc & 0xFFFFFFFF) >> (32 - 8 * 1)
		header[9]  |= (ssrc & 0x00FFFFFF) >> (32 - 8 * 2)
		header[10] |= (ssrc & 0x0000FFFF) >> (32 - 8 * 3)
		header[11] |= (ssrc & 0x000000FF) >> (32 - 8 * 4)

		self.header = header

		# Get the payload from the argument
		# self.payload = ...
		self.payload = payload
		
	def decode(self, byteStream):
		"""Decode the RTP packet."""
		self.header = bytearray(byteStream[:HEADER_SIZE])
		self.payload = byteStream[HEADER_SIZE:]
	
	def version(self):
		"""Return RTP version."""
		return int(self.header[0] >> 6)
	
	def seqNum(self):
		"""Return sequence (frame) number."""
		seqNum = self.header[2] << 8 | self.header[3]
		return int(seqNum)
	
	def timestamp(self):
		"""Return timestamp."""
		timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
		return int(timestamp)
	
	def payloadType(self):
		"""Return payload type."""
		pt = self.header[1] & 127
		return int(pt)
	
	def getPayload(self):
		"""Return payload."""
		return self.payload
		
	def getPacket(self):
		"""Return RTP packet."""
		return self.header + self.payload