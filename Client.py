from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import time
import functools

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	SWITCH = 1
	READY = 2
	PLAYING = 3
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	DESCRIBE = 4
	LOAD = 5
	FASTER = 6
	LOWER = 7
	FORWARD = 8
	BACK = 9
	REWIND = 10
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = ''
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.timePeriod = 0
		self.totalData = 0
		self.loss = 0
		self.maxFrame = 0
		self.secPerFrame = 0
		self.totalFrame = 0
		self.videos = []
		self.reset = False
		self.speed =20
		self.loadMovies()
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Text
		self.ann = Text(self.master, width=40, padx=3, pady=3, height=10)
		self.ann.grid(row=4, columnspan=2)

		# Create Description
		self.des = Text(self.master, width=40, padx=3, pady=3, height=10)
		self.des.grid(row=4, columnspan=2, column=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=2, column=0, padx=0, pady=0)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=3, column=0, padx=0, pady=0)
		
		# Create Faster button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Faster"
		self.setup["command"] = self.fasterMovie
		self.setup.grid(row=2, column=1, padx=2, pady=2)

		# Create Lower button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Lower"
		self.setup["command"] = self.lowerMovie
		self.setup.grid(row=3, column=1, padx=2, pady=2)

		# Create Foward button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Forward"
		self.teardown["command"] =  self.forwardMovie
		self.teardown.grid(row=2, column=2, padx=2, pady=2)

		# Create Back button
		self.describe = Button(self.master, width=20, padx=3, pady=3)
		self.describe["text"] = "Back"
		self.describe["command"] = self.backMovie
		self.describe.grid(row=3, column=2, padx=2, pady=2)

		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=2, column=3, padx=2, pady=2)

		# Describe
		self.describe = Button(self.master, width=20, padx=3, pady=3)
		self.describe["text"] = "Describe"
		self.describe["command"] = self.describeMovie
		self.describe.grid(row=3, column=3, padx=2, pady=2)

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=6, sticky=W+E+N+S, padx=5, pady=5) 

		self.frameContainer = Frame(self.master, width = 200)
		self.frameContainer.grid(column=4, row= 1, rowspan = 4)

	def loadMovies(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.LOAD)

	def setupMovie(self):
		"""Setup button handler."""
		self.reset = False
		if self.state == self.SWITCH:
			self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)
		# Close the gui window
		self.master.destroy() 
		# Delete the cache image from video
		try:
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
		except:
			print("No such cache file to delete")

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)

	def fasterMovie(self):
		"""Faster button handler."""
		self.sendRtspRequest(self.FASTER)

	def lowerMovie(self):
		"""Lower button handler."""
		self.sendRtspRequest(self.LOWER)

	def forwardMovie(self):
		"""Forward button handler."""
		self.sendRtspRequest(self.FORWARD)

	def backMovie(self):
		"""Back button handler."""
		self.sendRtspRequest(self.BACK)

	def describeMovie(self):
		"""Describe button handler."""
		self.sendRtspRequest(self.DESCRIBE)

	def playMovie(self):
		"""Play button handler."""
		if self.state == self.SWITCH and self.fileName != '' or self.reset:
			self.frameNbr = 0
			self.reset = False
			self.sendRtspRequest(self.SETUP)
		elif self.state == self.READY:
			self.startRecv = time.time()
			# Create a new thread to connect to server and listen to the change on server
			threading.Thread(target=self.listenRtp).start()
			# Create a variable to save the next event after click on the button "Play"
			self.playEvent = threading.Event()
			
			# Block thread until the request PLAY send to server and client receive the response
			self.playEvent.clear()
			# Send request to server
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):
		"""Listen for RTP packets."""
		while True:
			if (self.frameNbr >= self.maxFrame or self.reset == True):
				self.sendRtspRequest(self.PAUSE)
			try:
				data, _ = self.rtpSocket.recvfrom(20480) # load all bytes need to display
				
				if data:
					self.totalFrame += 1
					rtpData = RtpPacket()
					rtpData.decode(data)

					seqNum = rtpData.seqNum()
					if seqNum > self.frameNbr: # Discard the late packet
						self.endRecv = time.time()
						if (self.endRecv < self.startRecv):
							print("TIME ERROR")
						if seqNum > self.frameNbr + 1 and self.tempFrameNum != -1:
							self.loss += seqNum - self.frameNbr
						self.timePeriod += self.endRecv - self.startRecv
						self.totalData += len(rtpData.getPayload())
						self.startRecv = time.time()

						self.frameNbr = seqNum
						if self.teardownAcked != 1:
							self.updateMovie(self.writeFrame(rtpData.getPayload())) # send cache name to update movie to change content
						else:
							self.rtpSocket.shutdown(socket.SHUT_RDWR)
							self.rtpSocket.close()
							self.state = self.READY
							break

			except:
				if self.playEvent.isSet():
					self.state = self.READY
					break
				
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					self.state = self.READY
					break
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT # name of cache file
		file = open(cachename, "wb") # open file with authorization: write and the standard file is binary
		file.write(data)
		file.close()
		
		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile)) # read the data and transger to variable "photo" by using Tk package
		self.label.configure(image = photo, height=288) 
		self.label.image = photo # update screen
		self.ann.delete("1.0", END)

		self.ann.insert(INSERT, "Video data recieved: "+str(self.totalData))
		self.ann.insert(INSERT, "\nRTP packet loss rate: " + str(0 if self.frameNbr == 0 else self.loss/(self.totalFrame + self.loss)))
		self.ann.insert(INSERT, "\nVideo data rate: " + str(0 if self.timePeriod == 0 else self.totalData/self.timePeriod))
		self.ann.insert(INSERT, "\nFPS: " + str(0 if self.timePeriod == 0 else self.speed))	
		# self.setTime()
		
	def connectToServer(self):
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		if requestCode == self.LOAD and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			self.rtspSeq += 1
			msg = 'LOAD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.LOAD

		elif requestCode == self.SETUP and self.state != self.INIT:
			# update rptspSeq = self.[action]
			self.rtspSeq += 1
			# save the content of action
			msg = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
			# keep track the request sent to server
			self.requestSent = self.SETUP
			self.state = self.READY
		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			self.rtspSeq += 1

			msg = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.PLAY
			self.state = self.PLAYING
		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			self.rtspSeq += 1

			msg = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.PAUSE
			self.state = self.READY
		# Teardown request
		elif requestCode == self.TEARDOWN and (self.state == self.PLAYING or self.state == self.READY or self.state == self.SWITCH):
			self.rtspSeq += 1

			msg = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) 
			self.requestSent = self.TEARDOWN
			self.state = self.INIT

		elif requestCode == self.DESCRIBE and (self.state == self.PLAYING or self.state == self.READY):
			self.rtspSeq += 1

			msg = 'DESCRIBE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) 
			self.requestSent = self.DESCRIBE

		# Faster request
		elif requestCode == self.FASTER :
			#Update speed
			self.speed *=2
        
			# Update RTSP sequence number.
			self.rtspSeq+=1
        
			# Write the RTSP request to be sent.
			msg = 'FASTER ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.FASTER		
			# Lower request
		elif requestCode == self.LOWER:
			#Update speed
			self.speed /=2

			# Update RTSP sequence number.
			self.rtspSeq+=1
        
			# Write the RTSP request to be sent.
			msg = 'LOWER ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			# Keep track of the sent request.
			self.requestSent = self.LOWER
			# Forward request
		elif requestCode == self.FORWARD :
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			# Update frame
			self.frameNbr +=30

			# Write the RTSP request to be sent.
			msg = 'FORWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) + '\nFrame: ' + str(self.frameNbr)
			
			# Keep track of the sent request.
			self.requestSent = self.FORWARD
			# Back request
		elif requestCode == self.BACK :
			# Update RTSP sequence number.
			self.rtspSeq+=1
        
			# # Update frame
			self.frameNbr -=30
			if self.frameNbr < 0:
				self.frameNbr = 0

			# Write the RTSP request to be sent.
			msg = 'BACK ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) + '\nFrame: ' + str(self.frameNbr)
			
			# Keep track of the sent request.
			self.requestSent = self.BACK
		else:
			return
		
		# Send request to server using rtspSocket
		self.rtspSocket.sendall(bytes(msg, 'utf8'))
		
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			try:
				data = self.rtspSocket.recv(1024) # each request will be received 1024 bytes
			except:
				print("Error 1")
			if data:
				# try:
				self.parseRtspReply(data)
				# except:
				# 	print("Error 2")
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.split(b'\n')
		seqNum = int(lines[1].split(b' ')[1])
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(b' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(b' ')[1]) == 200: # The status code 200 is OK
					if self.requestSent == self.LOAD:
						temp = lines[3].decode()[8: ].split(',')
						self.videos = temp
						self.setList()
						self.state = self.SWITCH

					elif self.requestSent == self.SETUP:
						self.maxFrame = int(lines[3].decode().split(' ')[1])
						self.secPerFrame = float(lines[4].decode().split(' ')[1])
						# Update RTSP state.
						self.state = self.READY
						# Open RTP port.
						self.openRtpPort()
						self.playMovie()
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 
					elif self.requestSent == self.DESCRIBE:
						temp = lines[3].decode()
						for i in range(4, len(lines)):
							temp += '\n' + lines[i].decode()
						self.des.insert(INSERT, temp + '\n\n')
									
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		
		try:
			# Bind the socket to the address using the RTP port given by the client user
			self.rtpSocket.bind(("", self.rtpPort))
		except:
			tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			self.playMovie()

	def setList(self):
		def func(name):
			self.fileName = name
			self.reset = True
			self.des.insert(INSERT, "Switch to file " + name + '\n\n')
		for item in self.videos:
			button = Button(self.frameContainer, text=item, width=20, padx=2, pady=2, command=functools.partial(func,item))
			button.pack(side=TOP)