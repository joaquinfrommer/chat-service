import argparse
from audioop import add
import tools
from time  import perf_counter
import socket
import select

# ----- Server Side Protocol -----
# LOGIN
#   Data - username
#   msg_type - LOGIN (0)
#
# LIST
#   Data - list of users 
#   msg_type - LST (1)
#
# SEND 
#   Data: 
#       username - username
#       uip - user ip
#       uport - user port
#   msg_type - SND (2)
#
# LOGOUT
#   msg_type - LOGOUT (3)
#
# Error
#   Data - null
#   Error - error message
#   msg_type: ERROR (-1)
# ----- ----- ----- -----

# User entries and abilities
LOGIN, LST, SND, LOGOUT, ERROR = 0, 1, 2, 3, -1
USERS = []
TAKEN_NAMES = []
IPTOUSR = {}
USRNAMETOUSR = {}

# Class for messaging service users
class User:
  def __init__(self, username, ip, port):
    self.username = username
    self.ip = ip
    self.port = port
    self.time = perf_counter()

# Socket setup
SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send msg to addr through socket, addr: (ip, port)
def socket_snd(msg, addr):
    try:
        SOCKET.sendto(tools.encode_json(msg), addr)
    except:
        print("Error sending message")
        return -1
    return 0

# Updates a users in activity time to 0
def update_time(address):
    user = IPTOUSR[address]
    user.time = perf_counter()
    return

# Handles user timeout after in activity
def check_timeout():
    current_time = perf_counter()
    for user in USERS:
        if current_time - user.time >= 120:
            address = (user.ip, user.port)
            logout(address)
    return

# Handles user sign-ins
def sign_in(address, data):
    if address in IPTOUSR.keys():
        reg_error = {"Data": "", "Error": "Error: Already logged in", "msg_type": ERROR}
        socket_snd(reg_error, address)
        return -1
    elif data["Data"] in TAKEN_NAMES:
        reg_error = {"Data": "", "Error": "Error: Username already taken", "msg_type": ERROR}
        socket_snd(reg_error, address)
        return -1
    else:
        uname = data["Data"]
        uip = address[0]
        uport = address[1]
        new_user = User(uname, uip, uport)
        USERS.append(new_user)
        TAKEN_NAMES.append(uname)
        IPTOUSR[address] = new_user
        USRNAMETOUSR[uname] = new_user
        loggedin = {"Data": 1, "msg_type": LOGIN}
        return socket_snd(loggedin, address)

# Handles requests to list users
def list_usrs_req(address):
    update_time(address)
    to_send = {"Data": TAKEN_NAMES, "msg_type": LST}
    return socket_snd(to_send, address)

def send_msg(address, data):
    update_time(address)
    uname = data["Data"]
    if (uname not in TAKEN_NAMES):
        to_send = {"Data": "", "Error": "No user %s online" % uname, "msg_type": ERROR}
        res = socket_snd(to_send, address)
    else:
        get_user = USRNAMETOUSR[uname]
        to_send = {"Data": {"username": uname, "uip": get_user.ip, "uport": get_user.port}, "msg_type": SND}
        res = socket_snd(to_send, address)
    return res

# Handles logging out users
def logout(address):
    user = IPTOUSR[address]
    TAKEN_NAMES.remove(user.username)
    del IPTOUSR[address]
    del USRNAMETOUSR[user.username]
    USERS.remove(user)
    socket_snd({"msg_type": LOGOUT}, address)
    print("+++ User with address %s is now logged out" % str(address[0]))
    return

# Handles message based on message type
def handle_message():
    msg, addr = SOCKET.recvfrom(2048)
    data = tools.decode_json(msg)
    msg_type = data["msg_type"]
    if msg_type == LOGIN:
        res = sign_in(addr, data)
        print("--- Unable to login user with address %s" % str(addr[0])) if res < 0 else print("+++ User logged in from address %s" % str(addr[0]))
    elif addr not in IPTOUSR:
        socket_snd(addr, {"Data": "", "Error": "Please log in again", "msg_type": ERROR})
    elif msg_type == LST:
        res = list_usrs_req(addr)
        if res < 0: print("--- Not able to list users for user with address %s" % str(addr[0])) 
    elif msg_type == SND:
        res = send_msg(addr, data)
        if res < 0: print("--- Not able to provide messaging information for user with address %s" % str(addr[0]))
    elif msg_type == LOGOUT:
        logout(addr)
    else:
        print("--- Recieved invalid request from user with address %s" % str(addr[0]))
        reg_error = {"Data": "", "Error": "Error: Invalid request", "msg_type": ERROR}
        res = socket_snd(addr, reg_error)
        if res < 0: print("--- Can not reach user with address %s" % str(addr[0]))
    return 

def main():
    t0 = perf_counter()
    while True:
        # Check for timeout 
        tn = perf_counter()
        if tn - t0 >= 60:
            check_timeout()
            t0 = perf_counter()
        # Recieve messages
        readyInput,w,e = select.select([SOCKET],[],[])
        for input in readyInput:
            if input == SOCKET:
                handle_message()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-sp', type=int, default=8080)
    args = parser.parse_args()
    host, port = socket.gethostbyname(socket.gethostname()), args.sp
    SOCKET.bind((host, port))
    print("+++ Server started at %s:%s" % (host, str(port)))
    main()
