from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

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

	LOAD = 5
	
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
		self.videos = []
		self.reset = False
		self.loadMovies()

	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		# self.setup = Button(self.master, width=20, padx=3, pady=3)
		# self.setup["text"] = "Setup"
		# self.setup["command"] = self.setupMovie
		# self.setup.grid(row=1, column=0, padx=2, pady=2)

		# Create Description
		self.des = Text(self.master, width=40, padx=3, pady=3, height=10)
		self.des.grid(row=4, columnspan=2, column=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Stop"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
		self.frameContainer = Frame(self.master, width= 200)
		self.frameContainer.grid(column=4, row=1, rowspan=4)

	def loadMovies(self):
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
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.SWITCH and self.fileName != '' or self.reset:
			self.frameNbr = 0
			self.reset = False
			self.sendRtspRequest(self.SETUP)
		elif self.state == self.READY:
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):
		"""Listen for RTP packets."""
		while True:
			if (self.reset == True):
				self.sendRtspRequest(self.PAUSE)
			try:
				data, addr = self.rtpSocket.recvfrom(20480)
				if data:
					rtpData = RtpPacket()
					rtpData.decode(data)

					seqNum = rtpData.seqNum()
					if seqNum > self.frameNbr: 

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
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288)
		self.label.image = photo
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning("Connect to server failed", 'Connection to \'%s\' port= \'%d\' failed.' %self.serverAddr %self.serverPort)

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
			self.rtspSeq += 1

			msg = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

			self.requestSent = self.SETUP
			self.state = self.READY

		elif requestCode == self.PLAY and self.state == self.READY:
			self.rtspSeq += 1

			msg = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.PLAY
			self.state = self.PLAYING

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
		else:
			return
		
		self.rtspSocket.sendall(bytes(msg, 'utf8'))
		
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			try:
				data = self.rtspSocket.recv(1024) # each request will be received 1024 bytes
			except:
				print("Error 1")
			if data:
				self.parseRtspReply(data)
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.split(b'\n')
		seqNum = int(lines[1].split(b' ')[1])

		if seqNum == self.rtspSeq:
			session = int(lines[2].split(b' ')[1])
			if self.sessionId == 0:
				self.sessionId = session
			
			if self.sessionId == session:
				if int(lines[0].split(b' ')[1]) == 200:
					msg = 'RTSP/1.0 200 OK\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) + '\n'
					print(msg)
					if self.requestSent == self.LOAD:
						temp = lines[3].decode()[8: ].split(',')
						self.videos = temp
						self.setList()
						self.state = self.SWITCH
					elif self.requestSent == self.SETUP:
						self.state = self.READY
						self.openRtpPort()
						self.playMovie()
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						self.playEvent.set()
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						self.teardownAcked = 1
	
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
		
		self.rtpSocket.settimeout(0.5)

		try:
			self.rtpSocket.bind(("", self.rtpPort))
		except:
			tkinter.messagebox.showwarning("Unable to Bind", "Unable to bind Port=%d" %self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("Close?", "Do you want to close?"):
			self.exitClient()
		else:
			self.playMovie()

	def setList(self):
		def func(name):
			self.fileName = name
			self.reset = True
			self.des.insert(INSERT, "Switch to file " + name + '\n\n')
			print("Switch to file " + name + '\n\n')
		
		for item in self.videos:
			button = Button(self.frameContainer, text=item, width=20, padx=2, pady=2, command=functools.partial(func, item))
			button.pack(side=TOP)