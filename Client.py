from tkinter import *
import tkinter.messagebox
tkinter.messagebox
import time
from tkinter import messagebox 
tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
from RtpPacket import RtpPacket

from tkinter import messagebox, PhotoImage


CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:

	SETUP_STR = 'SETUP'
	PLAY_STR = 'PLAY'
	PAUSE_STR = 'PAUSE'
	TEARDOWN_STR = 'TEARDOWN'
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	RTSP_VER = "RTSP/1.0"
	TRANSPORT = "RTP/UDP"
	
	
	
	# Khởi tạo đối tượng
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.master.geometry("400x360")
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
  		

	####################################################
	#Hàm này dùng để tạo giao diện bao gồm các nút
	def createWidgets(self):
		"""Build GUI."""
		# Tạo cái nút setup
		self.master.rowconfigure(2, weight=1)
		self.master.columnconfigure(0, weight=25)
		self.master.columnconfigure(1, weight=25)
		self.master.columnconfigure(2, weight=25)
		self.master.columnconfigure(3, weight=25)

		self.setup = Button(self.master, width=20, padx=10, pady=10, bg='gray', fg='white')
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=5, pady=5, sticky="SE")
		
		# Tạo cái nút play	
		self.start = Button(self.master, width=20, padx=10, pady=10, bg='green', fg='white')
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=5, pady=5, sticky="S")
		
		# Tạo cái nút Pause ấy		
		self.pause = Button(self.master, width=20, padx=10, pady=10, bg='blue', fg='white')
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=5, pady=5, sticky="S")
		# Tạo cái nút teardown
		self.teardown = Button(self.master, width=20, padx=10, pady=10, bg='red', fg='white')
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=5, pady=5, sticky="S")
		
		# Tạo 1 nhãn để hiển thị video
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=S, padx=5, pady=5) 

	##################################################
	# Khi nhấn setup thì sẽ gửi 1 yêu cầu RTSP tới server
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	##################################################
	# Khi ấn nút teardown thì sẽ gửi 1 yêu cầu RTSP tới server để ngừng phát video + đóng kết nối RTSP && RTP
	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)		
		self.master.destroy() # Close the gui window
	# Dòng này để đóng ứng dụng và xoá cache đã lưu
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) 

	##################################################
	# Khi nhấn pause thì hàm này sẽ gửi 1 RTSP tới server
	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	##################################################
	#Khi ấn play thì sẽ gửi 1 RTSP tới server, đồng thời tạo 1 luồng mới để nghe các gói RTP gửi tới
	def playMovie(self):
		"""Play button handler."""
		self.sendRtspRequest(self.SETUP)
		if self.state == self.INIT or self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	
 	##################################################
	# Hàm này dùng để lắng nghe các gói RTP gửi tới, đồng thời cập nhật video vào giao diện ng dùng
	def listenRtp(self):		
		"""Listen for RTP packets."""
		totalReceived = 0
		totalLost = 0
		while True:
			try:
				print("LISTENING...")
				data = self.rtpSocket.recv(20480) # nhận dữ liêụ gói tin RTP = recv
				if data:
					rtpPacket = RtpPacket()	# trích xuất các trường thông tin
					rtpPacket.decode(data) # lấy dữ liệu
					
					currFrameNbr = rtpPacket.seqNum() # lấy stt khung hình 
					print ("CURRENT SEQUENCE NUM: " + str(currFrameNbr))
										
					if currFrameNbr > self.frameNbr: # Discard the late packet
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
						totalReceived += 1
					else:
						totalLost += 1

			except:
				# Vòng lặp dừng khi gặp Pause || Teardown
				if self.playEvent.isSet(): 
					break
				
				# Nhận đc ACK cho yêu cầu dừng phát video
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break
		print("Tổng số hình ảnh đã nhận: ", totalReceived)
		print ("Số hình ảnh bị rơi rớt: ", totalLost )
		packetLossRate = (totalLost / (totalReceived + totalLost)) * 100
		print("Tỉ lệ % rơi rớt hình ảnh là: " + str(packetLossRate) + "%")
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename

	def updateMovie(self, imageFile):
		# img = ImageTk.PhotoImage(Image.open(r'E:/CN-ASSIGNMENT-1/catFish.jpg'))
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image=photo, width= 640, height=287, bg = "pink")
		self.label.image = photo
    
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		
		# Setup request
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
                
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.SETUP_STR,self.fileName,self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nTransport: %s; client_port= %d" % (self.TRANSPORT,self.rtpPort)
			
			# Keep track of the sent request.
			self.requestSent = self.SETUP
			
			# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
        
			# Update RTSP sequence number.
			self.rtspSeq+=1
        
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.PLAY_STR,self.fileName,self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d"%self.sessionId
                
			
			# Keep track of the sent request.
			self.requestSent = self.PLAY
            
            
            # Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
        
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			request = "%s %s %s" % (self.PAUSE_STR,self.fileName,self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d"%self.sessionId
			
			self.requestSent = self.PAUSE
			
			# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
        
			# Update RTSP sequence number.
			self.rtspSeq+=1
			
			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.TEARDOWN_STR, self.fileName, self.RTSP_VER)
			request+="\nCSeq: %d" % self.rtspSeq
			request+="\nSession: %d" % self.sessionId
			
			self.requestSent = self.TEARDOWN

		else:
			return
		
		# Send the RTSP request using rtspSocket.
		self.rtspSocket.send(request.encode())
		
		print ('\nData Sent:\n' + request)
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspSocket.recv(1024)
			
			if reply: 
				self.parseRtspReply(reply)
			
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.decode().split('\n')
		seqNum = int(lines[1].split(' ')[1])
		
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:
						#-------------
						# TO COMPLETE
						#-------------
                        
                        
						# Update RTSP state.
						self.state = self.READY
						
						# Open RTP port.
						self.openRtpPort() 
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
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
    
		#-------------
		# TO COMPLETE
		#-------------
        
        
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
		
		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		
		try:
			# Bind the socket to the address using the RTP port given by the client user.
			self.state=self.READY
			self.rtpSocket.bind(('',self.rtpPort))
		except:
			messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if messagebox.askokcancel("Bạn muốn thoát ư?", "Hic, Tam bietttt", icon = "warning") :
			# messagebox.showinfo("Thông báo", "Bạn đã chọn OK.")
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			self.playMovie()
			