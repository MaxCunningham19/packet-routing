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
route_table = []
update_list = []

def get_table(filename):
    table = []
    with open(filename) as f:
        for line in f:
            cont = line.split(',')
            table.append([cont[0], cont[1], cont[2]])
    return table


def eq_adrs(adrs1, adrs2):
    return adrs1[0] == adrs2[0] and adrs1[1] == adrs2[1]


class Interface(threading.Thread):
    def __init__(self, sock: socket.socket, interface: int):
        threading.Thread.__init__(self)
        self.socket = sock
        self.interface = interface

    def run(self):
        print("interface", self.socket.getsockname(), self.interface, "running")
        while True:
            try:
                data = self.socket.recvfrom(BUFFERSIZE)
                op, adrs, info = enc.decode(data[0])
                if op != c.ACK:
                    add = self.sendACK(data[1])
                    if add:
                        print(self.interface, self.socket.getsockname(),
                              '| recieved', data[0], 'from', data[1])
                        recieved.append([data[0], data[1], self.interface])
                    while len(to_send[self.interface]) > 0:
                        sending = to_send[self.interface].pop()
                        print(self.interface, self.socket.getsockname(),
                              '| sending', sending)
                        self.send(sending)
                        print(self.interface, self.socket.getsockname(),
                              '| recieved ACK')
            except TimeoutError:
                while len(to_send[self.interface]) > 0:
                    sending = to_send[self.interface].pop()
                    print(self.interface, self.socket.getsockname(),
                          '| sending', sending)
                    self.send(sending)
                    print(self.interface, self.socket.getsockname(),
                          '| recieved ACK')

    def sendACK(self, adrs):
        try:
            print(self.interface, self.socket.getsockname(),
                  '| sending ACK to', adrs)
            msg = enc.encode(c.ACK, adrs, '')
            self.socket.sendto(msg, adrs)
            return True
        except TimeoutError:
            return False

    def send(self, sending):
        while True:
            try:
                self.socket.sendto(sending[0], sending[1])
                data = self.socket.recvfrom(BUFFERSIZE)
                op, _, _ = enc.decode(data[0])
                print(self.interface, '|', data[1], sending[1])
                if eq_adrs(data[1], sending[1]) and op == c.ACK:
                    return
            except TimeoutError:
                continue

class ContrlCon(threading.Thread):
    def __init__(self, sock:socket.socket, contrlr_adrs,):
        threading.Thread.__init__(self)
        self.socket = sock
        self.contrlr_adrs = contrlr_adrs

    def run(self):
        print("Controller Connection",self.socket.getsockname(), "running")
        while True:
            try:
                while len(update_list) > 0:
                    data = update_list.pop()
                    self.get_update(data)
                data,recved_adrs = self.socket.recvfrom(BUFFERSIZE)
                if eq_adrs(self.contrlr_adrs,recved_adrs):
                    op, adrs, info = enc.decode(data)
                    if op == c.FLOWMOD:
                        self.update_table(adrs,info)
            except TimeoutError:
                self.send_hello()

    def update_table(self,adrs, info):
        dest_pref, soc = enc.decode_data(info)
        for row in route_table:
            if row[0] == dest_pref:
                row[1] = adrs
                row[2] = soc

    def send_hello(self):
        try:
            msg = enc.encode(c.HELLO,self.socket.getsockname(),'')
            self.socket.sendto(msg,self.contrlr_adrs)
        except TimeoutError:
                return

    def get_update(self,data):
        while True:
            try:
                msg = enc.encode(c.FIND,data,'')
                self.socket.sendto(msg,self.contrlr_adrs)
                time.sleep(TIMEOUT)
                recv = self.socket.recvfrom(BUFFERSIZE)
                if eq_adrs(recv[0],self.contrlr_adrs):
                    op, adrs, info = enc.decode(data)
                    if op == c.FLOWMOD:
                        self.update_table(adrs,info)
            except TimeoutError:
                continue


#     Dest      #     whereto   #     socket    #
# ------------- # ------------- # ------------- #
#               #               #               #
#               #               #               #

class Router:
    def __init__(self, socks: List[socket.socket], contrl_con:socket.socket,ctrlr_adrs, init_table: List[List]):
        route_table = init_table
        self.contrl_con = ContrlCon(contrl_con,ctrlr_adrs)
        self.sockets: List[Interface] = []
        for i in range(len(socks)):
            to_send.append([])
            socks[i].settimeout(TIMEOUT)
            self.sockets.append(Interface(socks[i], i))

    def run(self):
        print("router started")
        for i in range(len(self.sockets)):
            self.sockets[i].start()
        while True:
            msg, adrs, interface = self.recieve()
            self.forward(msg, adrs, interface)

    def recieve(self):
        while True:
            if len(recieved) > 0:
                data = recieved.pop()
                return data[0], data[1], data[2]
            time.sleep(TIMEOUT)

    def forward(self, info, c_adrs, c_interface):
        op, dest_adrs, data = enc.decode(info)
        if op == c.SEND:
            next_address, interface = self.find_forward_address(dest_adrs)
            if  next_address is c.DROP or next_address is not None:
                self.send(c.SEND, dest_adrs, data,  next_address, interface)
                return
            print('dropped packet',  next_address, info)

    def find_forward_address(self, dest_adrs: str):
        longest_prefix_id = -1
        longest_prefix_length = 0
        for i in range(len(route_table)):
            row: List = route_table[i]
            if dest_adrs[0].startswith(route_table[i][0]):
                if len(route_table[i][0]) > longest_prefix_length:
                    longest_prefix_id = i
                    longest_prefix_length = len(route_table[i][0])
        if longest_prefix_id == -1:
            self.update(dest_adrs)
            return self.find_forward_address(dest_adrs)
        return route_table[longest_prefix_id][1], route_table[longest_prefix_id][2]

    def send(self, op, dest_adrs, data: bytes, next_address, interface):
        if next_address == c.IN_NETWORK:
            msg = enc.encode(op, dest_adrs, data)
            to_send[interface].append((msg, dest_adrs))
        else:
            msg = enc.encode(op, dest_adrs, data)
            to_send[interface].append((msg, next_address))

    def update(dest_adrs):
        update_list.append(dest_adrs)
        while len(update_list)> 0:
            time.sleep(TIMEOUT*4)
        

