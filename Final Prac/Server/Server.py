import fileinput
from socket import *

def hashString(stringToHash):
    list = stringToHash.split()           #Split the message sent to client/server
    intVal = 0
    m = 5
    for word in list:       #iterate over each word
        for char in word:   #iterate over each char in word
            newVal = (ord(char)**2)%m
            intVal = intVal + newVal
            if m == 21:
                m = 5
            else:
                m = 21
    return intVal

serverPort = 11000
serverSocket = socket(AF_INET, SOCK_DGRAM) # Create a UDP socket
serverSocket.bind(('', serverPort)) # Binds thhe port number to the server's socket

hashValue = 0
newMessage = ''
chatRoom = ''
senderId = ''

file = open('listOfClientID.txt','r')
lastLine = file.readlines()[-1] # checks for the most recent client ID 
lastLine = lastLine.lstrip('P')
lastLine = lastLine.lstrip('0')
clientId = int(lastLine)
file.close()

file = open('listOfChatSession.txt','r')
lastLine = file.readlines()[-1] # checks for the most recent chat ID 
lastLine = lastLine.lstrip('C')
lastLine = lastLine.lstrip('0')
chatId = int(lastLine)
file.close()

listOfClientId = []
file = open('listOfClientID.txt','r')
lines = file.readlines()
for line in lines:
     listOfClientId.append(line.strip()) # add lines of client ID into a list
file.close()

listOfChatSession = []
file = open('listOfChatSession.txt','r')
lines = file.readlines()
for line in lines:
     listOfChatSession.append(line.strip())  # add lines of Chat ID into a list
file.close()

print('The server is listening...') # indicates that the server is waiting for messages from clients
while True: # while loop will allow UDPServer to receive and process packets from clients indefinitely
 input, clientAddress = serverSocket.recvfrom(2048) # the packet’s data is put into the variable input and the packet’s source address is put into the variable clientAddress
 message = input.decode() # decode the message
 
 if message == 'REQID': # client request a new unique ID from the server
     clientId += 1
     if clientId < 10:
         newClientId = 'P0000'
     elif clientId < 100:
         newClientId = 'P000'
     elif clientId < 1000:
         newClientId = 'P00'
     elif clientId < 10000:
         newClientId = 'P0'
     elif clientId < 100000:
         newClientId = 'P'
    
     newClientId = newClientId + str(clientId) # creates a new Client ID
     file = open('listOfClientID.txt','a') # adds it to the text file
     file.write(newClientId + '\n')
     file.close()
     
     responseMessage = 'NEWID$' + str(newClientId) 
     serverSocket.sendto(responseMessage.encode(), clientAddress) # sends the client ID with the message back to the client
     print('A new client has been created!')

 if message == 'CRTCHT': # client wants to create a new chat room 
     chatId += 1
     if chatId < 10:
         newChatId = 'C0000'
     elif chatId < 100:
         newChatId = 'C000'
     elif chatId < 1000:
         newChatId = 'C00'
     elif chatId < 10000:
         newChatId = 'C0'
     elif chatId < 100000:
         newChatId = 'C'

     newChatId = newChatId + str(chatId) # creates a new chat ID
     file = open('listOfChatSession.txt', 'a') # adds it to the text file
     file.write(newChatId + '\n')
     file.close()

     file = open("Chat Sessions/" + newChatId + ".txt", "w")
     file.close()

     responseMessage = 'NEWCHT$' + str(newChatId)
     serverSocket.sendto(responseMessage.encode(), clientAddress) # sends the chat ID with the message back to the client
     print('A new chat room created!')

 if 'RETRIEVE' in message: # client requests messages from the server for a specified chat room
     instruction = message.split('$') # interprets the message
     chatSession = instruction[1]
     numOfLines = int(instruction[2])

     file = open("Chat Sessions/" + chatSession + '.txt','r')
     lines = file.readlines()
     file.close()

     lineCount = 0
     for line in lines:  # counts the number of lines in the textfile
         if line != "\n":
             lineCount += 1
     if lineCount > numOfLines: # if the server's textfile has more lines than the client's textfile then it sends the unread messages to the client
         index = numOfLines - lineCount
         lastLines = lines[index:]
         unreadMessages = []
         for line in lastLines:
             unreadMessages.append(line.strip())
         for msg in unreadMessages: #send the unread messages to the client one by one
             responseMessage = 'COLLECT$' + msg
             serverSocket.sendto(responseMessage.encode(), clientAddress)
     responseMessage = 'DONE' # once all the unread messages have been sent then the server will indicate that there are no more new messages
     serverSocket.sendto(responseMessage.encode(), clientAddress)

 if 'SEND' in message: # the client wants to send a new message to a chat room
     instruction = message.split('$')
     senderId = instruction[1]
     newMessage = instruction[2]
     chatRoom = instruction[3]
     senderhash = int(instruction[4])

     hashmess = "SEND$" + senderId + "$" + newMessage + "$" + chatRoom
     hashValue = hashString(hashmess) # uses the hash function here

     if hashValue == senderhash:
         file = open("Chat Sessions/" + chatRoom + ".txt", "a")
         file.write(senderId + ": " + newMessage + "\n")
         file.close()
         responseMessage = "VERIFIED"
     else: responseMessage = "HVALUE"

     serverSocket.sendto(responseMessage.encode(), clientAddress)

 if 'HValue' in message: # the server receives the hash value from a client
     instruction = message.split('$')
     clientHashValue = int(instruction[1])
     if hashValue == clientHashValue: # checks if the client's hash value matches the server's hash value
         responseMessage = 'VERIFIED' 
         serverSocket.sendto(responseMessage.encode(), clientAddress) # the server sends a message to a client to confirm that the message has been recieved correctly
         file = open("Chat Sessions/" + chatRoom + '.txt','a')
         file.write(senderId + ': ' + newMessage + '\n') # if they do match the server adds a new message to the textfile of the specified chat room
         file.close()
     else:
         responseMessage = 'The hash value does not match. Please send the message again.'
         serverSocket.sendto(responseMessage.encode(), clientAddress)

 if 'ASKCHT' in message: # a client asks if the chat session exist
     instruction = message.split('$')
     chatSession = instruction[1]

     listOfClientId = []
     file = open('listOfChatSession.txt', 'r')
     lines = file.readlines()
     for line in lines:
         listOfClientId.append(line.strip())  # add lines of client ID into a list
     file.close()

     if chatSession in listOfClientId:
         responseMessage = 'CHTEXST$YES'
         serverSocket.sendto(responseMessage.encode(), clientAddress)
     else:
         responseMessage = 'CHTEXST$NO'
         serverSocket.sendto(responseMessage.encode(), clientAddress)