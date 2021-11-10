import tkinter as tk
from tkinter import ttk
from tkinter import * 

# this is the function called when the button is clicked
def read_cc_card():
	print('clicked')


# this is the function called when the button is clicked
def read_fingerprint():
	print('clicked')


# this is the function called when the button is clicked
def read_facial():
	print('clicked')



root = Tk()

# This is the section of code which creates the main window
root.geometry('850x570')
root.configure(background='#838B8B')
root.title('Biometric System')


# This is the section of code which creates a button
Button(root, text='Read CC Card', bg='#838B8B', font=('arial', 12, 'normal'), command=read_cc_card).place(x=122, y=300)


# This is the section of code which creates a button
Button(root, text='Read Fingerprint', bg='#838B8B', font=('arial', 12, 'normal'), command=read_fingerprint).place(x=492, y=467)


# This is the section of code which creates a button
Button(root, text='Facial Recoognition', bg='#838B8B', font=('arial', 12, 'normal'), command=read_facial).place(x=642, y=467)


# First, we create a canvas to put the picture on
Video_Feed= Canvas(root, height=400, width=400)
# Then, we actually create the image file to use (it has to be a *.gif)
picture_file = PhotoImage(file = '')  # <-- you will have to copy-paste the filepath here, for example 'C:\Desktop\pic.gif'
# Finally, we create the image on the canvas and then place it onto the main window
Video_Feed.create_image(400, 0, anchor=NE, image=picture_file)
Video_Feed.place(x=422, y=37)


# This is the section of code which creates the a label
Label(root, text='Card Info', bg='#838B8B', font=('arial', 20, 'normal')).place(x=132, y=57)


# This is the section of code which creates the a label
Label(root, text='Name: João Pinto Silva', bg='#838B8B', font=('arial', 12, 'normal')).place(x=52, y=107)


# This is the section of code which creates the a label
Label(root, text='NIF: 123456789', bg='#838B8B', font=('arial', 12, 'normal')).place(x=52, y=137)


# This is the section of code which creates the a label
Label(root, text='Gender: M', bg='#838B8B', font=('arial', 12, 'normal')).place(x=52, y=167)


# This is the section of code which creates the a label
Label(root, text='(...)', bg='#838B8B', font=('arial', 12, 'normal')).place(x=52, y=197)


root.mainloop()
