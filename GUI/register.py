from abc import abstractmethod
import os
from os import name
import tkinter as tk
from tkinter import ttk
from tkinter import *
import cv2
from pprint import pprint
import PyKCS11
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.backends.interfaces import DHBackend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
import mysql.connector
from mysql.connector import Error
import PIL.Image

from PIL import ImageTk



# self.my_w_child = tk.Toplevel(root)
# self.my_w_child.geometry("500x500")
# self.my_w_child.title('Register')
# my_str1 = tk.StringVar()
# l1 = tk.Label(self.my_w_child, textvariable=my_str1)
# l1.grid(row=1, column=2)
# my_str1.set('Hi I am child window')
# b2 = tk.Button(self.my_w_child, text='Close child',
#                 command=self.my_w_child.destroy)
# b2.grid(row=2, column=2)


class RegisterGUI:

    def __init__(self, main_gui_root) -> None:


        self.user_id = None
        self.user = {
            'SERIAL_NUMBER' : None,
            'GIVEN_NAME' : None,
            'SURNAME' : None
        }

        self.state = {'card_read' : 0, 'facial_recognition' : 0, 'fingerprint_recognition' : 0}

        self.my_w_child = tk.Toplevel(main_gui_root)

        self.my_w_child.geometry("1600x900")
        self.my_w_child.title('Register')
        my_str1 = tk.StringVar()
        b2 = tk.Button(self.my_w_child, text='Quit',
                       command=self.my_w_child.destroy)
        b2.grid(row=2, column=2)

        # DB connection
        try:
            self.connection = mysql.connector.connect(host='localhost',
                                                      database='users',
                                                      user='user',
                                                      password='pwd')
            if self.connection.is_connected():
                db_Info = self.connection.get_server_info()
                print("Connected to MySQL Server version ", db_Info)
                self.cursor = self.connection.cursor()
                self.cursor.execute("select database();")
                record = self.cursor.fetchone()
                print("You're connected to database: ", record)

        except Error as e:
            print("Error while connecting to MySQL", e)

        # This is the section of code which creates the main window
        
        self.frame_width = 1600
        self.frame_height = 900

        self.framerow1height = self.frame_height/10
        self.framerow2height = self.frame_height/1.5

        self.framerow_center = self.frame_width/3

        self.videocanvasheight = 375
        self.videocanvaswidth = 500

        ##################################################### CC #####################################################
        w = self.framerow_center / 5

        self.lbl_card_info = Label(self.my_w_child, text='Card Info', font=(
            'arial', 20, 'normal')).place(x=w, y=self.framerow1height)

        self.lbl_card_name = Label(self.my_w_child, text='',
                                   font=('arial', 12, 'normal')).place(x=w, y=self.framerow1height + 50)

        self.lbl_card_nif = Label(self.my_w_child, text='',
                                  font=('arial', 12, 'normal')).place(x=w, y=self.framerow1height + 100)

        self.lbl_card_gender = Label(self.my_w_child, text='', font=(
            'arial', 12, 'normal')).place(x=w, y=self.framerow1height + 150)

        self.btn_cc = Button(self.my_w_child, text='Read CC Card', font=(
            'arial', 12, 'normal'), command=self.read_cc).place(x=w, y=self.framerow1height + 150)

        ##################################################### FACIAL #####################################################
        self.create_image()
        w = self.framerow_center

        self.lbl_card_info = Label(self.my_w_child, text='Facial Recognition', font=(
            'arial', 20, 'normal')).place(x=w, y=self.framerow1height)

        self.btn_frcg = Button(self.my_w_child, text='Facial Recognition', font=(
            'arial', 12, 'normal'), command=self.read_facial)
            
        self.btn_frcg.place(x=w, y=self.framerow1height + self.videocanvasheight + 60)

        self.btn_frcg.config(state=tk.DISABLED)

        ##################################################### FINGERPRINT #####################################################

        w = self.framerow_center + self.videocanvaswidth + 100
        self.lbl_card_info = Label(self.my_w_child, text='Read Fingerprint', font=(
            'arial', 20, 'normal')).place(x=w, y=self.framerow1height)

        self.btn_fgp = Button(self.my_w_child, text='Read Fingerprint', font=(
            'arial', 12, 'normal'), command=self.read_fingerprint)
            
        self.btn_fgp.place(x=w, y=self.framerow1height + 50)

        self.btn_fgp.config(state=tk.DISABLED)

        ##################################################### ENROLL #####################################################

        w = self.framerow_center

        self.btn_enroll = Button(self.my_w_child, text='Enroll', font=(
            'arial', 12, 'normal'), command=self.enroll).place(x=w, y=self.framerow2height)

    def enroll(self):
        if self.state['card_read'] == 1:
            if self.state['facial_recognition'] + self.state['fingerprint_recognition'] > 0:
                # Insert new user
                user_insert_query = """ INSERT INTO users
                               (cc_number, given_name, surname, bio_data_location) VALUES (%s,%s,%s,%s)"""
                user = (self.user['SERIAL_NUMBER'], self.user['GIVEN_NAME'], self.user['SURNAME'], "bio_data/" + self.user['SERIAL_NUMBER'])
                self.cursor.execute(user_insert_query, user)
                print("Enrolled.")
                self.my_w_child.destroy()
            else:
                print("Can't enroll. Need at least 1 biometric authentication factor.")
        else:
            print("Can't enroll. Card not read.")

    def verify_cc(self):
        '''
        The existence of a CC is verified by the PKCS11 driver.
        '''
        try:
            lib = '/usr/local/lib/libpteidpkcs11.so'
            pkcs11 = PyKCS11.PyKCS11Lib()
            pkcs11.load(lib)
            slots = pkcs11.getSlotList()
            if slots:
                print("CC verified..")
                return pkcs11
            else:
                print("No CC inserted.")
                exit(0)
        except:
            print("CC verification failed.")
            exit(0)

    def read_cc(self):
        '''
        Needed info is retrieved from the Citizen Card:
        Name, serial number (Civil ID), Auth PrivKey and Citizen Authentication Cerificate.
        '''
        print("Reading Citizen card...")
        pkcs11 = self.verify_cc()
        print("Retrieving data from CC...")
        slot = pkcs11.getSlotList(tokenPresent=True)[0]
        all_attr = list(PyKCS11.CKA.keys())
        all_attr = [e for e in all_attr if isinstance(e, int)]
        session = pkcs11.openSession(slot)
        userInfo = dict()
        for obj in session.findObjects():
            # Get object attributes
            attr = session.getAttributeValue(obj, all_attr)
            # Create dictionary with attributes
            attr = dict(zip(map(PyKCS11.CKA.get, all_attr), attr))
            if attr['CKA_LABEL'] == 'CITIZEN AUTHENTICATION CERTIFICATE':
                if attr['CKA_CERTIFICATE_TYPE'] != None:
                    cert_bytes = bytes(attr['CKA_VALUE'])
                    cert = x509.load_der_x509_certificate(
                        cert_bytes, backend=default_backend())
                    userInfo['GIVEN_NAME'] = cert.subject.get_attributes_for_oid(
                        x509.NameOID.GIVEN_NAME)[0].value
                    userInfo['SURNAME'] = cert.subject.get_attributes_for_oid(x509.NameOID.SURNAME)[
                        0].value
                    userInfo['SERIAL_NUMBER'] = cert.subject.get_attributes_for_oid(
                        x509.NameOID.SERIAL_NUMBER)[0].value

        private_key = session.findObjects([
            (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
            (PyKCS11.CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')
        ])[0]

        print("USER INFO:")
        pprint(userInfo)

        # # Insert new user
        # sql_insert_query = """ INSERT INTO users
        #                (cc_number, given_name, surname, bio_data_location) VALUES (%s,%s,%s,%s)"""
        # # tuple to insert at placeholder
        # user = (userInfo['GIVEN_NAME'], userInfo['SURNAME'], userInfo['SERIAL_NUMBER'], "bio_data/" + userInfo['SERIAL_NUMBER'])

        # Check if user exists
        user_select_query = f"SELECT * FROM users WHERE cc_number = '{userInfo['SERIAL_NUMBER']}'"
        user_id = (userInfo['SERIAL_NUMBER'])

        self.cursor.execute(user_select_query)
        records = self.cursor.fetchall()
        print("Users match: ", self.cursor.rowcount)

        self.lbl_card_name = Label(self.my_w_child, text=userInfo['GIVEN_NAME'] + " " + userInfo['SURNAME'] + "\n" + userInfo['SERIAL_NUMBER'],
                                   font=('arial', 12, 'normal')).place(x=52, y=107)
        
        
        if self.cursor.rowcount > 0:
            self.lbl_card_rest = Label(self.my_w_child, text='User already exists.', bg='#FF0000', font=(
                'arial', 12, 'normal')).place(x=52, y=197)

        else:
            self.lbl_card_rest = Label(self.my_w_child, text="Card read. Proceed...", bg='#00FF00', font=(
                'arial', 12, 'normal')).place(x=52, y=197)
            self.user_id = userInfo['SERIAL_NUMBER']
            self.user['SERIAL_NUMBER'] = userInfo['SERIAL_NUMBER']
            self.user['GIVEN_NAME'] = userInfo['GIVEN_NAME']
            self.user['SURNAME'] = userInfo['SURNAME']
            self.state['card_read'] = 1
            self.btn_frcg.config(state=tk.NORMAL) 

        return cert_bytes, userInfo, private_key, session

    # this is the function called when the button is clicked

    def read_fingerprint(self):
        print('clicked')

    def create_image(self, file=""):
        # First, we create a canvas to put the picture on
        Video_Feed = Canvas(
            self.my_w_child, height=self.videocanvasheight, width=self.videocanvaswidth, bg="white")
        # Then, we actually create the image file to use (it has to be a *.gif)
        # <-- you will have to copy-paste the filepath here, for example 'C:\Desktop\pic.gif'
        self.picture_file = PhotoImage(file=file)
        # Finally, we create the image on the canvas and then place it onto the main window
        Video_Feed.create_image(400, 0, anchor=NE, image=self.picture_file)
        Video_Feed.place(x=self.framerow_center, y=self.framerow1height + 50)

    # this is the function called when the button is clicked
    def read_facial(self, user_id=5):
        camera = cv2.VideoCapture('http://192.168.1.215:8080/video')
        counter = 0
        while True:
            return_value, image = camera.read()
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cv2.imshow('image',image)
            if cv2.waitKey(1) & 0xFF == ord('s'):
                image = cv2.resize(image, (0, 0), fx=0.6, fy=0.6)
                image = cv2.resize(image, (400, 400))

                cv2.imwrite(f'img/{self.user_id}_{counter}.png', image)
                img = cv2.imread(f'img/{self.user_id}_{counter}.png', cv2.IMREAD_UNCHANGED)
                scale_percent = 80
                width = int(img.shape[1] * scale_percent / 100)
                height = int(img.shape[0] * scale_percent / 100)
                dsize = (width, height)

                cv2.resize(img, dsize)

                cv2.imwrite(f'img/{self.user_id}_{counter}.png', img)

                self.create_image(f'img/{self.user_id}_{counter}.png')

                counter+=1
            
            if counter >= 5:
                break
        
        camera.release()
        cv2.destroyAllWindows()


        current_directory = os.getcwd()
        final_directory = os.path.join(current_directory, f'backend/bio_data/{self.user_id}')
        temp_directory = os.path.join(current_directory, f'img')
        print(final_directory)
        if not os.path.exists(final_directory):
            os.makedirs(final_directory)
        for i in range(5):
            os.rename(f'{temp_directory}/{self.user_id}_{i}.png', f'{final_directory}/{i}.png')
        self.state['facial_recognition'] = 1
        

if __name__ == "__main__":
    gui = RegisterGUI()
    gui.root.mainloop()
