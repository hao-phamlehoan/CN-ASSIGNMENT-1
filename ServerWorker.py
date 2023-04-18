from http.client import FORBIDDEN
from random import randint
import sys, traceback, threading, socket
from turtle import speed

from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	DESCRIBE = 'DESCRIBE'
	REWIND = 'REWIND'
	LOAD = 'LOAD'
	FASTER = 'FASTER'
	LOWER = 'LOWER'
	FORWARD = 'FORWARD'
	BACK = 'BACK'
	
	INIT = 0
	SWITCH = 1
	READY = 2
	PLAYING = 3
	state = INIT

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2
	
	clientInfo = {}
	
	def __init__(self, clientInfo):
		self.clientInfo = clientInfo
		self.speed = 0.05
		
	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()
	
	def recvRtspRequest(self):
		"""Receive RTSP request from the client."""
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:            
			data = connSocket.recv(256)
			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"))
	
	def processRtspRequest(self, data):
		"""Process RTSP request sent from the client."""
		# try:
		# Get the request type
		request = data.split('\n')
		line1 = request[0].split(' ')
		requestType = line1[0]
		
		# Get the media file name
		filename = line1[1]
		
		# Get the RTSP sequence number 
		seq = request[1].split(' ')

		# Process LOAD request
		if requestType == self.LOAD:
			if self.state == self.INIT:
				self.clientInfo['session'] = randint(100000, 999999)
				print("processing LOAD\n")
				self.state = self.SWITCH
				self.replyLoad(self.OK_200, seq[1])

		# Process SETUP request
		elif requestType == self.SETUP:
			if self.state == self.SWITCH or self.state == self.PLAYING or self.state == self.READY:
				# Update state
				print("processing SETUP\n")
				
				if self.state == self.PLAYING:
					self.clientInfo['event'].set()
				try:
					self.clientInfo['videoStream'] = VideoStream(filename)
					self.state = self.READY
				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
				
				# Generate a randomized RTSP session ID
				
				# Send RTSP reply
				self.replyInit(self.OK_200, seq[1])
				
				# Get the RTP/UDP port from the last line
				self.clientInfo['rtpPort'] = request[2].split(' ')[3]
		
		# Process PLAY request 		
		elif requestType == self.PLAY:
			if self.state == self.READY:
				print("processing PLAY\n")
				self.state = self.PLAYING
				
				# Create a new socket for RTP/UDP
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				
				self.replyRtsp(self.OK_200, seq[1])
				
				# Create a new thread and start sending RTP packets
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker']= threading.Thread(target=self.sendRtp) 
				self.clientInfo['worker'].start()
		
		# Process PAUSE request
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("processing PAUSE\n")
				self.state = self.READY
				
				self.clientInfo['event'].set()
			
				self.replyRtsp(self.OK_200, seq[1])
		
		# Process TEARDOWN request
		elif requestType == self.TEARDOWN:
			print("processing TEARDOWN\n")
			if self.state == self.PLAYING:
				self.clientInfo['event'].set()
			
			self.replyRtsp(self.OK_200, seq[1])
			
			# Close the RTP socket
			if 'rtpSocket' in self.clientInfo:
				self.clientInfo['rtpSocket'].close()

		# Process DESCRIBE request
		elif requestType == self.DESCRIBE:
			print("processcing DESCRIBE\n")
			self.replyDes(self.OK_200, seq[1], filename)

		# Process FASTER request
		elif requestType == self.FASTER:
			print("processing FASTER\n")
			self.speed/=2
			self.replyRtsp(self.OK_200, seq[1])

		# Process LOWER request
		elif requestType == self.LOWER:
			print("processing LOWER\n")
			self.speed*=2
			self.replyRtsp(self.OK_200, seq[1])

		# Process Forward request
		elif requestType == self.FORWARD:
			try:
				frameNum = int(request[3].split(' ')[1])
			except:
				print(data)
			print("processcing Forward\n")
			self.replyRewind(self.OK_200, seq[1], frameNum)

		# Process Back request
		elif requestType == self.BACK:
			try:
				frameNum = int(request[3].split(' ')[1])
			except:
				print(data)
			print("processcing BACK\n")
			self.replyRewind(self.OK_200, seq[1], frameNum)
		elif requestType == self.REWIND:
			try: 
				frameNum = int(request[3].split(' ')[1])
			except:
				print(data)
			print("processcing REWIND\n")
			self.replyRewind(self.OK_200, seq[1], frameNum)
		else:
			print("Wrong format data")
			
	def sendRtp(self):
		"""Send RTP packets over UDP."""
		while True:
			self.clientInfo['event'].wait(self.speed) 
			
			# Stop sending if request is PAUSE or TEARDOWN
			if self.clientInfo['event'].isSet(): 
				break	
			data = self.clientInfo['videoStream'].nextFrame()
			if data: 
				frameNumber = self.clientInfo['videoStream'].frameNbr()
				try:
					address = self.clientInfo['rtspSocket'][1][0]
					port = int(self.clientInfo['rtpPort'])
					self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
				except:
					print("Connection Error")
					#print('-'*60)
					#traceback.print_exc(file=sys.stdout)
					#print('-'*60)
			else:
				self.clientInfo['event'].set()
				break

	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
		
	def replyRtsp(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			self.clientInfo['rtspSocket'][0].send(reply.encode())
		
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")

	def replyDes(self, code, seq, filename):
    		# body  = "\n\nv=0"
		# body += "\nm=video " + str(self.clientInfo['rtpPort']) + " RTP/AVP " + "26" 
		# body += "\na=control:streamid=" + str(self.clientInfo["session"])
		# body += "\na=\mimetype:string;\"video/MJPEG\""
		numFrame = self.clientInfo['videoStream'].getNumberFrame()
		total_seconds = numFrame / 20
		minutes = total_seconds // 60
		seconds = total_seconds % 60
		time_str = "{:02d}:{:02d}".format(int(minutes), int(seconds))
		if code == self.OK_200:
			reply  = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			reply += '\nName of video: \n' + filename
			reply += '\nTotal time: ' + time_str
			reply += '\nTotal frame: ' + str(numFrame)
			# reply += '\nContent−Length: ' + str(len(body)) + body
			self.clientInfo["rtspSocket"][0].send(reply.encode())
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")

	def replyRewind(self, code, seq, frameNum):
		if code == self.OK_200:
			self.clientInfo['videoStream'].setFrame(frameNum)
			reply  = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\nFrame: ' + str(frameNum)
			self.clientInfo["rtspSocket"][0].send(reply.encode())
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")

	def replyInit(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			numFrame = self.clientInfo['videoStream'].getNumberFrame()
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\nFrame: ' + str(numFrame) + '\nSecPerFrame: ' + '0.05'
			self.clientInfo['rtspSocket'][0].send(reply.encode())
		
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")

	def replyLoad(self, code, seq):
		if code == self.OK_200:
			#print("200 OK")
			videos = ','.join(VideoStream.getVideosList())
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\nVideos: ' + videos
			self.clientInfo['rtspSocket'][0].send(reply.encode())
		
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")