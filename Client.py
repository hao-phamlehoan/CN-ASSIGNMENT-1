from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import time
import functools
from tkinter import messagebox 
tkinter.messagebox
from tkinter import ttk

from RtpPacket import RtpPacket

import tkinter as tk

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"
DEFAULT_IMG = "./hihi.jpg"


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
		self.boolean = False
		self.speed =20
		self.loadMovies()
		self.updateMovie(DEFAULT_IMG)	
		self.master.geometry("535x650")
		self.tempFrameNum = -1
  
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def create_gradient(start_color, end_color, width, height):
		gradient = ttk.Frame(width=width, height=height, style="GradientFrame.TFrame")
		gradient.place(x=0, y=0)

		gradient.tk.call(
			"ttk::style", "configure", "GradientFrame.TFrame",
			background=f"linear-gradient(to right, {start_color}, {end_color})"
		)
  
  
	def createWidgets(self):
		"""Build GUI."""
		# Create Text
		self.ann = Text(self.master, width=40, padx=3, pady=3, height=10)
		self.ann.grid(row=5, columnspan=2)
		# Create Description
		self.des = Text(self.master,width=40, padx=3, pady=3, height=10)
		self.des.grid(row=5, columnspan=2, column=2)
		# timestart 
		self.aaa = Label(self.master, width=4,height=1, padx=3, pady=3, text="00:00", bg="#a6dcef")
		self.aaa.grid(row=2, column=0)
		# timeend 
		self.bbb = Label(self.master, width=4,height=1, padx=3, pady=3, text="00:00", bg="#a6dcef")
		self.bbb.grid(row=2, column=3)
		# sroll
		
		# self.scale = Scale(self.master, from_=0, to=1, resolution=0.001, orient=HORIZONTAL, command= lambda event: self.rewindMovie(self.scale.get()))
		# self.scale.grid(row=2, column=1, sticky="WE", pady=0, columnspan=2)
		self.scale = Scale(self.master, from_=0, to=1, resolution=0.001, orient=HORIZONTAL,showvalue=0, command= lambda event: self.rewindMovie(self.scale.get()))
		self.scale.grid(row=2, column=1, sticky="WE", pady=0, columnspan=2)
		
		# Create Play button
		self.start = Button(self.master, width=10, padx=5, pady=5, text="Play", command=self.playMovie, bg="#a6dcef")
		self.start.grid(row=3, column=0, padx=5, pady=5)
		# Create Pause button
		self.pause = Button(self.master, width=10, padx=5, pady=5, text="Pause", command=self.pauseMovie, bg="#ffd966")
		self.pause.grid(row=4, column=0, padx=5, pady=5)
		# Create Faster button
		self.setup = Button(self.master, width=10, padx=5, pady=5, text="Faster", command=self.fasterMovie, bg="#d7bde2")
		self.setup.grid(row=3, column=1, padx=5, pady=5)
		# Create Lower button
		self.setup = Button(self.master, width=10, padx=5, pady=5, text="Lower", command=self.lowerMovie, bg="#f5b7b1")
		self.setup.grid(row=4, column=1, padx=5, pady=5)
		# Create Forward button
		self.teardown = Button(self.master, width=10, padx=5, pady=5, text="Forward", command=self.forwardMovie, bg="#aed6f1")
		self.teardown.grid(row=3, column=2, padx=5, pady=5)
		# Create Back button
		self.describe = Button(self.master, width=10, padx=5, pady=5, text="Back", command=self.backMovie, bg="#f9e79f")
		self.describe.grid(row=4, column=2, padx=5, pady=5)
		# Create Teardown button
		self.teardown = Button(self.master, width=10, padx=5, pady=5, text="Teardown", command=self.exitClient, bg="#f5cba7")
		self.teardown.grid(row=3, column=3, padx=5, pady=5)
		# Describe
		self.describe = Button(self.master, width=10, padx=5, pady=5, text= "Describe", command=self.describeMovie, bg="#d6dbdf")
		self.describe.grid(row=4, column=3, padx=5, pady=5)
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=6, sticky=W, padx=5, pady=5)
   
		self.frameContainer = Frame(self.master, width=200)
		self.frameContainer.grid(column=5, row=0, rowspan=5, padx=5, pady=5, sticky="nsew")

		    # Configure rows
		self.master.grid_rowconfigure(0, weight=1)
		self.master.grid_rowconfigure(1, weight=1)
		self.master.grid_rowconfigure(2, weight=1)
		self.master.grid_rowconfigure(3, weight=1)
		self.master.grid_rowconfigure(4, weight=1)
		self.master.grid_rowconfigure(5, weight=1)

		# Configure columns
		self.master.grid_columnconfigure(0, weight=3)
		self.master.grid_columnconfigure(1, weight=3)
		self.master.grid_columnconfigure(2, weight=3)
		self.master.grid_columnconfigure(3, weight=3)
		self.master.grid_columnconfigure(4, weight=3)
		self.master.grid_columnconfigure(5, weight=1)
  
	def loadMovies(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.LOAD)

	def rewindMovie(self, rate: float):
		if rate > 1:
			rate = 1
		if rate < 0:
			rate = 0
		if (self.state == self.PLAYING or self.state == self.READY) and self.secPerFrame != 0:
			frameNumber = int(rate * self.maxFrame)
		self.tempFrameNum = frameNumber
		# số khung hình hiện tại, ko thay đổi frameNbr
		# số khung hình hiện tại trong thanh kéo, có thay đổi tempFrameNum
		self.sendRtspRequest(self.REWIND)

	def setupMovie(self):
		"""Setup button handler."""
		self.reset = False
		if self.state == self.SWITCH:
			self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
		
		# Close the gui window
		if self.boolean:
			self.sendRtspRequest(self.TEARDOWN)
			self.master.destroy() 
		else:
			self.reset = True	
		# Delete the cache image from video
		try:
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
		except:
			if self.boolean == True:
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
		if self.state == self.SWITCH and self.fileName == '':
			messagebox.showinfo("Thông báo", "Bạn chưa chọn video cần phát.")
		elif self.state == self.SWITCH and self.fileName != '' or self.reset:
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
						x = self.frameNbr / self.maxFrame
						self.scale.set(x)
						total_seconds = self.frameNbr / 20
						minutes = total_seconds // 60
						seconds = total_seconds % 60
						time_str = "{:02d}:{:02d}".format(int(minutes), int(seconds))

						self.aaa.config(text = time_str)
						
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
		#self.ann.insert(INSERT, "TotalFrames: ", + str(self.getN))
		self.ann.insert(INSERT, "Video data recieved: \n"+str(self.totalData))
		self.ann.insert(INSERT, "\nRTP packet loss rate: \n" + str(0 if self.frameNbr == 0 else self.loss/(self.totalFrame + self.loss)))
		self.ann.insert(INSERT, "\nVideo data rate: \n" + str(0 if self.timePeriod == 0 else self.totalData/self.timePeriod))
		self.ann.insert(INSERT, "\nFPS: \n" + str(0 if self.timePeriod == 0 else self.speed))	
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
		elif requestCode == self.REWIND and self.tempFrameNum != -1 and self.tempFrameNum != self.frameNbr:
			self.rtspSeq += 1
			msg = 'REWIND ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq)+ '\nSession: ' + str(self.sessionId) + '\nFrame: ' + str(self.tempFrameNum)
			self.requestSent = self.REWIND
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
						total_seconds = self.maxFrame / 20
						minutes = total_seconds // 60
						seconds = total_seconds % 60
						time_str = "{:02d}:{:02d}".format(int(minutes), int(seconds))
						self.bbb.config(text = time_str)
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
					elif self.requestSent == self.REWIND:
						temp = int(lines[3].decode().split(' ')[1])
						if self.tempFrameNum == temp:
							self.tempFrameNum = -1
							self.frameNbr = temp
									
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
			self.boolean = True
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			self.playMovie()

	def setList(self):
		def func(name):
			self.fileName = name
			self.reset = True
			self.des.insert(INSERT, "Switch to file \n" + name + '\n\n')

		for idx, item in enumerate(self.videos):
			button = Button(self.frameContainer, text=item, width=15, padx=5, pady=5, command=functools.partial(func,item))
			
			# Set different background colors for each button
			if idx == 0:
				button.configure(background='#F9A602', foreground='white')
			elif idx == 1:
				button.configure(background='#40C9A2', foreground='white')
			elif idx == 2:
				button.configure(background='#FF5733', foreground='white')
			elif idx == 3:
				button.configure(background='#FFC300', foreground='white')
			elif idx == 4:
				button.configure(background='#900C3F', foreground='white')
			elif idx == 5:
				button.configure(background='#58B19F', foreground='white')
			elif idx == 6:
				button.configure(background='#FFC107', foreground='white')
			elif idx == 7:
				button.configure(background='#138D75', foreground='white')
			
			# Set the same font and relief for all buttons
			button.configure(font=('Helvetica', 10), relief='raised', borderwidth=3)
			button.pack(side=TOP)
