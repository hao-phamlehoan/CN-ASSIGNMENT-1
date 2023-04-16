import os

class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			path = './videos/'+ filename
			repath = os.path.join(os.path.dirname(__file__), path)
			self.file = open(repath, 'rb')
			# self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		self.frames = []
		self.loadFrames()
		
	def nextFrame(self):
		"""Get next frame."""
		# data = self.file.read(5) # Get the framelength from the first 5 bits
		# if data: 
		# 	framelength = int(data)
							
		# 	# Read the current frame
		# 	data = self.file.read(framelength)
		# 	self.frameNum += 1
		if (self.frameNum >= len(self.frames)):
			return None
		data = self.frames[self.frameNum]
		self.frameNum += 1
		return data
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum

	def loadFrames(self):
		frameNum = 0
		while 1:
			data = self.file.read(5)
			if data: 
				framelength = int(data)		
				# Read the current frame
				data = self.file.read(framelength)
				self.frames.append(data)
				frameNum += 1
			else: 
				break

	def getFrame(self, index):
		return self.frames[index]
		
	def setFrame(self, frameNum):
		self.frameNum = frameNum if frameNum < len(self.frames) else len(self.frames) - 1

	def getNumberFrame(self):
		return len(self.frames)

	@staticmethod
	def getVideosList():
		path = './videos/'
		return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
		