import tkinter as tk
from tkinter import * 
my_w = tk.Tk()
my_w.geometry("200x200")  # Size of the window 
my_w.title("www.plus2net.com")  # Adding a title

# create one lebel 
my_str = tk.StringVar()
l1 = tk.Label(my_w,  textvariable=my_str )
l1.grid(row=1,column=2) 
my_str.set("Hi I am main window")
# add one button 
b1 = tk.Button(my_w, text='Clik me to open new window',
               command=lambda:my_open())
b1.grid(row=2,column=2) 

def my_open():
    my_w_child=tk.Toplevel(my_w)
    my_w_child.geometry("200x200")
    my_w_child.title('www.plus2net.com')
    my_str1=tk.StringVar()
    l1=tk.Label(my_w_child,textvariable=my_str1)
    l1.grid(row=1,column=2)
    my_str1.set('Hi I am child window')
    b2=tk.Button(my_w_child,text='Close child',command=my_w_child.destroy)
    b2.grid(row=2,column=2)
    b3 = tk.Button(my_w_child, text='Disable parent',command=lambda:my_w_child.grab_set())
    b3.grid(row=4,column=2)
    # change background color of parent from child
    b4 = tk.Button(my_w_child, text='Parent Colour',
		command=lambda:my_w.config(bg='red'))
    b4.grid(row=4,column=2)
    # change background color of child from parent 
    b5 = tk.Button(my_w, text='Child Colour',
		command=lambda:my_w_child.config(bg='green'))
    b5.grid(row=5,column=2)
my_w.mainloop()