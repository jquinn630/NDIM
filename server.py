# John Quinn
# Rob Wirthman
# CSE 30332 - Programming Paradigms
# Final Project - Instant Messenger
# April 21, 2013
import cherrypy
import json
from datetime import datetime
from encryptor import Encryptor

# Key: username Value: password
users = {}
friends = {}
# Key: username Value: list of message ids
users_messages = {}
# Key: message id Value: message content
messages = {}
# Key: username Value: status
statuses = {}
# Used in FriendController - MODIFY_RELATIONSHIP
actions=["friend","unfriend","block","unblock"]

def restore_data():
  # Restore users
  try:
    with open('users.dat') as file:
      for line in file:
        if line == "\n":
          break
        name,pwd=line.strip().split(':')
        users[name]=pwd
      file.close()
  except IOError:
    print "Unable to open users.dat"
  # Restore friends
  try:
    with open('friends.dat') as file:
      for line in file:
        if line == "\n":
          break
        name,data=line.strip().split('<')
        if not name in friends:
          friends[name] = []
        tuples = data.split('>')
        for tup in tuples:
           friends[name].append(tup.split(':'))
      file.close()
  except IOError:
    print "Unable to open friends.dat"

def backup_data():
  # Backup users
  try:
    with open('users.dat', 'w') as file:
      for user in users:
        file.write(user+":"+users[user]+"\n")
      file.close()
  except IOError:
    print "Unable to write users.dat"
  # Backup friends
  try:
    with open('friends.dat', 'w') as file:
      for name in friends:
        to_write = name+"<"
        for person,desc in friends[name]:
          to_write += person+":"+desc+">"
        file.write(to_write[:-1]+"\n")
      file.close()
  except IOError:
    print "Unable to write friends.dat"

class BackupController(object):
  # Usage: Backup users and friends
  # URL: /backups/get
  # Request Method: GET
  # Form-Data: N/A
  # On Success Returns: {"result":"success"}
  def BACKUP(self):
    output = {}
    backup_data()
    output["result"]="success"
    return json.dumps(output)
class StatusController(object):
  # Usage: Get a status for a given user
  # URL: /statuses/user
  # Request Method: GET
  # Form-Data: N/A
  # On Success Returns: {"status":"offline","result":"success"}
  def GET_STATUS(self,user):
    output = {}
    # Check that the username is recognized
    if user in users:
      if user in statuses:
        output["status"]=statuses[user]
      else:
        output["status"]="offline"
      output["result"]="success"
      return json.dumps(output)  
    else:
      output["message"]="The username "+user+" is not recognized."
      output["result"]="failure"
      return json.dumps(output)
  # Usage: Change a status for a given user
  # URL: /statuses/user
  # Request Method: PUT
  # Form-Data: {"status":"online"}
  # On Success Returns: {"result":"success"}
  def SET_STATUS(self,user):
    output = {}
    status_data = json.loads(cherrypy.request.body.read())
    # Check that the username is recognized
    if user in users:
      # Check that the request included status
      if "status" in status_data:
        statuses[user]=status_data["status"]
        output["result"]="success"
        return json.dumps(output)
      else:
        output["message"]="The key: status, was not included in the request."
        output["result"]="failure"
        return json.dumps(output)
    else:
      output["message"]="The username "+user+" is not recognized."
      output["result"]="failure"
      return json.dumps(output)
class MessageController(object):
  # Usage: Add/Remove a message id to/from a user's message list
  # URL: /messages/id
  # Request Method: POST
  # Form-Data to add: {"username":"user1","action":"add"}
  # Form-Data to remove: {"username":"user1","action":"remove"}
  # On Success Returns: {"result":"success"}
  def MANAGE_MESSAGE_ACCESS(self,id):
    output = {}
    message_data = json.loads(cherrypy.request.body.read())
    # Check that the request included username
    if "username" in message_data:
      # Check that the username is recognized
      if message_data["username"] in users:
        # Check that the id is recognized
        if int(id) in messages:
          # Check that the request included action
          if "action" in message_data:
            # Check that the action is either add or remove
            if message_data["action"] == "add":
              # Add More here
              if not message_data["username"] in users_messages:
                users_messages[message_data["username"]] = []
              users_messages[message_data["username"]].append(int(id))
              output["result"]="success"
              return json.dumps(output)
            elif message_data["action"] == "remove":
              if message_data["username"] in users_messages:
                if int(id) in users_messages[message_data["username"]]:
                  users_messages[message_data["username"]].remove(int(id))
              output["result"]="success"
              return json.dumps(output)
            else:
              output["message"]="The action "+message_data["action"]+" is not recognized."
              output["result"]="failure"
              return json.dumps(output)
          else:
            output["message"]="The key: action, was not included in the request."
            output["result"]="failure"
            return json.dumps(output)
        else:
          output["message"]="The id "+message_data["id"]+" is not recognized."
          output["result"]="failure"
          return json.dumps(output)
      else:
        output["message"]="The username "+message_data["username"]+" is not recognized."
        output["result"]="failure"
        return json.dumps(output)
    else:
      output["message"]="The key: username, was not included in the request."
      output["result"]="failure"
      return json.dumps(output)
  # Usage: Get the contents of a message given a specific id
  # URL: /messages/id
  # Request Method: PUT
  # Form-Data: Irrelevant
  # On Success Returns: {"content":"message text here...","usernames":["user1","user2",...],"result":"success"}
  def GET_MESSAGE(self,id):
    output = {}
    # Check if recognized id:
    if int(id) in messages:
      # Get the usernames of the people in the converstaion
      names = []
      for user in users:
        if user in users_messages:
          if int(id) in users_messages[user]:
            names.append(user)
      output["usernames"]=names
      output["content"]=messages[int(id)]
      output["result"]="success"
      return json.dumps(output)
    else:
      output["message"]="ID "+id+" is not recognized."
      output["result"]="failure"
      return json.dumps(output)
  # Usage: Get a list of message ids that the user can access
  # URL: /messages/username
  # Request Method: GET
  # Form-Data: N/A
  # On Success Returns: {"message_ids":[0,1,2,3,...],"result":"success"}
  def GET_MESSAGE_IDS(self,user):
    output = {}
    # Check if recognized username
    if user in users:
      # The user is recognized and has message(s)
      if user in users_messages:
        output["message_ids"]=users_messages[user]
        output["result"]="success"
        return json.dumps(output)
      # The user is recognized, but has no messages
      else:
        output["message_ids"]=[]
        output["result"]="success"
        return json.dumps(output)
    # The user is not recognized
    else:
      output["message"]="Username "+user+" is not recognized."
      output["result"]="failure"
      return json.dumps(output)
  # Usage: Create a new message
  # URL: /messages/
  # Request Method: POST
  # Form-Data: {"usernames":"[username1,username2,username3,...]"}
  # On Success Returns: {"id":0,"result":"success"}
  def CREATE_MESSAGE(self):
    output = {}
    message_data = json.loads(cherrypy.request.body.read())
    # Generate a unique message id
    message_id = 0
    while message_id in messages:
      message_id += 1
    # Check that the request included usernames
    if "usernames" in message_data:
      # message_data["usernames"] returns the literal string: [user1,user2,...]
      # Need to convert string into list
      for name in message_data["usernames"][1:-1].split(','):
        # Check that each username is recognized
        if name not in users:
          output["message"]="Username "+name+" is not recognized."
          output["result"]="failure"
          return json.dumps(output)
      for name in message_data["usernames"][1:-1].split(','):
        # Make sure that user is a key in users_messages
        if name not in users_messages:
          users_messages[name]=[]
        users_messages[name].append(message_id)
      # Add new, empty message to messages dictionary
      messages[message_id]=""
      output["id"]=message_id
      output["result"]="success"
      return json.dumps(output)
    else:
      output["message"]="Usernames were not included in the request."
      output["result"]="failure"
      return json.dumps(output)
  # Usage: Add text to a message with a given id
  # URL: /messages/
  # Request Method: PUT
  # Form-Data without timestamp: {"username":"user1","id":"0","content":"Hello World!"}
  # Form-Data with timestamp: {"username":"user1","id":"0","content":"Hello World!","timestamp":"yes"}
  # On Success Returns: {"result":"success"}
  def ADD_TO_MESSAGE(self):
    encryptor = Encryptor()
    output = {}
    message_data = json.loads(cherrypy.request.body.read())
    # Check that the request included username
    if "username" in message_data:
      # Check that the request included id
      if "id" in message_data:
        # Check that the request included content
        if "content" in message_data:
          # Check that the username is valid
          if message_data["username"] in users:
            # Check that the id is valid
            if int(message_data["id"]) in messages:
              # Safe to add to the message
              # Include timestamp in message?
              print_time = "no"
              # Check that the request included timestamp
              if "timestamp" in message_data:
                # Check the value of timestamp
                if message_data["timestamp"] == "yes":
                  print_time = "yes"
              str_to_add = "\n"
              if print_time == "no":
                str_to_add += encryptor.caesar_cipher_encrypt(7,message_data["username"])+": "+message_data["content"]
              else:
                str_to_add += encryptor.caesar_cipher_encrypt(7,message_data["username"])+encryptor.caesar_cipher_encrypt(7," at ")+str(datetime.now())[:-7]+": "+message_data["content"]
              messages[int(message_data["id"])] += str_to_add
              output["result"]="success"
              return json.dumps(output)
            else:
              output["message"]="Message ID "+message_data["id"]+" is not recognized."
              output["result"]="failure"
              return json.dumps(output)
          else:
            output["message"]="Username "+message_data["username"]+" is not recognized."
            output["result"]="failure"
            return json.dumps(output)
        else:
          output["message"]="The content was not included in the request."
          output["result"]="failure"
          return json.dumps(output)
      else:
        output["message"]="The id (of the message) was not included in the request."
        output["result"]="failure"
        return json.dumps(output)
    else:
      output["message"]="The username was not included in the request."
      output["result"]="failure"
      return json.dumps(output)

class FriendController(object):
  # Request Method: GET
  def GET_FRIENDS(self,user):
    output = {}
    # Check if recognized username
    if user in users:
      # The user is recognized and has friend(s)
      if user in friends:
        output["usernames"]=friends[user]
        output["result"]="success"
        return json.dumps(output)
      # The user is recognized, but has no friends
      else:
        output["usernames"]=[]
        output["result"]="success"
        return json.dumps(output)
    # The user is not recognized
    output["message"]="Username "+user+" is not recognized."
    output["result"]="failure"
    return json.dumps(output)
  # Request Method: POST
  def ADD_FRIEND(self):  
    output = {}
    friend_data = json.loads(cherrypy.request.body.read())
    # Check that the request included the username
    if "username" in friend_data:
      # Check that the username is recognized
      if friend_data["username"] in users:
        # Check that the request included the friend's usernamer
        if "friendname" in friend_data:
          # Check that the friend's username is recognized
          if friend_data["friendname"] in users:
            # If username is not a key in the friends dictionary, add it
            if not friend_data["username"] in friends:
              friends[friend_data["username"]]=[]
            # Add entry to the user's friend list
            friends[friend_data["username"]].append((friend_data["friendname"],"friender"))
            # If the friend's username is not a key in the friends dictionary, add it
            if not friend_data["friendname"] in friends:
              friends[friend_data["friendname"]]=[]
            # Add entry to the user's friend's friend list
            friends[friend_data["friendname"]].append((friend_data["username"],"friended"))
            output["result"]="success"
            return json.dumps(output)
          else:
            output["message"]="The friend's username "+friend_data["friendname"]+" is not recognized."
            output["result"]="failure"
            return json.dumps(output)
        else:
          output["message"]="The friend's username was not included in the request."
          output["result"]="failure"
          return json.dumps(output)
      else:
        output["message"]="Username "+friend_data["username"]+" is not recognized."
        output["result"]="failure"
        return json.dumps(output)
    else:
      output["message"]="The username was not included in the request."
      output["result"]="failure"
      return json.dumps(output)
  # Request Method: PUT
  def MODIFY_RELATIONSHIP(self):
    output = {}
    friend_data = json.loads(cherrypy.request.body.read())
    # Check that the request included the username
    if "username" in friend_data:
      # Check that the username is recognized
      if friend_data["username"] in users:
        # Check that the request included the friend's usernamer
        if "friendname" in friend_data:
          # Check that the friend's username is recognized
          if friend_data["friendname"] in users:
            # Check that the request included the action
            if "action" in friend_data:
              # Check that the action is recognized
              if friend_data["action"] in actions:
                pass
                # If need to debug function, add additional error checking here
                # Build up temp_user to include what was originally in friends[username] except for the entry for friendname
                temp_user = []
                for name,status in friends[friend_data["username"]]:
                  if not name == friend_data["friendname"]:
                    temp_user.append((name,status))
                # Build up temp_friend to include what was originally in friends[friendname] except for the entry for username
                temp_friend = []
                for name,status in friends[friend_data["friendname"]]:
                  if not name == friend_data["username"]:
                    temp_friend.append((name,status))
                # friend
                if friend_data["action"]=="friend":
                  temp_user.append((friend_data["friendname"],"friends"))
                  temp_friend.append((friend_data["username"],"friends"))
                # unfriend
                elif friend_data["action"]=="unfriend":
                  # no need to do anything - at this point temp_user and temp_friend do not include the other party
                  pass
                # block
                elif friend_data["action"]=="block":
                  temp_user.append((friend_data["friendname"],"blocker"))
                  temp_friend.append((friend_data["username"],"blocked"))
                # unblock
                elif friend_data["action"]=="unblock":
                  # no need to do anything - at this point temp_user and temp_friend do not include the other party
                  # either party is now free to friend request the other
                  pass
                friends[friend_data["username"]]=temp_user
                friends[friend_data["friendname"]]=temp_friend
                output["result"]="success"
                return json.dumps(output)
              else:
                output["message"]="The action "+friend_data["action"]+" is not recognized."
                output["result"]="failure"
                return json.dumps(output)
            else:
              output["message"]="The action was not included in the request."
              output["result"]="failure"
              return json.dumps(output)
          else:
            output["message"]="The friend's username "+friend_data["friendname"]+" is not recognized."
            output["result"]="failure"
            return json.dumps(output)
        else:
          output["message"]="The friend's username was not included in the request."
          output["result"]="failure"
          return json.dumps(output)
      else:
        output["message"]="Username "+friend_data["username"]+" is not recognized."
        output["result"]="failure"
        return json.dumps(output)
    else:
      output["message"]="The username was not included in the request."
      output["result"]="failure"
      return json.dumps(output)

class UserController(object):
  # Consider returing a list of friends if successful
  # Request Method: POST
  def LOGIN(self,user):
    output = {}
    # Check if recognized username
    if user in users:
      # Check that the request included the password
      user_data = json.loads(cherrypy.request.body.read())
      if "password" in user_data:
        # Check that the request included the correct password
        if user_data["password"] == users[user]:
          output["result"]="success"
          return json.dumps(output)
    # Invalid login credintials
    output["message"]="Permission denied, please try again."
    output["result"]="failure"
    return json.dumps(output)
  # Get all recognized usernames
  def GET(self):
    output = {}
    output["usernames"]=users.keys()
    output["result"]="success"
    return json.dumps(output)
  # Add a new user
  def POST(self):  
    output = {}
    user_data = json.loads(cherrypy.request.body.read())
    # Check that the request included the username
    if "username" in user_data:
      # Check that the username is available
      if user_data["username"] in users:
        output["message"]="Username "+user_data["username"]+" is not available."
        output["result"]="failure"
        return json.dumps(output)
      # Check that the username is 6-14 characters long
      if len(user_data["username"]) < 6 or len(user_data["username"]) > 14:
        output["message"]="Username "+user_data["username"]+" is not 6-14 characters long."
        output["result"]="failure"
        return json.dumps(output)
      # Check that the username is alphanumeric
      if not user_data["username"].isalnum():
        output["message"]="Username "+user_data["username"]+" is not alphanumeric."
        output["result"]="failure"
        return json.dumps(output)
    else:
      output["message"]="The username was not included in the request."
      output["result"]="failure"
      return json.dumps(output)
    # Check that the request included the password
    if "password" in user_data:
      # Check the complexity of the password
      # Check that the password is 8-16 characters long
      if len(user_data["password"]) < 8 or len(user_data["username"]) > 16:
        output["message"]="Your password is not 8-16 characters long."
        output["result"]="failure"
        return json.dumps(output)
      # Check that the password has at least 3 of the properties listed below
      contains_number=0
      contains_uppercase=0
      contains_lowercase=0
      contains_special=0
      for char in user_data["password"]:
        if char.isdigit() and contains_number == 0:
          contains_number = 1
        if char.islower() and contains_lowercase == 0:
          contains_lowercase = 1
        if char.isupper() and contains_uppercase == 0:
          contains_uppercase = 1
        if not char.isalpha() and contains_special == 0:
          contains_special = 1
      complexity_sum = contains_number + contains_uppercase + contains_lowercase + contains_special
      if complexity_sum < 3:
        output["message"]="Your password does not have at least 3 of the 4 required properties."
        output["result"]="failure"
        return json.dumps(output)
    else:
      output["message"]="The password was not included in the request."
      output["result"]="failure"
      return json.dumps(output)
    # The username and password combination has passed all the checks, add to users dictionary
    users[user_data["username"]]=user_data["password"]
    output["result"]="success"
    return json.dumps(output)

def start_service():
  dispatcher = cherrypy.dispatch.RoutesDispatcher()

  dispatcher.connect('users_get','/users/',controller=UserController(),action='GET',conditions=dict(method=['GET']))
  dispatcher.connect('users_post','/users/',controller=UserController(),action='POST',conditions=dict(method=['POST']))
  dispatcher.connect('users_post','/users/:user',controller=UserController(),action='LOGIN',conditions=dict(method=['POST']))
  dispatcher.connect('friends_get','/friends/:user',controller=FriendController(),action='GET_FRIENDS',conditions=dict(method=['GET']))
  dispatcher.connect('friends_post','/friends/',controller=FriendController(),action='ADD_FRIEND',conditions=dict(method=['POST']))
  dispatcher.connect('friends_put','/friends/',controller=FriendController(),action='MODIFY_RELATIONSHIP',conditions=dict(method=['PUT']))
  dispatcher.connect('messages_get','/messages/:user',controller=MessageController(),action='GET_MESSAGE_IDS',conditions=dict(method=['GET']))
  dispatcher.connect('messages_post','/messages/',controller=MessageController(),action='CREATE_MESSAGE',conditions=dict(method=['POST']))
  dispatcher.connect('messages_put','/messages/',controller=MessageController(),action='ADD_TO_MESSAGE',conditions=dict(method=['PUT']))
  dispatcher.connect('messages_put','/messages/:id',controller=MessageController(),action='GET_MESSAGE',conditions=dict(method=['PUT']))
  dispatcher.connect('messages_post','/messages/:id',controller=MessageController(),action='MANAGE_MESSAGE_ACCESS',conditions=dict(method=['POST']))
  dispatcher.connect('statuses_get','/statuses/:user',controller=StatusController(),action='GET_STATUS',conditions=dict(method=['GET']))
  dispatcher.connect('statuses_put','/statuses/:user',controller=StatusController(),action='SET_STATUS',conditions=dict(method=['PUT']))
  dispatcher.connect('backups_get','/backups/',controller=BackupController(),action='BACKUP',conditions=dict(method=['GET']))

  conf = {
          'global': {'server.socket_host': 'student03.cse.nd.edu', 'server.socket_port': 40004,},
          '/': {'request.dispatch': dispatcher,}
         }
  cherrypy.config.update(conf)
  app = cherrypy.tree.mount(None, config=conf)
  cherrypy.quickstart(app)

if __name__ == '__main__':
  restore_data()
  start_service()
