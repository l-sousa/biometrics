from abc import abstractmethod
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

class GUI:

    def __init__(self) -> None:
        self.root = Tk()

        # This is the section of code which creates the main window
        self.root.geometry('850x570')
        self.root.configure(background='#838B8B')
        self.root.title('Biometric System')

        # This is the section of code which creates a button
        self.btn_cc = Button(self.root, text='Read CC Card', bg='#838B8B', font=(
            'arial', 12, 'normal'), command=self.read_cc).place(x=122, y=300)

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
        self.lbl_card_name = Label(self.root, text='', bg='#838B8B',
                                   font=('arial', 12, 'normal')).place(x=52, y=107)

        # This is the section of code which creates the a label
        self.lbl_card_nif = Label(self.root, text='', bg='#838B8B',
                                  font=('arial', 12, 'normal')).place(x=52, y=137)

        # This is the section of code which creates the a label
        self.lbl_card_gender = Label(self.root, text='', bg='#838B8B', font=(
            'arial', 12, 'normal')).place(x=52, y=167)

        # This is the section of code which creates the a label
        self.lbl_card_rest = Label(self.root, text='(...)', bg='#838B8B', font=(
            'arial', 12, 'normal')).place(x=52, y=197)

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
                    cert = x509.load_der_x509_certificate(cert_bytes, backend=default_backend())
                    userInfo['GIVEN_NAME'] = cert.subject.get_attributes_for_oid(x509.NameOID.GIVEN_NAME)[0].value
                    userInfo['SURNAME'] = cert.subject.get_attributes_for_oid(x509.NameOID.SURNAME)[0].value
                    userInfo['SERIAL_NUMBER'] = cert.subject.get_attributes_for_oid(x509.NameOID.SERIAL_NUMBER)[0].value
            
        private_key = session.findObjects([
            (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
            (PyKCS11.CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')
            ])[0]

        print("USER INFO:")
        pprint(userInfo)
        self.lbl_card_name = Label(self.root, text= userInfo['GIVEN_NAME'] + " " + userInfo['SURNAME'] + "\n" + userInfo['SERIAL_NUMBER'], bg='#838B8B',
                                   font=('arial', 12, 'normal')).place(x=52, y=107)
        
        return cert_bytes, userInfo, private_key, session

     

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
            cv2.imshow('image')
            if cv2.waitKey(1) & 0xFF == ord('s'):
                image = cv2.resize(image, (0, 0), fx=0.6, fy=0.6)
                image = cv2.resize(image, (400, 400))

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
