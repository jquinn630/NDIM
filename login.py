#Login Screen for NDIM
# John Quinn and Robert Wirthman

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ndim import *
import json
import requests

SERVER_ADDR = r'http://student03.cse.nd.edu:40004/'

#class to create login window
class login(QDialog):
	def __init__(self, uname="default", parent=None):
		super(login, self).__init__(parent)
		#basic setup
		self.setWindowTitle("NDIM Login")
		layout = QVBoxLayout()

		#login existing user portion layout
		self.nameLabel=QLabel("Username:")
		self.passLabel=QLabel("Password:")
		self.nameEdit=QLineEdit()
		self.passEdit=QLineEdit()
		self.passEdit.setEchoMode(QLineEdit.Password)
		self.verifyButton=QPushButton("Login")
		layout.addWidget(self.nameLabel)
		layout.addWidget(self.nameEdit)
		layout.addWidget(self.passLabel)
		layout.addWidget(self.passEdit)
		layout.addWidget(self.verifyButton)
		self.connect(self.verifyButton, SIGNAL("pressed()"), self.checkForLogin)

		#create new user portion layour
		self.newnameLabel=QLabel("New User:")
		self.newpassLabel=QLabel("Choose a Password:\n Must have 3 of the following. \n 1)lowercase letters\n 2)uppercase letters\n 3)numbers\n4)special characters")
		self.newnameEdit=QLineEdit()
		self.newpassEdit=QLineEdit()
		self.createButton=QPushButton("Create New Account")
		layout.addWidget(self.newnameLabel)
		layout.addWidget(self.newnameEdit)
		layout.addWidget(self.newpassLabel)
		layout.addWidget(self.newpassEdit)
		layout.addWidget(self.createButton)
		self.connect(self.createButton, SIGNAL("pressed()"), self.createNewUser)

		#set main widget
		self.setLayout(layout)

	def checkForLogin(self):
		uname=self.nameEdit.text()
		uname=str(uname).strip()
		password={}
		password['password']=str(self.passEdit.text())
		#send a request to the server to verify the username and pass
		r = requests.post(SERVER_ADDR+'users/'+uname, data=json.dumps(password))
		response=json.loads(r.content)
		#if the response checked out, log the user in.  otherwise give an error message
		if response['result']=='success':
			self.logUserIn()
		else:
			self.feedback=QMessageBox()
			self.feedback.setText(response['message'])
			self.feedback.show()

	def logUserIn(self):
		#create a buddylist window for the user and hide this first login window.  The buddylist window will become the main window
		self.mainBuddyList=buddyList(self.nameEdit.text())
		self.mainBuddyList.show()
		
		#request to change status to online
		logoff={}
		logoff['status']='online'
		r=requests.put(SERVER_ADDR+'statuses/'+str(self.nameEdit.text()).strip(), data=json.dumps(logoff))
		response=json.loads(r.content)

		#handle error
		if response['result']=='failure':
			self.message.setText('Log In Failed.')
			self.message.exec_()

		self.hide()

	def createNewUser(self):
		#get the data for the new user
		userdata={}
		userdata['password']=str(self.newpassEdit.text())
		uname=self.newnameEdit.text()
		uname=str(uname).strip()
		userdata['username']=uname
		#send new user data to the server for creation
		r = requests.post(SERVER_ADDR+'users/', data=json.dumps(userdata))
		response=json.loads(r.content)
		self.feedback=QMessageBox()
		#tell the user whether creation was successful or not
		if response['result']=='success':
			self.feedback.setText('Account created successfully.')
		else:
			self.feedback.setText(response['message'])
		self.feedback.show()


#initialize the application, main function for NDIM
app = QApplication(sys.argv)
form = login()
form.show()
sys.exit(app.exec_())
