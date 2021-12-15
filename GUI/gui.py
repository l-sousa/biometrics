from abc import abstractmethod
from os import name
import os
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
import time
import numpy as np

from PIL import ImageTk

import time
import serial

import adafruit_fingerprint

from register import RegisterGUI
import face_recognition

class GUI:

    def __init__(self) -> None:
        self.root = Tk()

        self.user_id = None
        self.user = {
            'SERIAL_NUMBER' : None,
            'GIVEN_NAME' : None,
            'SURNAME' : None,
            'BIO_DATA_LOCATION' : None,
            'HAS_FACIAL' : False,
            'HAS_FINGERPRINT' : False,
            'FINGERPRINT_ID_SENSOR': None
        }

        self.state = {'card_read' : 0, 'facial_recognition' : 0, 'fingerprint_recognition' : 0, 'authorized' : 0}

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


        # Fingerprint Sensor connection
        self.uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
        self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)

        # This is the section of code which creates the main window

        self.frame_width = 1600
        self.frame_height = 600
        self.root.geometry('1600x600')
        self.root.configure()
        self.root.title('Biometric System')

        self.framerow1height = self.frame_height/10
        self.framerow2height = self.frame_height/1.1

        self.framerow_center = self.frame_width/3

        self.videocanvasheight = 375
        self.videocanvaswidth = 500

        ##################################################### CC #####################################################
        w = self.framerow_center / 5

        self.lbl_card_info = Label(self.root, text='Card Info', font=(
            'arial', 20, 'normal')).place(x=w, y=self.framerow1height)

        self.lbl_card_name = Label(self.root, text='',
                                   font=('arial', 12, 'normal'))
                                   
        self.lbl_card_name.place(x=w, y=self.framerow1height + 50)

        self.lbl_card_nif = Label(self.root, text='',
                                  font=('arial', 12, 'normal')).place(x=w, y=self.framerow1height + 100)

        self.lbl_card_gender = Label(self.root, text='', font=(
            'arial', 12, 'normal')).place(x=w, y=self.framerow1height + 150)

        self.lbl_card_rest = Label(self.root, text='', font=(
            'arial', 12, 'normal'))
            
        self.lbl_card_rest.place(x=self.framerow_center / 5, y=self.framerow1height + 100)

        self.btn_cc = Button(self.root, text='Read CC Card', font=(
            'arial', 12, 'normal'), command=self.read_cc).place(x=w, y=self.framerow1height + 150)
        
        
        ##################################################### FACIAL #####################################################
        
        self.create_image()
        w = self.framerow_center

        self.lbl_card_info = Label(self.root, text='Facial Recognition', font=(
            'arial', 20, 'normal')).place(x=w, y=self.framerow1height)

        self.btn_frcg = Button(self.root, text='Facial Recognition', font=(
            'arial', 12, 'normal'), command=self.read_facial)
        
        self.btn_frcg.place(x=w, y=self.framerow1height + self.videocanvasheight + 60)

        self.btn_frcg.config(state=tk.DISABLED)

        self.lbl_facial_rest = Label(self.root, text='', bg='#000000', font=('arial', 12, 'normal'))

        self.lbl_facial_rest.place(x=self.framerow_center + 250, y=self.framerow1height + self.videocanvasheight + 60)

        ##################################################### FINGERPRINT #####################################################

        w = self.framerow_center + self.videocanvaswidth + 100
        self.lbl_card_info = Label(self.root, text='Fingerprint Recognition', font=(
            'arial', 20, 'normal')).place(x=w, y=self.framerow1height)

        self.btn_fgp = Button(self.root, text='Read Fingerprint', font=(
            'arial', 12, 'normal'), command=self.read_fingerprint)
            
        self.btn_fgp.place(x=w, y=self.framerow1height + 50)

        self.btn_fgp.config(state=tk.DISABLED)

        self.lbl_fingerprint_rest = Label(self.root, text='', font=('arial', 12, 'normal'))

        self.lbl_fingerprint_rest.place(x=w + 150, y=self.framerow1height + 100)

        ##################################################### ENROLL #####################################################

        w = self.framerow_center

        self.btn_register = Button(self.root, text='Register', font=(
            'arial', 12, 'normal'), command=self.register).place(x=w, y=self.framerow2height)

        
        ############################################ ACCESS FEEDBACK #####################################################
        
        self.label_access_feedback = Label(self.root, text='ACCESS DENIED.', font=('arial', 16, 'normal'), bg='#FF0000')
                                   
        self.label_access_feedback.place(x=self.framerow_center / 5, y=self.framerow2height)


    def register(self):
        RegisterGUI(self.root)

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
        
        user_info = None
        card_read = False
        print("Reading Citizen card...")
        pkcs11 = self.verify_cc()
        print("Retrieving data from CC...")
        try:
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
            card_read= True
        except IndexError as e:
            self.lbl_card_rest.config(text="Invalid or non-existing Citizen Card.", bg='#FF0000')
            self.lbl_card_name.config(text='')
            self.lbl_fingerprint_rest.config(text='')
            print("Invalid or non-existing Citizen Card.")

        if card_read:
            print("USER INFO:")
            pprint(userInfo)

            # Check if user exists
            user_select_query = f"SELECT * FROM users WHERE cc_number = '{userInfo['SERIAL_NUMBER']}'"
            user_id = (userInfo['SERIAL_NUMBER'])

            self.cursor.execute(user_select_query)
            records = self.cursor.fetchall()
            print("Users match: ", self.cursor.rowcount)

            # Show users info
            self.lbl_card_name.config(text=f"{userInfo['GIVEN_NAME']} {userInfo['SURNAME']}\n{userInfo['SERIAL_NUMBER']}")

            # User exists. Allow read face and/or finger
            if self.cursor.rowcount >= 1:
                
                self.lbl_card_rest.config(text='User exists, proceed to biometric auth...', bg='#00FF00')

                user_data = records[0]
                
                self.user_id = user_data[0]
                self.user['SERIAL_NUMBER'] = user_data[0]
                self.user['GIVEN_NAME'] = user_data[1]
                self.user['SURNAME'] = user_data[2]
                self.user['BIO_DATA_LOCATION'] = user_data[3]
                self.user['HAS_FACIAL'] = user_data[4]
                self.user['HAS_FINGERPRINT'] = user_data[5]
                self.user['FINGERPRINT_ID_SENSOR'] = user_data[6]

                # Activate respective buttons
                print(f"has facial -> {self.user['HAS_FACIAL']}\nhas finger -> {self.user['HAS_FINGERPRINT']}")
                if self.user['HAS_FACIAL']:
                    self.btn_frcg.config(state=tk.NORMAL)
                if self.user['HAS_FINGERPRINT']:
                    self.btn_fgp.config(state=tk.NORMAL)
                
                # Card has been read
                self.state['card_read'] = 1
                self.state['facial_recognition'] = 0
                self.state['fingerprint_recognition'] = 0
                self.state['approved'] = 0
                
            else:
                self.lbl_card_rest.config(text="Access denied. User doesn't exist.", bg='#FF0000')
                self.lbl_fingerprint_rest.config(text='')
                self.lbl_facial_rest.config(text='')

                self.user['SERIAL_NUMBER'] = None
                self.user['GIVEN_NAME'] = None
                self.user['SURNAME'] = None
                self.user['BIO_DATA_LOCATION'] = None
                self.user['HAS_FACIAL'] = False
                self.user['HAS_FINGERPRINT'] = False
                self.user['FINGERPRINT_ID_SENSOR'] = None

                # Activate respective buttons
                print(f"has facial -> {self.user['HAS_FACIAL']}, {type(self.user['HAS_FACIAL'])}")
                if self.user['HAS_FACIAL']:
                    self.btn_frcg.config(state=tk.NORMAL)
                else:
                    self.btn_frcg.config(state=tk.DISABLED)
                if self.user['HAS_FINGERPRINT']:
                    self.btn_fgp.config(state=tk.NORMAL)
                else:
                    self.btn_fgp.config(state=tk.DISABLED) 
                
                # Card has not been read, reset values
                self.state['card_read'] = 0
                self.state['facial_recognition'] = 0
                self.state['fingerprint_recognition'] = 0
                self.state['approved'] = 0
            
            self.check_if_access_granted()

    # this is the function called when the button is clicked

    def read_fingerprint(self):
        match = False
        if self.get_fingerprint():
            print("Detected #", self.finger.finger_id, "with confidence", self.finger.confidence)
            finger_id = self.finger.finger_id
            # Read finger is the same id as users -> match
            if finger_id == self.user['FINGERPRINT_ID_SENSOR']:
                match = True
            # Finger doesnt match
            else:
                self.lbl_fingerprint_rest.config(text="Fingers don't match.", bg='#FF0000')
        else:
            print("Finger not found. Try again.")
            self.lbl_fingerprint_rest.config(text="Fingers don't match.", bg='#FF0000')
        
        if match:
            self.lbl_fingerprint_rest.config(text='Fingerprint read OK.', bg='#00FF00')
            self.state['fingerprint_recognition'] = 1
        else:
            self.state['fingerprint_recognition'] = 0
        
        self.check_if_access_granted()

    def create_image(self, file=""):
        # First, we create a canvas to put the picture on
        Video_Feed = Canvas(
            self.root, height=self.videocanvasheight, width=self.videocanvaswidth, bg="white")
        # Then, we actually create the image file to use (it has to be a *.gif)
        # <-- you will have to copy-paste the filepath here, for example 'C:\Desktop\pic.gif'
        self.picture_file = PhotoImage(file=file)
        # Finally, we create the image on the canvas and then place it onto the main window
        Video_Feed.create_image(500, 0, anchor=NE, image=self.picture_file)
        Video_Feed.place(x=self.framerow_center, y=self.framerow1height + 50)

    # this is the function called when the button is clicked
    def read_facial(self, user_id=5):
        
        user_encodings = np.load(os.path.join(os.getcwd(), f"../backend/{self.user['BIO_DATA_LOCATION']}/{self.user_id}_facial_features.npy"))

        known_face_encodings = [user_encodings]
        known_face_names = [self.user['SERIAL_NUMBER']]
        
        video_capture = cv2.VideoCapture(0)

        face_locations = []
        face_encodings = []
        face_names = []
        process_this_frame = True
        
        while True:
            match = False
            ret, frame = video_capture.read()

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            rgb_small_frame = small_frame[:, :, ::-1]

            if process_this_frame:
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                face_names = []
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    name = "Unknown"

            
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]
                        match = True
                        break

                    face_names.append(name)

                if match:
                    break

            process_this_frame = not process_this_frame
            # Caixa
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            cv2.imshow('Video', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        img_dir = os.path.join(os.getcwd(), f'../img/{self.user_id}_match_temp.png')
        cv2.imwrite(img_dir, frame)
        self.create_image(img_dir)

        print(f"facial rec -> {self.state['facial_recognition']}")

        if match:
            self.lbl_facial_rest.config(text = 'Facial recognition passed!', bg = '#00FF00')
            self.state['facial_recognition'] = 1
        else:
            self.lbl_facial_rest.config(text = 'Facial recognition failed!', bg = '#FF0000')
            self.state['facial_recognition'] = 0
        
        video_capture.release()
        cv2.destroyAllWindows()

        self.check_if_access_granted()

    def get_fingerprint(self):
        print("Waiting for image...")
        while self.finger.get_image() != adafruit_fingerprint.OK:
            pass
        print("Templating...")
        if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
            return False
        print("Searching...")
        if self.finger.finger_search() != adafruit_fingerprint.OK:
            return False
        return True

    def check_if_access_granted(self):
        bio_count = 0
        if self.user['HAS_FACIAL']:
            bio_count += 1
        if self.user['HAS_FINGERPRINT']:
            bio_count += 1
        if self.state['card_read'] + self.state['fingerprint_recognition'] + self.state['facial_recognition'] >= bio_count + 1:
            print("Access is granted.")
            self.label_access_feedback.config(text='ACCESS GRANTED.', bg='#00FF00')
            return True
        else:
            print("Access is denied.")
            self.label_access_feedback.config(text='ACCESS DENIED.', bg='#FF0000')
            return False

if __name__ == "__main__":
    gui = GUI()
    gui.root.mainloop()
