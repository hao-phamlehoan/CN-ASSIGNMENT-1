from flask import Flask, render_template
from tkinter import *
from tkinterweb import *

app = Flask(__name__)

@app.route('/')
def index():
    # Create a new tkinter window
    root = Tk()
    root.title("My Tkinter App")

    # Add your tkinter widgets here
    label = Label(root, text="Hello, World!")
    label.pack()

    # Embed the tkinter window in a TkinterWeb frame
    frame = TkinterWeb(root, width=400, height=300)
    frame.pack()

    # Return the HTML template with the TkinterWeb frame
    return render_template('index.html', frame=frame)

if __name__ == '__main__':
    app.run(debug=True)
