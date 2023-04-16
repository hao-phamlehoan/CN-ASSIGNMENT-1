import functools

from tkinter import *

import tkinter as tk

window = Tk()
frame_container = Frame(window)

canvas_container = Canvas(frame_container, height=1000)
frame2 = Frame(canvas_container)
myscrollbar = Scrollbar(frame_container, orient="vertical",command=canvas_container.yview) # will be visible if the frame2 is to to big for the canvas
canvas_container.create_window((0,0), window=frame2, anchor='nw')

def func(name):
    print (name)

mylist = ['item1','item2','item3','item4','item5','item6','item7','item8','item9']
for item in mylist:
    button = Button(frame2, text=item, command=functools.partial(func,item))
    button.pack()


frame2.update() # update frame2 height so it's no longer 0 ( height is 0 when it has just been created )
canvas_container.configure(yscrollcommand=myscrollbar.set, scrollregion="0 0 0 %s" % frame2.winfo_height()) # the scrollregion mustbe the size of the frame inside it,
                                                                                                            #in this case "x=0 y=0 width=0 height=frame2height"
                                                                                                            #width 0 because we only scroll verticaly so don't mind about the width.

canvas_container.pack(side=LEFT)
myscrollbar.pack(side=RIGHT, fill = Y)

frame_container.pack()
window.mainloop()