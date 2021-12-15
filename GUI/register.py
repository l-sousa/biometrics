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
import face_recognition
import numpy as np
from PIL import ImageTk

import time
import serial
import adafruit_fingerprint


class RegisterGUI:

    def __init__(self, main_gui_root) -> None:

        # Current user and current registration state variables
        self.user_id = None
        self.user = {
            'SERIAL_NUMBER' : None,
            'GIVEN_NAME' : None,
            'SURNAME' : None,
            'FINGER_ID' : None
        }

        self.state = {'card_read' : 0, 'facial_recognition' : 0, 'fingerprint_recognition' : 0}

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

        # Tkinter stuff
        self.my_w_child = tk.Toplevel(main_gui_root)
        self.my_w_child.geometry("1600x600")
        self.my_w_child.title('Register')
        my_str1 = tk.StringVar()
        b2 = tk.Button(self.my_w_child, text='Quit',
                       command=self.my_w_child.destroy)
        b2.grid(row=2, column=2)

        # This is the section of code which creates the main window
        
        self.frame_width = 1600
        self.frame_height = 600

        self.framerow1height = self.frame_height/10
        self.framerow2height = self.frame_height/1.1

        self.framerow_center = self.frame_width/3

        self.videocanvasheight = 375
        self.videocanvaswidth = 500

        ##################################################### CC #####################################################
        w = self.framerow_center / 5

        self.lbl_card_info = Label(self.my_w_child, text='Card Info', font=(
            'arial', 20, 'normal')).place(x=w, y=self.framerow1height)

        self.lbl_card_name = Label(self.my_w_child, text='',
                                   font=('arial', 12, 'normal'))
                                   
        self.lbl_card_name.place(x=w, y=self.framerow1height + 50)

        self.lbl_card_nif = Label(self.my_w_child, text='',
                                  font=('arial', 12, 'normal')).place(x=w, y=self.framerow1height + 100)

        self.lbl_card_gender = Label(self.my_w_child, text='', font=(
            'arial', 12, 'normal')).place(x=w, y=self.framerow1height + 150)

        self.lbl_card_rest = Label(self.my_w_child, text='', font=(
            'arial', 12, 'normal'))
            
        self.lbl_card_rest.place(x=self.framerow_center / 5, y=self.framerow1height + 100)

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

        self.lbl_facial_rest = Label(self.my_w_child, text='', font=('arial', 12, 'normal'))

        self.lbl_facial_rest.place(x=self.framerow_center + 250, y=self.framerow1height + self.videocanvasheight + 60)

        ##################################################### FINGERPRINT #####################################################

        w = self.framerow_center + self.videocanvaswidth + 100
        self.lbl_card_info = Label(self.my_w_child, text='Read Fingerprint', font=(
            'arial', 20, 'normal')).place(x=w, y=self.framerow1height)

        self.btn_fgp = Button(self.my_w_child, text='Read Fingerprint', font=(
            'arial', 12, 'normal'), command=self.read_fingerprint)
        
        self.lbl_fingerprint_info = Label(self.my_w_child, text='Place yout finger when the light turns on.\nRemove your finger when the light turns off.',
                                   font=('arial', 12, 'normal'))
                                   
        self.lbl_fingerprint_info.place(x=w, y=self.framerow1height + 50)        

        self.btn_fgp.place(x=w, y=self.framerow1height + 100)

        self.btn_fgp.config(state=tk.DISABLED)

        self.lbl_fingerprint_rest = Label(self.my_w_child, text='', font=('arial', 12, 'normal'))

        self.lbl_fingerprint_rest.place(x=w + 150, y=self.framerow1height + 100)

        ##################################################### ENROLL #####################################################

        w = self.framerow_center

        self.btn_enroll = Button(self.my_w_child, text='Enroll', font=(
            'arial', 12, 'normal'), command=self.enroll).place(x=w, y=self.framerow2height)

        self.lbl_enroll_feedback = Label(self.my_w_child, text='', font=('arial', 12, 'normal'))

        self.lbl_enroll_feedback.place(x=w+80, y=self.framerow2height)

    def enroll(self):
        if self.state['card_read'] == 1:
            if self.state['facial_recognition'] + self.state['fingerprint_recognition'] > 0:
                
                # Insert new user
                
                # If facial rec -> move images to bio_images
                if self.state['facial_recognition'] == 1:
                    current_directory = os.getcwd()
                    final_directory = os.path.join(current_directory, f'../backend/bio_data/{self.user_id}')
                    temp_directory = os.path.join(current_directory, '../img')
                    print(final_directory)
                    if not os.path.exists(final_directory):
                        os.makedirs(final_directory)
                    #for i in range(5):
                    os.rename(f'{temp_directory}/{self.user_id}/{self.user_id}_facial_features.npy', f'{final_directory}/{self.user_id}_facial_features.npy')

                # Insert user in databse
                user_insert_query = """ INSERT INTO users
                               (cc_number, given_name, surname, bio_data_location, has_facial, has_fingerprint, fingerprint_id_sensor) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
                user = (self.user['SERIAL_NUMBER'], self.user['GIVEN_NAME'], self.user['SURNAME'], "bio_data/" + self.user['SERIAL_NUMBER'],self.state['facial_recognition'],self.state['fingerprint_recognition'], self.user['FINGER_ID'])
                self.cursor.execute(user_insert_query, user)
                
                print("Enrolled.")
                self.lbl_enroll_feedback.config(text="Success.", bg='#00FF00')
                
                self.my_w_child.destroy()
                
            else:
                print("Can't enroll. Need at least 1 biometric authentication factor.")
                self.lbl_enroll_feedback.config(text="Error. Need at least 1 biometric authentication factor.", bg='#FF0000')
        else:
            print("Can't enroll. Card not read.")
            self.lbl_enroll_feedback.config(text="Error. Card not read.", bg='#FF0000')

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

        print("Reading Citizen card...")
        self.lbl_card_rest.config(text='Reading Citizen card...', bg='#FFFF00')
        pkcs11 = self.verify_cc()
        print("Retrieving data from CC...")
        self.lbl_card_rest.config(text='Retrieving data from CC...', bg='#FFFF00')
        user_info = None
        card_read = False
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
            card_read = True
        except IndexError as e:
            self.lbl_card_rest.config(text="Invalid or non-existing Citizen Card.", bg='#FF0000')
            self.lbl_card_name.config(text='')
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
            
            # If user already exists in the DB, he may not enroll
            if self.cursor.rowcount > 0:
                self.lbl_card_rest.config(text='User already exists.', bg='#FF0000')
                print("User already exists.")

                # Update current user variables
                self.user_id = None
                self.user['SERIAL_NUMBER'] = None
                self.user['GIVEN_NAME'] = None
                self.user['SURNAME'] = None

                # Update current registration state
                self.state['card_read'] = 0
                self.state['facial_recognition'] = 0
                self.state['fingerprint_recognition'] = 0

                # Disallow biometric registration
                self.btn_frcg.config(state=tk.DISABLED)
                self.btn_fgp.config(state=tk.DISABLED)

            # If user doesn't exist in the DB, he may enroll
            else:
                self.lbl_card_rest.config(text="Card read. Proceed...", bg='#00FF00')
                print("Card read. Proceed...")

                # Update current user variables
                self.user_id = userInfo['SERIAL_NUMBER']
                self.user['SERIAL_NUMBER'] = userInfo['SERIAL_NUMBER']
                self.user['GIVEN_NAME'] = userInfo['GIVEN_NAME']
                self.user['SURNAME'] = userInfo['SURNAME']

                # Update current registration state
                self.state['card_read'] = 1
                self.state['facial_recognition'] = 0
                self.state['fingerprint_recognition'] = 0

                # Allow biometric registration
                self.btn_frcg.config(state=tk.NORMAL)
                self.btn_fgp.config(state=tk.NORMAL)


    def read_fingerprint(self):
        finger_id = None
        self.state['fingerprint_recognition'] = 0
        if self.finger.read_templates() != adafruit_fingerprint.OK:
            raise RuntimeError("Failed to read templates")

        print(self.finger.templates)
        print(type(self.finger.templates))

        for i in range(1000):
            if i not in self.finger.templates:
                finger_id = i
                print(f"Break at {i}")
                break
        if finger_id != None:
            status, response = self.enroll_finger(finger_id)
            if status:
                self.lbl_fingerprint_rest.config(text='Fingerprint read OK.', bg='#00FF00')
                # Sensor registred the finger, add it to state
                self.user['FINGER_ID'] = finger_id
                self.state['fingerprint_recognition'] = 1
                print(f"Fingerprint saved to sensor with id #{finger_id}")
                print(f"Fingerprint rec state -> {self.state['fingerprint_recognition']}") 
                if self.finger.read_templates() != adafruit_fingerprint.OK:
                    raise RuntimeError("Failed to read templates")
                print("Fingerprint templates: ", self.finger.templates)
                if self.finger.count_templates() != adafruit_fingerprint.OK:
                    raise RuntimeError("Failed to read templates")
                print("Number of templates found: ",self.finger.template_count)
            else:
                self.lbl_fingerprint_rest.config(text=f'{response}', bg='#FF0000')
        else:
            self.lbl_fingerprint_rest.config(text='Fingerprint id maximum capacity reached!', bg='#FF0000')
            print("Fingerprint id maximum capacity reached!")


    def create_image(self, file=""):
        # First, we create a canvas to put the picture on
        Video_Feed = Canvas(
            self.my_w_child, height=self.videocanvasheight, width=self.videocanvaswidth, bg="white")
        self.picture_file = PhotoImage(file=file)
        Video_Feed.create_image(500, 0, anchor=NE, image=self.picture_file)
        Video_Feed.place(x=self.framerow_center, y=self.framerow1height + 50)

    # this is the function called when the button is clicked
    def read_facial(self, user_id=5):
        camera = cv2.VideoCapture(0)
        #counter = 0
        find = False
        process_this_frame = True
        while True:
            return_value, image = camera.read()
            small_image = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
            
            if process_this_frame:
                user_encodings_list = face_recognition.face_encodings(np.array(PIL.Image.fromarray(small_image)))

                if user_encodings_list:
                    if not os.path.exists(os.path.join(os.getcwd(), f'../img/{self.user_id}')):
                        os.makedirs(os.path.join(os.getcwd(), f'../img/{self.user_id}'))
                    np.save(os.path.join(os.getcwd(), f'../img/{self.user_id}/{self.user_id}_facial_features.npy'),user_encodings_list[0])
                    image = cv2.resize(image, (0, 0), fx=0.8, fy=0.8)
                    img_dir = os.path.join(os.getcwd(), f'../img/{self.user_id}_0.png')
                    cv2.imwrite(img_dir, image)
                    self.create_image(img_dir)
                    find = True
                    break
            
            process_this_frame = not process_this_frame
            cv2.imshow('image',image)
                   
            if cv2.waitKey(1) & 0xFF == ord('s'):
                image = cv2.resize(image, (0, 0), fx=0.8, fy=0.8)
                img_dir = os.path.join(os.getcwd(), f'../img/{self.user_id}_0.png')
                cv2.imwrite(img_dir, image)
                self.create_image(img_dir)
                break
        
        if find:
            self.lbl_facial_rest.config(text = 'Facial recognition OK', bg = '#00FF00')
            self.state['facial_recognition'] = 1
        else:
            self.lbl_facial_rest.config(text = 'Facial recognition failed. Try again.', bg = '#FF0000')
            self.state['facial_recognition'] = 0

        camera.release()
        cv2.destroyAllWindows()

    def enroll_finger(self,location):
        """Take a 2 finger images and template it, then store in 'location'"""
        #images = []
        for fingerimg in range(1, 3):
            if fingerimg == 1:
                print("Place finger on sensor...", end="", flush=True)
            else:
                print("Place same finger again...", end="", flush=True)

            while True:
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    print("Image taken")
                    break
                if i == adafruit_fingerprint.NOFINGER:
                    print(".", end="", flush=True)
                elif i == adafruit_fingerprint.IMAGEFAIL:
                    print("Imaging error")
                    return False, 'Error. Try again.'
                else:
                    print("Other error")
                    return False, 'Error. Try again.'

            print("Templating...", end="", flush=True)
            i = self.finger.image_2_tz(fingerimg)
            if i == adafruit_fingerprint.OK:
                print("Templated")
            else:
                if i == adafruit_fingerprint.IMAGEMESS:
                    print("Image too messy")
                    return False, 'Image too messy. Try again.'
                elif i == adafruit_fingerprint.FEATUREFAIL:
                    print("Could not identify features")
                    return False, 'Could not identify features. Try again.'
                elif i == adafruit_fingerprint.INVALIDIMAGE:
                    print("Image invalid")
                    return False, 'Invalid image. Try again.'
                else:
                    print("Other error")
                    return False, 'Error. Try again.'
                return False

            if fingerimg == 1:
                print("Remove finger")
                time.sleep(1)
                while i != adafruit_fingerprint.NOFINGER:
                    i = self.finger.get_image()

        print("Creating model...", end="", flush=True)
        i = self.finger.create_model()
        if i == adafruit_fingerprint.OK:
            print("Created")
        else:
            if i == adafruit_fingerprint.ENROLLMISMATCH:
                print("Prints did not match")
                return False, 'Prints did not match. Try again.'
            else:
                print("Other error")
                return False, 'Error. Try again.'

        print("Storing model #%d..." % location, end="", flush=True)
        i = self.finger.store_model(location)
        if i == adafruit_fingerprint.OK:
            print("Stored")
        else:
            if i == adafruit_fingerprint.BADLOCATION:
                print("Bad storage location")
                return False, 'Storage error. Try again.'
            elif i == adafruit_fingerprint.FLASHERR:
                print("Flash storage error")
                return False, 'Storage error. Try again.'
            else:
                print("Other error")
                return False, 'Other error. Try again.'

        return True, 'OK'  
        

if __name__ == "__main__":
    gui = RegisterGUI()
    gui.root.mainloop()
