#Joshua Peter Roux
#Client of the messanger application.
#05 March 2022
import time
from socket import *
import os.path
import os
from threading import Thread

HOSTIP = "192.168.42.95"                                        #IP address of server
HOSTPORT = 11000                                                #Port of server
TEXTFILEDIR = "TextFiles/"                                      #Directory for the text files
BUFFERSIZE = 2000                                               #Size of buffers
PRESSEDI = False                                                #Checks whether user has pressed 'i' to enter message in chat message
CANCHECK = True
THREADRUNNING = True

class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

def header():                                                   #Displays User's name and ID
    f = open(TEXTFILEDIR + "ID.txt", "r")
    userid = f.readline()
    username = f.readline()
    print("ID: " + userid + "User: " + username)
    f.close()

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

def check_id(csocket:socket):                                   #Checks if ID has already been given by server
    exists = os.path.exists("TextFiles/ID.txt")
    if exists:                                                  #If file does not exist create new file
        header()
    else:
        csocket.sendto("REQID".encode(), (HOSTIP, HOSTPORT))    #Request unique ID
        message, serverip = csocket.recvfrom(BUFFERSIZE)
        message = message.decode()
        message = message.split("$")

        f = open("TextFiles/ID.txt", "w")
        f.write(message[1] + "\n")
        keyinput = input("Please enter your username: ")
        f.write(keyinput)
        f.close()

        f = open(TEXTFILEDIR + "chatid.txt", "w")
        f.close()

        header()

def count_file_lines(chatid:str):
    f = open(TEXTFILEDIR + chatid + ".txt", "r")
    count = 0
    while True:
        line = f.readline().strip("\n")
        if line == "":
            break
        else:
            count = count + 1
    f.close()
    return count

def create_session(csocket:socket):
    csocket.sendto("CRTCHT".encode(), (HOSTIP, HOSTPORT))
    message, haddress = csocket.recvfrom(BUFFERSIZE)
    message = message.decode()
    message = message.split("$")

    f = open(TEXTFILEDIR + "chatid.txt", "r")
    line = f.read()
    f.close()

    if line == '':
        f = open(TEXTFILEDIR + "chatid.txt", "a")
        f.write(message[1])
        f.close()
    else:
        f = open(TEXTFILEDIR + "chatid.txt", "a")
        f.write("\n" + message[1])
        f.close()

    f = open(TEXTFILEDIR + message[1] + ".txt", "w")
    f.close()

    print("Chat session has been created.\n" + "New chat session ID: " + message[1] + "\nPress Enter to continue")
    enter = input()

    join_session(message[1], csocket)

def join_session(sessionid, csocket):                           #Join existing session.
    f = open(TEXTFILEDIR + "chatid.txt", "r")
    while True:
        chatid = f.readline().strip("\n")
        if chatid == "":
            break
        if chatid == sessionid:
            break
    f.close()

    if chatid == "":
        message = "ASKCHT$" + sessionid
        csocket.sendto(message.encode(), (HOSTIP, HOSTPORT))
        message, serveraddress = csocket.recvfrom(BUFFERSIZE)

        message = message.decode().split("$")
        if message[1] == "YES":
            f = open(TEXTFILEDIR + "chatid.txt", "r")
            line = f.read()
            f.close()

            if line == "":
                f = open(TEXTFILEDIR + "chatid.txt", "a")
                f.write(sessionid)
                f.close()
            else:
                f = open(TEXTFILEDIR + "chatid.txt", "a")
                f.write("\n" + sessionid)
                f.close()

            f = open(TEXTFILEDIR + sessionid + ".txt", "w")
            f.close()

            join_session(sessionid, csocket)
        else:
            print("Sorry. Chat session could not be found.\n")
    else:
        load_session(chatid, csocket)

def load_session(chatid:str, csocket):
    print("--Entered Session--")
    f = open(TEXTFILEDIR + chatid + ".txt", "r")
    log = f.read()
    f.close()
    print(log)

    message = "RETRIEVE$" + chatid

    count = count_file_lines(chatid)
    message = message + "$" + str(count)
    csocket.sendto(message.encode(), (HOSTIP, HOSTPORT))        #Requests new unsaved messages of sessions

    message = ''
    while True:
        message, serverip = csocket.recvfrom(BUFFERSIZE)        #Gets new messages for session.
        message = message.decode()
        message = message.split("$")

        if message[0] == "DONE":
            break
        else:
            update_chat_file(chatid, message[1])                #Update client chat log file
            print(message[1])

    global PRESSEDI
    global CANCHECK

    keybthread = Thread(target=keyboard_check)
    keybthread.start()                                          #Starts thread to check whether the user wants to enter a message
    while True:
        if PRESSEDI:
            CANCHECK = False
            userid = get_id()
            usermess = input("Enter message (Enter '!back' to exit chat session):\n")                #User enters message
            usermess = usermess.replace("\n", "")

            if usermess == "!back": break

            sendmess = "SEND$" + userid + "$" + usermess + "$" + chatid
            hashval = hashString(sendmess)
            sendmess = sendmess + "$" + str(hashval)
            sendmess = sendmess.encode()

            while True:
                csocket.sendto(sendmess, (HOSTIP, HOSTPORT))
                sendmess, serveraddress = csocket.recvfrom(BUFFERSIZE)
                response = sendmess.decode().split("$")
                if response[0] == "VERIFIED": break

            sendmess = sendmess.decode().split("$")
            
            f = open(TEXTFILEDIR + chatid + ".txt", "r")
            line = f.read().strip("\n")
            f.close()

            if line == '':
                f = open(TEXTFILEDIR + chatid + ".txt", "a")
                f.write(get_id() + ": " + usermess)
                f.close
            else:
                f = open(TEXTFILEDIR + chatid + ".txt", "a")
                f.write("\n" + get_id() + ": " + usermess)
                f.close

            f = open(TEXTFILEDIR + chatid + ".txt", "r")
            log = f.read()
            f.close()
            print()
            print()
            print(log)

            PRESSEDI = False
            CANCHECK = True

        count = count_file_lines(chatid)
        message = "RETRIEVE$" + chatid + "$" + str(count)       #Ask for new messages
        csocket.sendto(message.encode(), (HOSTIP, HOSTPORT))

        message, serveraddress = csocket.recvfrom(BUFFERSIZE)
        message = message.decode().split("$")
        if message[0] == "DONE":
            pass
        else:
            print(message[1])
            update_chat_file(chatid, message[1])                    #Update chat log file of a session

def update_chat_file(chatid, message):                          #Update chat log file of a session
    f = open(TEXTFILEDIR + chatid + ".txt", 'r')
    line = f.read().strip("\n")
    if line == '':
        f = open(TEXTFILEDIR + chatid + ".txt", "a")
        f.write(message)
        f.close()
    else:
        f = open(TEXTFILEDIR + chatid + ".txt", "a")
        f.write("\n" + message)
        f.close()

def get_id():
    f = open(TEXTFILEDIR + "ID.txt", "r")
    userid = f.readline().strip("\n")
    f.close()
    return userid

def keyboard_check():                                           #Run's in a separate thread to check whether the user has pressed i to enter message into chat.
    global PRESSEDI
    while THREADRUNNING:
        getch = _Getch()
        if CANCHECK:
            useri = getch()
            if useri == 'i'.encode(): useri = useri.decode()
            if useri == 'i':
                PRESSEDI = True
                time.sleep(2)

def chatid_correct(chatid:str) -> bool:                         #Checks whether chat id given by user is in the correct format.
    if chatid[0] != 'C':
        return False

    if len(chatid) != 6:
        return False
    
    chatid = chatid[1:]
    for char in chatid:
        if char.isnumeric():
            pass
        else:
            return False
    return True

def main():
    if not os.path.exists(TEXTFILEDIR):
        os.makedirs(TEXTFILEDIR)
        f = open(TEXTFILEDIR + "chatid.txt", "w")
        f.close()

    global PRESSEDI
    global CANCHECK
    global THREADRUNNING

    clientsock = socket(AF_INET, SOCK_DGRAM)                    #Creates the Socket of the client.

    check_id(clientsock)

    exitbool = False
    while not exitbool:
        PRESSEDI = False
        CANCHECK = True
        THREADRUNNING = True
        userinput = input("What would you like to do with a session (join/create) or would you like to (exit):\n")
        
        if userinput == "exit":
            exitbool = True

        elif userinput == "join":      
            sessionid = input("Please enter chat session code, once inside session press i to start writing or exit chat: \n")
            
            while True:
                check = chatid_correct(sessionid)
                if check: break
                else:
                    sessionid = input("Not a Valid chat session id.\nPlease make sure the id is 6 characters long, starts with 'C' and that the remaining carachters are numbers:\n")
                    print()
            join_session(sessionid, clientsock)
        
        elif userinput == "create":
            create_session(clientsock)
        
        else:
            print("Please enter a valid option.")
        THREADRUNNING = False
        time.sleep(1)

    clientsock.close()                                          #Closes socket
    print("Good Bye")
    exit()

def test_message(message):                                      #Used for testing
    print("////")
    print(message)
    print("///")

if __name__=="__main__":
    main()
