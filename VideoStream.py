import os

class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			path = './videos/' + filename
			repath = os.path.join(os.path.dirname(__file__), path)
			self.file = open(repath, 'rb')
			# self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits
		if data: 
			framelength = int(data)
							
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	@staticmethod
	def getVideosList():
		path = './videos/'
		return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
		