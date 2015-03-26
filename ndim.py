# GUI portion of NDIM
# John Quinn and Robert Wirthman
# CSE30332 Final Project

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import json
import requests
import cgi
from encryptor import Encryptor

encryptor = Encryptor()

SERVER_ADDR = r'http://student03.cse.nd.edu:40004/'

#class to create main window
class buddyList(QMainWindow):
	def __init__(self, uname="default", parent=None):
		super(buddyList, self).__init__(parent)
		self.uname=str(uname).strip()
		#set title
		self.setWindowTitle("ND IM")

		#setup member data to keep track of conversations
		self.convos={}
		self.convoIds=[]

		#setup a dialog for future use
		self.theDialog=QDialog()
		self.isGroupDialog=False

		#create a layout to add subwwidgets
		layout = QVBoxLayout()

		#setup the menues
		#add the buddy management menu
		self.buddyMenu = self.menuBar().addMenu("&Buddy")
		addBuddy = QAction("&Add Buddy", self)
		self.buddyMenu.addAction(addBuddy)
		deleteBuddy = QAction("&Remove Buddy", self)
		self.buddyMenu.addAction(deleteBuddy)
		blockBuddy = QAction("&Block Buddy", self)
		self.buddyMenu.addAction(blockBuddy)
		unblockBuddy=QAction("&Unblock Buddy", self)
		self.buddyMenu.addAction(unblockBuddy)
		viewRequests=QAction("&View Requests", self)
		self.buddyMenu.addAction(viewRequests)
		#add the converstaion menu
		self.convoMenu = self.menuBar().addMenu("&Chat")
		groupConvo = QAction("&Group Conversation", self)
		self.convoMenu.addAction(groupConvo)
		#add the logout menu
		self.logoutMenu=self.menuBar().addMenu("&Logout")
		logoutAction=QAction("&Logout", self)
		self.logoutMenu.addAction(logoutAction)
		#connect the menu actions to the appropriate functions
		self.connect(groupConvo, SIGNAL("triggered()"), self.groupConSetup)
		self.connect(addBuddy, SIGNAL("triggered()"), self.addBuddyWindow)
		self.connect(deleteBuddy, SIGNAL("triggered()"), self.deleteBuddyWindow)
		self.connect(blockBuddy, SIGNAL("triggered()"), self.blockBuddyWindow)
		self.connect(unblockBuddy, SIGNAL("triggered()"), self.unblockBuddyWindow)
		self.connect(viewRequests, SIGNAL("triggered()"), self.viewRequestsWindow)
		self.connect(logoutAction, SIGNAL("triggered()"), self.logoutUser)

		#setup a label to see who is online
		self.statusLabel=QLabel()
		layout.addWidget(self.statusLabel)

		#label for buddy list
		self.buddyLabel=QLabel("All Buddies - double click to chat")
		layout.addWidget(self.buddyLabel)

		#add the buddy list widget
		self.friends=QListWidget()
		self.friends.setFixedHeight(450)
		self.friends.setSortingEnabled(True)
		# get friends from server
		self.loadBuddies(self.friends, ['friends'])
		layout.addWidget(self.friends)
		self.updateStatus()
		self.connect(self.friends, SIGNAL("itemDoubleClicked(QListWidgetItem*)"), self.startGroupChat)

		#add layout to a widget
		self.mainWidget=QWidget()
		self.mainWidget.setMouseTracking(True)
		self.mainWidget.setLayout(layout)

		#setup timer to check for new messages.
		self.timer = QTimer()
		self.timer.timeout.connect(self.checkForIncomingMessages)
		self.timer.start(500)

		#setup message for modal feedback
		self.message=QMessageBox()

		#load emoticon images.
		self.smiley=QImage("smile.png")

		#set main widget
		self.setCentralWidget(self.mainWidget)

	def loadBuddies(self, item, attr):
		#function to populate friends list.
		#clear whatever was previously in the list
		item.clear()
		#get the friends of the user from the server
		r = requests.get(SERVER_ADDR+'friends/'+self.uname)
		response=json.loads(r.content)

		#check if successful
		if response['result']=='success':
			for i in response['usernames']:
				#only add the friends that meet the specified attributes (ie friends, blocked, friender , etc.)
				if i[1] in attr:
					item.addItem(i[0])
		#error message if not successful
		else:
			self.message.setText(response['message'])
			self.message.exec_()

	def addBuddyWindow(self):
		#add stuff to send data to server here
		#setup add buddylayout
		layout = QVBoxLayout()
		instructionLabel=QLabel("Enter a buddy name:")
		layout.addWidget(instructionLabel)

		# text for buddy name and submit button
		self.buddyText=QLineEdit()
		layout.addWidget(self.buddyText)
		self.submitButton=QPushButton("Add")
		layout.addWidget(self.submitButton)

		#signal to add the buddy
		self.theDialog = QDialog()
		self.theDialog.setLayout(layout)
		self.connect(self.submitButton, SIGNAL("pressed()"), self.addBuddy)
		self.theDialog.exec_()


	def addBuddy(self):
		if str(self.buddyText.text())=='':
			#if the user didn't enter anything in the field supply and error
			self.message.setText("Please enter a buddy name")
			self.message.exec_()
		else:
			#prepare data to send to server
			userfriend={}
			userfriend['username']=str(self.uname).strip()
			userfriend['friendname']=str(self.buddyText.text()).strip()
			#try to add friend on server
			r = requests.post(SERVER_ADDR+'friends/', data=json.dumps(userfriend))
			response=json.loads(r.content)
			#tell the user what happened and update data
			if response['result']=='success':
				self.message.setText("Buddy request sent.")
				self.message.exec_()
			else:
				self.message.setText(response['message'])
				self.message.exec_()
			self.theDialog.done(1)
			self.loadBuddies(self.friends, ['friends'])

	def deleteBuddyWindow(self):
		#setup delete buddy layout
		layout = QVBoxLayout()
		instructionLabel=QLabel("Choose a buddy name:")
		layout.addWidget(instructionLabel)

		# drop down menu for buddy selection and submit button
		self.buddySelect=QComboBox()
		#get buddies from server
		self.loadBuddies(self.buddySelect, ['friends'])
		layout.addWidget(self.buddySelect)
		self.removeButton=QPushButton("Remove")
		layout.addWidget(self.removeButton)

		#signal to remove the buddy
		self.theDialog = QDialog()
		self.theDialog.setLayout(layout)
		self.connect(self.removeButton, SIGNAL("pressed()"), self.deleteBuddy)
		self.theDialog.exec_()

	def deleteBuddy(self):
		#if the user didn't pick a buddy, give them an error
		if str(self.buddySelect.currentText())=='':
			self.message.setText("Please choose a buddy name")
			self.message.exec_()
		else:
			#prepare data
			userfriend={}
			userfriend['username']=str(self.uname).strip()
			userfriend['friendname']=str(self.buddySelect.currentText()).strip()
			userfriend['action']='unfriend'
			#attempt to remove buddy on server
			r = requests.put(SERVER_ADDR+'friends/', data=json.dumps(userfriend))
			response=json.loads(r.content)
			#notify the user of what happened
			if response['result']=='success':
				self.message.setText("Buddy successfully removed.")
				self.message.exec_()
			else:
				self.message.setText(response['message'])
				self.message.exec_()
			self.theDialog.done(1)
			self.loadBuddies(self.friends, ['friends'])

	def blockBuddyWindow(self):
		#setup block buddy window
		layout = QVBoxLayout()
		instructionLabel=QLabel("Choose a buddy name:")
		layout.addWidget(instructionLabel)

		# drop down menu for buddy selection and submit button
		self.buddySelect=QComboBox()
		#get from server
		self.loadBuddies(self.buddySelect, ['friends', 'friender'])
		layout.addWidget(self.buddySelect)
		self.blockButton=QPushButton("Block")
		layout.addWidget(self.blockButton)

		#signal to block the buddy
		self.theDialog = QDialog()
		self.theDialog.setLayout(layout)
		self.connect(self.blockButton, SIGNAL("pressed()"), self.blockBuddy)
		self.theDialog.exec_()

	def blockBuddy(self):
		#setup data to send to server
		userfriend={}
		userfriend['username']=str(self.uname).strip()
		userfriend['friendname']=str(self.buddySelect.currentText()).strip()
		userfriend['action']='block'
		#tell the server to attempt to block the buddy
		r = requests.put(SERVER_ADDR+'friends/', data=json.dumps(userfriend))
		response=json.loads(r.content)
		#tell the user what happened
		if response['result']=='success':
			self.message.setText("Buddy blocked.")
			self.message.exec_()
		else:
			self.message.setText(response['message'])
			self.message.exec_()
		self.theDialog.done(1)
		self.loadBuddies(self.friends, ['friends'])

	def unblockBuddyWindow(self):
		#setup unblock buddylayout
		layout = QVBoxLayout()
		instructionLabel=QLabel("Choose a buddy name:")
		layout.addWidget(instructionLabel)
		# drop down menu to pick buddy and submit button
		self.buddySelect=QComboBox()
		#get from server
		self.loadBuddies(self.buddySelect, ['blocker'])
		layout.addWidget(self.buddySelect)
		self.unblockButton=QPushButton("Unblock")
		layout.addWidget(self.unblockButton)
		#signal to unblock the buddy
		self.theDialog = QDialog()
		self.theDialog.setLayout(layout)
		self.connect(self.unblockButton, SIGNAL("pressed()"), self.unblockBuddy)
		self.theDialog.exec_()

	def unblockBuddy(self):
		#prepare data to send to server
		userfriend={}
		userfriend['username']=str(self.uname).strip()
		userfriend['friendname']=str(self.buddySelect.currentText()).strip()
		userfriend['action']='unblock'
		#attempt to unblock buddy on server
		r = requests.put(SERVER_ADDR+'friends/', data=json.dumps(userfriend))
		response=json.loads(r.content)
		#tell the user what happened
		if response['result']=='success':
			self.message.setText("Buddy unblocked.")
			self.message.exec_()
		else:
			self.message.setText(response['message'])
			self.message.exec_()
		self.theDialog.done(1)
		self.loadBuddies(self.friends, ['friends'])

	def viewRequestsWindow(self):
		#setup some widgets so that all the user requests are displayed.  One section of the
		# window will be outgoing requests, the other incoming requests
		requestLabel=QLabel("You currently have friend requests from:")
		self.requestsList=QListWidget()
		self.requestsList.setFixedHeight(200)
		self.requestsList.setSortingEnabled(True)
		self.loadBuddies(self.requestsList, ['friended'])
		requestedLabel=QLabel("You have pending requets sent to:")
		self.requestedList=QListWidget()
		self.requestedList.setFixedHeight(200)
		self.requestedList.setSortingEnabled(True)
		self.loadBuddies(self.requestedList, ['friender'])

		#setup buttons to allow the user to manage the requests
		self.cancelRequestButton=QPushButton('Cancel Request')
		self.acceptRequestButton=QPushButton('Accept Request')
		self.rejectRequestButton=QPushButton('Reject Request')

		#setup a layout for the request management window
		layout = QVBoxLayout()
		layout.addWidget(requestLabel)
		layout.addWidget(self.requestsList)
		layout.addWidget(self.acceptRequestButton)
		layout.addWidget(self.rejectRequestButton)
		layout.addWidget(requestedLabel)
		layout.addWidget(self.requestedList)
		layout.addWidget(self.cancelRequestButton)

		#connect the buttons to the appropriate actions
		self.connect(self.cancelRequestButton, SIGNAL('pressed()'), self.cancelRequest)
		self.connect(self.acceptRequestButton, SIGNAL('pressed()'), self.acceptRequest)
		self.connect(self.rejectRequestButton, SIGNAL('pressed()'), self.rejectRequest)

		#show the dialog to the user
		self.theDialog = QDialog()
		self.theDialog.setLayout(layout)
		self.theDialog.exec_()

	def acceptRequest(self):
		#make sure user actually selected a buddy before hitting the button, give them an error message if necessary
		if str(self.requestsList.currentItem().text()).strip()=='':
			self.message.setText('Please select a buddy from the list.')
			self.message.exec_()
			return
		#setup data to send to server
		userfriend={}
		userfriend['username']=str(self.uname).strip()
		userfriend['friendname']=str(self.requestsList.currentItem().text()).strip()
		userfriend['action']='friend'
		#attempt to accept friend request on server
		r = requests.put(SERVER_ADDR+'friends/', data=json.dumps(userfriend))
		response=json.loads(r.content)
		#tell the user what happened
		if response['result']=='success':
			self.message.setText("Request accepted.")
			self.message.exec_()
		else:
			self.message.setText(response['message'])
			self.message.exec_()
		self.theDialog.done(1)
		self.loadBuddies(self.friends, ['friends'])

	def rejectRequest(self):
		#make sure user actually selected a buddy before hitting the button, give them an error message if necessary
		if str(self.requestsList.currentItem().text()).strip()=='':
			self.message.setText('Please select a buddy from the list.')
			self.message.exec_()
			return
		#setup data to send to server
		userfriend={}
		userfriend['username']=str(self.uname).strip()
		userfriend['friendname']=str(self.requestsList.currentItem().text()).strip()
		userfriend['action']='unfriend'
		#attempt to reject a friend request on the server
		r = requests.put(SERVER_ADDR+'friends/', data=json.dumps(userfriend))
		response=json.loads(r.content)
		#check what happened and tell user
		if response['result']=='success':
			self.message.setText("Request rejected.")
			self.message.exec_()
		else:
			self.message.setText(response['message'])
			self.message.exec_()
		self.theDialog.done(1)
		self.loadBuddies(self.friends, ['friends'])

	def cancelRequest(self):
		#make sure user actually selected a buddy before hitting the button, give them an error message if necessary
		if str(self.requestedList.currentItem().text()).strip()=='':
			self.message.setText('Please select a buddy from the list.')
			self.message.exec_()
			return
		#setup data to send to server
		userfriend={}
		userfriend['username']=str(self.uname).strip()
		userfriend['friendname']=str(self.requestedList.currentItem().text()).strip()
		userfriend['action']='unfriend'
		#attempt to cancel a friend request on the server
		r = requests.put(SERVER_ADDR+'friends/', data=json.dumps(userfriend))
		response=json.loads(r.content)
		#tell the user what happened
		if response['result']=='success':
			self.message.setText("Request canceled.")
			self.message.exec_()
		else:
			self.message.setText(response['message'])
			self.message.exec_()
		self.theDialog.done(1)
		self.loadBuddies(self.friends, ['friends'])


	def groupConSetup(self):
		#setup layout to start conversation, make suer the group dialog is turned on so that startGroupChat knows to check the appropriate widge
		self.isGroupDialog=True
		layout = QVBoxLayout()
		instructionLabel=QLabel("Choose a buddy name:")
		layout.addWidget(instructionLabel)

		#setup a combobox with all the user's current buddies
		self.buddySelect=QComboBox()
		self.loadBuddies(self.buddySelect, ['friends'])
		layout.addWidget(self.buddySelect)
		self.addButton=QPushButton("Add To Chat")
		layout.addWidget(self.addButton)

		#setup a list view that lists the buddies the user has already selected
		self.groupLabel=QLabel("Current Buddies:\n")
		layout.addWidget(self.groupLabel)
		self.groupBuddies=QListWidget()
		layout.addWidget(self.groupBuddies)
		self.startConvoButton=QPushButton("Start Chat")
		layout.addWidget(self.startConvoButton)

		#setup the dialog and its layout
		self.theDialog = QDialog()
		self.theDialog.setLayout(layout)
		#connect the buttons to the appropriate actions, to add the buddies to the list, and to start the group chat
		self.connect(self.addButton, SIGNAL("pressed()"), self.addGroupBuddy)
		self.connect(self.startConvoButton, SIGNAL("pressed()"), self.startGroupChat)
		self.theDialog.exec_()

	def addGroupBuddy(self):
		#add a buddy to the list of selected buddies
		self.groupBuddies.addItem(self.buddySelect.currentText())

	def startGroupChat(self):
		#setup data to send to the server to start the chat.
		#server requires list of buddies be represented as a literal string.
		selectedBuddies=''
		selectedBuddiesList=[]
		selectedBuddies='[' + self.uname

		#check whether the conversation was created from the groupConvoWindow dialog or by double clicking on a buddy
		# and handle appropriately.
		# if self.isGroupDialog is True, that means it was created from groupConvoWindow.  Otherwise, the convo must have been created by double clicking on a name in the buddy list.
		if self.isGroupDialog==True:
			for i in range(0,self.groupBuddies.count()):
				selectedBuddies= selectedBuddies+ ','+ str(self.groupBuddies.item(i).text()).strip()
				selectedBuddiesList.append(str(self.groupBuddies.item(i).text()).strip())
		else:
			selectedBuddies= selectedBuddies+ ','+ str(self.friends.currentItem().text()).strip()
			selectedBuddiesList.append(str(self.friends.currentItem().text()).strip())

		selectedBuddies=selectedBuddies+']'
		userdata={}
		userdata['usernames']=selectedBuddies
		#request to server to start convo
		r = requests.post(SERVER_ADDR+'messages/', data=json.dumps(userdata))
		response=json.loads(r.content)

		#handle server response appropriately.  If the creation worked, spawn a new conversation.  Otherwise, show an error.
		if response['result']=='success':
			newconvo=groupConvoWindow(selectedBuddiesList, response['id'], self.uname)
			newconvo.show()
			self.convoIds.append(str(response['id']))
			self.convos[str(response['id'])]=newconvo
			self.theDialog.done(1)

		else:
			self.message.setText(response['message'])
			self.message.exec_()

		self.isGroupDialog=False

	def checkForIncomingMessages(self):
		#get convos from the server
		r=requests.get(SERVER_ADDR+'messages/'+self.uname)
		response=json.loads(r.content)
		#update list of active convos user is involved in, based on id
		if response['result']=='success':
			self.convoIds[:]=[]
			for idNum in response['message_ids']:
				self.convoIds.append(str(idNum))

		#create convo windows for conversations user is now a part of
		for i in self.convoIds:
			if str(i) not in self.convos:
				self.convos[str(i)]=groupConvoWindow([], str(i), self.uname)

		#call receive message for each active convo.
		for chat in self.convos:
			if chat in self.convoIds:
				self.convos[chat].receiveMessage()

		#check if anyone is now online
		self.friends.clear()
		self.loadBuddies(self.friends, ['friends'])
		self.updateStatus()

	def logoutUser(self):
		#request to backup data on server
		r=requests.get(SERVER_ADDR+'backups/')

		#request to change status to offline
		logoff={}
		logoff['status']='offline'
		r=requests.put(SERVER_ADDR+'statuses/'+self.uname, data=json.dumps(logoff))
		response=json.loads(r.content)

		#if successful, close.  Otherwiise tell the user what happened.
		if response['result']=='success':
			self.close()
		else:
			self.message.setText('failure')
			self.message.exec_()

	def updateStatus(self):
		#check if you have friends online
		text='Currently Online: \n'
		#iterate through and check if friends are online
		counter=0
		for i in range(0,self.friends.count()):
			r=requests.get(SERVER_ADDR+'statuses/'+str(self.friends.item(i).text()).strip())
			response=json.loads(r.content)
			if response['status']=='online':
				text=text+str(self.friends.item(i).text()).strip()+'\n'
				counter=counter+1
		#case if no one is online
		if counter==0:
			text=text+'None'
		#set label appropriately
		self.statusLabel.setText(text)


class groupConvoWindow(QDialog):
	# class for conversation windows
	def __init__(self, buddies, message_id, uname, parent=None):
		super(groupConvoWindow, self).__init__(parent)
		#setup chat window
		self.setWindowTitle("Group Chat")
		layout = QVBoxLayout()

		#basic member data
		self.uname=uname
		self.buddies=buddies
		self.message_id=str(message_id).strip()

		#message box for alerts
		self.message=QMessageBox()

		#label to list all the buddies in the chat
		labeltext=''
		self.buddyLabel=QLabel(labeltext)
		layout.addWidget(self.buddyLabel)

		#setup boxes and buttons to send and receive messages
		self.chatBox=QTextEdit()
		self.chatBox.setReadOnly(True)
		self.chatBox.setFixedWidth(450)
		self.sendBox=QTextEdit()
		self.sendBox.setFixedHeight(70)
		self.sendButton=QPushButton('Send Message')
		layout.addWidget(self.chatBox)
		layout.addWidget(self.sendBox)
		layout.addWidget(self.sendButton)
		self.connect(self.sendButton, SIGNAL("pressed()"), self.sendMessage)

		#buttons for inviting people and leaving conversation:
		self.inviteButton=QPushButton("Invite A Buddy")
		self.leaveButton=QPushButton("Leave Conversation")
		layout.addWidget(self.inviteButton)
		layout.addWidget(self.leaveButton)
		self.connect(self.inviteButton, SIGNAL("pressed()"), self.inviteToConvoWindow)
		self.connect(self.leaveButton, SIGNAL("pressed()"), self.leaveConvo)

		#setup modal dialog member
		self.theDialog=QDialog()

		#member variable to keep track of current text
		self.oldText=''

		self.setLayout(layout)

	def sendMessage(self):
		text = str(self.sendBox.toPlainText())
                text = encryptor.caesar_cipher_encrypt(7,text)
		#setup data for server
		messagedata={}
		messagedata['username']=self.uname
		messagedata['id']=self.message_id
		#escape special html characters
		messagedata['content']=cgi.escape(text)
		#messagedata['content']=text
		messagedata['timestamp']='yes'
		#send message to server
		r=requests.put(SERVER_ADDR+'messages/', data=json.dumps(messagedata))
		response=json.loads(r.content)
		#tell the user what happened
		if response['result']=='success':
			self.sendBox.clear()
			self.receiveMessage()
		else:
			self.message.setText(response['message'])
			self.message.exec_()


	def receiveMessage(self):
		#get message from server
		r=requests.put(SERVER_ADDR+'messages/'+self.message_id)
		response=json.loads(r.content)
		#tell the user what happened and update chatbox if necessary.
		text=response['content']
                text=encryptor.caesar_cipher_decrypt(7,text)
		users=response['usernames']
		#change \n to <br> tags
		text=text.replace('\n', "<br>")
		#set emoticons
		text=text.replace(':)', "<img src=\":smile.png\"> ")
		text=text.replace(':(', "<img src=\":sad.png\"> ")
		text=text.replace(':D', "<img src=\":happy.png\"> ")
		text=text.replace(':/', "<img src=\":confused.png\"> ")
		text=text.replace(';)', "<img src=\":wink.png\"> ")
		#update text in box if necessary
		if response['result']=='success':
			if self.oldText!=text:
				self.show()
				self.chatBox.setHtml(text)
				self.chatBox.verticalScrollBar().setValue(self.chatBox.verticalScrollBar().maximum())
				#keep track of what current text is in a python string.
				self.oldText=text

			#update label of who is in conversation
			nametext=''
			for names in users:
				nametext=nametext+names+','
			nametext=nametext[:-1]
			self.buddyLabel.setText(nametext)

		else:
			self.message.setText(response['message'])
			self.message.exec_()

	def leaveConvo(self):
		#leave the conversation
		#setup data to send to server
		userdata={}
		userdata['username']=self.uname
		userdata['action']='remove'
		#request to leave conversation on server
		r=requests.post(SERVER_ADDR+'messages/'+str(self.message_id), data=json.dumps(userdata))
		response=json.loads(r.content)
		#tell the user what happened.  If successfully left, hide the window
		if response['result']=='success':
			self.hide()
		else:
			self.message.setText(response['message'])
			self.message.exec_()

	def inviteToConvoWindow(self):
		#setup layout to invite a new buddy
		layout = QVBoxLayout()
		instructionLabel=QLabel("Pick a buddy to invite:")
		layout.addWidget(instructionLabel)
		# give the user a dropdown menu of buddies to select to invite
		self.buddyText=QComboBox()
		self.loadBuddies(self.buddyText, ['friends'])
		layout.addWidget(self.buddyText)
		self.submitButton=QPushButton("Add")
		layout.addWidget(self.submitButton)
		#signal to invite the buddy through a button
		self.theDialog = QDialog()
		self.theDialog.setLayout(layout)
		self.connect(self.submitButton, SIGNAL("pressed()"), self.inviteToConvo)
		self.theDialog.exec_()

	def inviteToConvo(self):
		#setup data to send to server
		userdata={}
		userdata['username']=str(self.buddyText.currentText()).strip()
		userdata['action']='add'
		#send request to invite a friend to the conversation to the server
		r=requests.post(SERVER_ADDR+'messages/'+str(self.message_id), data=json.dumps(userdata))
		response=json.loads(r.content)
		#tell the user what happened
		if response['result']=='success':
			self.message.setText("Buddy successfully added to chat.")
			self.message.exec_()
			self.theDialog.done(1)
		else:
			self.message.setText(response['message'])
			self.message.exec_()

	def loadBuddies(self, item, attr):
		#function to populate buddy list.
		#clear collection
		item.clear()
		#request new list of buddies
		r = requests.get(SERVER_ADDR+'friends/'+self.uname)
		response=json.loads(r.content)
		if response['result']=='success':
			for i in response['usernames']:
				#add buddies that meetcriteria to list
				if i[1] in attr:
					item.addItem(i[0])
		else:
			#notify user if there is an error.
			self.message.setText(response['message'])
			self.message.exec_()

