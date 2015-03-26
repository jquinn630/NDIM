class Encryptor(object):
  def __init__(self):
    pass
  # Shift alphabet charcters up
  def caesar_cipher_encrypt(self,shift,message):
    encrypted_message = ""
    for char in message:
      if ord(char) >= 97 and ord(char) <= 122:
        encrypted_message += chr((((ord(char)-97)+shift)%26)+97)
      elif ord(char) >= 65 and ord(char) <= 90:
        encrypted_message += chr((((ord(char)-65)+shift)%26)+65)
      else:
        encrypted_message += char
    return encrypted_message
  # Shift alphabet characters down
  def caesar_cipher_decrypt(self,shift,message):
    decrypted_message = ""
    for char in message:
      if ord(char) >= 97 and ord(char) <= 122:
        decrypted_message += chr((((ord(char)-97)-shift)%26)+97)
      elif ord(char) >= 65 and ord(char) <= 90:
        decrypted_message += chr((((ord(char)-65)-shift)%26)+65)
      else:
        decrypted_message += char
    return decrypted_message
