import socket
from typing import List
import constants as c
import encode as enc
import threading
import time

BUFFERSIZE = 1024
DEST_TBL_I = 0
FRWR_TBL_I = 1
EMPTY_ROW = -1

EMPTY = []
recieved = []
to_send = []
update_list = []
routing_table = []


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
                        if self.send(sending):
                            print(self.interface, self.socket.getsockname(),
                              '| recieved ACK')
                        else:
                            print(self.interface, self.socket.getsockname(),
                              '| dropped',sending)
            except TimeoutError:
                while len(to_send[self.interface]) > 0:
                    sending = to_send[self.interface].pop()
                    print(self.interface, self.socket.getsockname(),
                          '| sending', sending)
                    if self.send(sending):
                        print(self.interface, self.socket.getsockname(),
                          '| recieved ACK')
                    else:
                        print(self.interface, self.socket.getsockname(),
                          '| dropped',sending)
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
        count = 0
        while True:
            try:
                self.socket.sendto(sending[0], sending[1])
                data = self.socket.recvfrom(BUFFERSIZE)
                op, _, _ = enc.decode(data[0])
                print(self.interface, '|', data[1], sending[1])
                if eq_adrs(data[1], sending[1]) and op == c.ACK:
                    return True
            except TimeoutError:
                if count > 10:
                    return False
                count = count+1
                continue

ctrlr_lock = threading.Lock()
class ConHello(threading.Thread):
    def __init__(self, sock:socket.socket, contrlr_adrs):
        threading.Thread.__init__(self)
        self.socket = sock
        self.contrlr_adrs = contrlr_adrs

    def run(self):
        while True:
            try:
                self.send_hello()
                time.sleep(c.TIMEOUT*c.TIMEOUT_MUL)
            except TimeoutError:
                continue

    def send_hello(self):
        msg = enc.encode(c.HELLO,self.socket.getsockname(),'')
        ctrlr_lock.acquire()
        while True:
            try:
                self.socket.sendto(msg,self.contrlr_adrs)
                data = self.socket.recvfrom(BUFFERSIZE)
                op, adrs, _ = enc.decode(data[0])
                if op == c.ACK and eq_adrs(self.contrlr_adrs, data[1]) and eq_adrs(self.socket.getsockname(),adrs):
                    ctrlr_lock.release()
                    return
            except TimeoutError:
                continue

class ContrlCon():
    def __init__(self, sock:socket.socket, contrlr_adrs):
        self.hellos = ConHello(sock,contrlr_adrs)
        self.hellos.start()
        self.socket = sock
        self.contrlr_adrs = contrlr_adrs

    # def update_table(self,adrs, info):
    #     dest_pref, _ = enc.decode_data(info)
    #     for i in range(len(routing_table)):
    #         if dest_pref == routing_table[i][0]:
    #             soc = self.find_socket(adrs)
    #             if soc == -1:
    #                 raise Exception('error controller gave invalid address')
    #             routing_table[i] = [dest_pref,adrs,soc]

    def get_update(self,dest):
        msg = enc.encode(c.FIND,dest,'')
        ctrlr_lock.acquire()
        while True:
            try:
                self.socket.sendto(msg,self.contrlr_adrs)
                recv = self.socket.recvfrom(BUFFERSIZE)
                op, adrs, info = enc.decode(recv[0])
                if eq_adrs(recv[1],self.contrlr_adrs) and op == c.FLOWMOD:
                    ctrlr_lock.release()
                    return c.ACK, adrs, info
            except TimeoutError:
                continue





# Dest prefix   #    whereto    #     socket    #
# ------------- # ------------- # ------------- #
#               #               #               #
#               #               #               #

class Router:
    def __init__(self, socks: List[socket.socket], contrl_con:socket.socket,ctrlr_adrs, init_table: List[List]):
        self.table = init_table
        self.contrl_con = ContrlCon(contrl_con,ctrlr_adrs)
        self.sockets: List[Interface] = []
        for i in range(len(socks)):
            to_send.append([])
            socks[i].settimeout(c.TIMEOUT)
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
            time.sleep(c.TIMEOUT)

    def forward(self, info, c_adrs, c_interface):
        op, dest_adrs, data = enc.decode(info)
        if op == c.SEND:
            next_address, interface = self.find_forward_address(dest_adrs)
            if next_address != c.DROP and next_address is not None and interface != -1:
                self.send(c.SEND, dest_adrs, data,  next_address, interface)
                return
            print('dropped packet', dest_adrs, info)

    def find_forward_address(self, dest_adrs: str):
        longest_prefix_id = -1
        longest_prefix_length = 0
        for i in range(len(self.table)):
            if dest_adrs[0].startswith(self.table[i][0]):
                if len(self.table[i][0]) > longest_prefix_length:
                    longest_prefix_id = i
                    longest_prefix_length = len(self.table[i][0])
                    
        if longest_prefix_id == -1:
            op, nxt_adrs, _ = self.update(dest_adrs)
            if op == c.ACK:
                return self.add_to_table(nxt_adrs,dest_adrs)
            else:
                return None, None
            
        return self.table[longest_prefix_id][1],self.table[longest_prefix_id][2]

    def add_to_table(self,nxt_adrs,dest):
        if eq_adrs(nxt_adrs,dest):
            return dest, self.find_socket(dest)
        if eq_adrs(c.DROP,nxt_adrs):
            return nxt_adrs,0

        soc = 0
        print(nxt_adrs,dest)
        if nxt_adrs != c.DROP:
            soc = self.find_socket(nxt_adrs)
            if soc == -1:
                raise Exception('error controller gave invalid address')
        prefix = dest[0].split('.')
        prefix = prefix[0:3]
        prefix = '.'.join(prefix)
        self.table.append([prefix,nxt_adrs,soc])
        return nxt_adrs,soc

    def find_socket(self,adrs):
        longest = -1
        soc = -1
        for row in self.table:
            if adrs[0].startswith(row[0]) and len(row[0])>longest:
                soc = row[2]
                longest = len(row[0])
        return soc

    def send(self, op, dest_adrs, data: bytes, next_address, interface):
        if next_address == c.IN_NETWORK:
            msg = enc.encode(op, dest_adrs, data)
            to_send[interface].append((msg, dest_adrs))
        else:
            msg = enc.encode(op, dest_adrs, data)
            to_send[interface].append((msg, next_address))

    def update(self,dest_adrs):
        return self.contrl_con.get_update(dest_adrs)
        # update_list.append(dest_adrs)
        # while len(update_list)> 0:
        #     time.sleep(c.TIMEOUT*4)
        

