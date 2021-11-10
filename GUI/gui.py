from abc import abstractmethod
from os import name
import tkinter as tk
from tkinter import ttk
from tkinter import *
import cv2


class GUI:

    def __init__(self) -> None:
        self.root = Tk()

        # This is the section of code which creates the main window
        self.root.geometry('850x570')
        self.root.configure(background='#838B8B')
        self.root.title('Biometric System')


        # This is the section of code which creates a button
        self.btn_cc = Button(self.root, text='Read CC Card', bg='#838B8B', font=(
            'arial', 12, 'normal'), command=self.read_cc_card).place(x=122, y=300)


        # This is the section of code which creates a button
        self.btn_fgp = Button(self.root, text='Read Fingerprint', bg='#838B8B', font=(
            'arial', 12, 'normal'), command=self.read_fingerprint).place(x=492, y=467)


        # This is the section of code which creates a button
        self.btn_frcg = Button(self.root, text='Facial Recoognition', bg='#838B8B', font=(
            'arial', 12, 'normal'), command=self.read_facial).place(x=642, y=467)


        self.create_image()   


        # This is the section of code which creates the a label
        self.lbl_card_info = Label(self.root, text='Card Info', bg='#838B8B', font=(
            'arial', 20, 'normal')).place(x=132, y=57)


        # This is the section of code which creates the a label
        self.lbl_card_name = Label(self.root, text='Name: João Pinto Silva', bg='#838B8B',
            font=('arial', 12, 'normal')).place(x=52, y=107)


        # This is the section of code which creates the a label
        self.lbl_card_nif = Label(self.root, text='NIF: 123456789', bg='#838B8B',
            font=('arial', 12, 'normal')).place(x=52, y=137)


        # This is the section of code which creates the a label
        self.lbl_card_gender = Label(self.root, text='Gender: M', bg='#838B8B', font=(
            'arial', 12, 'normal')).place(x=52, y=167)


        # This is the section of code which creates the a label
        self.lbl_card_rest = Label(self.root, text='(...)', bg='#838B8B', font=(
            'arial', 12, 'normal')).place(x=52, y=197)

    def read_cc_card(self):
        print('clicked')


    # this is the function called when the button is clicked
    def read_fingerprint(self):
        print('clicked')

    def create_image(self, file=""):
        # First, we create a canvas to put the picture on
        Video_Feed = Canvas(self.root, height=400, width=400)
        # Then, we actually create the image file to use (it has to be a *.gif)
        # <-- you will have to copy-paste the filepath here, for example 'C:\Desktop\pic.gif'
        self.picture_file = PhotoImage(file=file)
        # Finally, we create the image on the canvas and then place it onto the main window
        Video_Feed.create_image(400, 0, anchor=NE, image=self.picture_file)
        Video_Feed.place(x=422, y=37)

    # this is the function called when the button is clicked
    def read_facial(self):
        camera = cv2.VideoCapture(0)

        while True:
            return_value, image = camera.read()
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cv2.imshow('image', gray)
            if cv2.waitKey(1) & 0xFF == ord('s'):
                image = cv2.resize(image, (0,0), fx=0.6, fy=0.6) 
                image = cv2.resize(image, (400,400)) 

                cv2.imwrite('img/selfie.png', image)
                img = cv2.imread('img/selfie.png', cv2.IMREAD_UNCHANGED)
                scale_percent = 80
                width = int(img.shape[1] * scale_percent / 100)
                height = int(img.shape[0] * scale_percent / 100)
                dsize = (width, height)

                cv2.resize(img, dsize)

                cv2.imwrite('img/selfie.png', img)

                self.create_image('img/selfie.png')

                break
            
        
        camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    gui = GUI()
    gui.root.mainloop()