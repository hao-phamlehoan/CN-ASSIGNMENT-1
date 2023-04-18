import sys
from tkinter import Tk
from Client import Client

import tkinter as tk
import tkinterweb as tkweb

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")	
	
	root = Tk()
	
	# Create a new client
	app = Client(root, serverAddr, serverPort, rtpPort)
	app.master.title("RTPClient")	
	root.mainloop()
	