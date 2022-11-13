import socket
from typing import List
import constants as c
import encode as enc
import threading
import time

BUFFERSIZE = 1024
TIMEOUT = 0.1
DEST_TBL_I = 0
FRWR_TBL_I = 1
EMPTY_ROW = -1

EMPTY = []
recieved = []
to_send = []

def get_table(filename):
    table = []
    with open(filename) as f:
        for line in f:
            cont = line.split(',')
            table.append([cont[0],cont[1],cont[2]])
    return table

class Interface(threading.Thread):
    def __init__(self,sock:socket.socket, interface:int):
        threading.Thread.__init__(self)
        self.socket = sock
        self.interface = interface
       
    def run(self):
        print("interface",self.socket.getsockname(), self.interface, "running")
        while True:
            try:
                data = self.socket.recvfrom(BUFFERSIZE)
                recieved.append(data)
                while len(to_send[self.interface]) > 0:
                    sending = to_send[self.interface].pop()
                    print(sending, self.interface, self.socket.getsockname())
                    self.socket.sendto(sending[0],sending[1])
            except TimeoutError:
                while len(to_send[self.interface]) > 0:
                    sending = to_send[self.interface].pop()
                    print(sending, self.interface, self.socket.getsockname())
                    self.socket.sendto(sending[0],sending[1])
       

#     Dest      #     whereto   #     socket    #
# ------------- # ------------- # ------------- #
#               #               #               #
#               #               #               #

class Router:
    def __init__(self, socks:List[socket.socket], table: List[List]):
        self.route_table = table
        self.sockets : List[Interface] = []
        for i in range(len(socks)):
            to_send.append([])
            socks[i].settimeout(TIMEOUT)
            self.sockets.append(Interface(socks[i],i))
        

    def run(self):
        print("router started")
        for i in range(len(self.sockets)):
            self.sockets[i].start()
        while True:
            self.forward(self.recieve())


    def recieve(self):
        while True:
            if len(recieved) > 0:
                data = recieved.pop()
                return data[0]
            time.sleep(TIMEOUT)

    def forward(self, info):
        _, dest_adrs, data = enc.decode(info)
        next_address, interface = self.find_forward_address(dest_adrs)
        if  next_address is not None:
            self.send(dest_adrs, data,  next_address, interface)
            return
        print('dropped packet',  next_address, info)


    def find_forward_address(self, dest_adrs:str):
        longest_prefix_id = -1
        longest_prefix_length = 0
        for i in range(len(self.route_table)):
            row : List = self.route_table[i]
            if dest_adrs[0].startswith(self.route_table[i][0]):
                if len(self.route_table[i][0]) > longest_prefix_length:
                    longest_prefix_id = i
                    longest_prefix_length = len(self.route_table[i][0])
        if longest_prefix_id == -1:
            return None, None
        return self.route_table[longest_prefix_id][1], self.route_table[longest_prefix_id][2]


    def send(self,dest_adrs, data:bytes, next_address, interface):
        if next_address == c.IN_NETWORK:
            msg = enc.encode('',dest_adrs, data)
            to_send[interface].append((msg,dest_adrs))
        else:
            msg = enc.encode('',dest_adrs,data)
            to_send[interface].append((msg,next_address))
            

