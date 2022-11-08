import socket
from typing import List

BUFFERSIZE = 1024
TIMEOUT = 3.0
DEST_TBL_I = 0
FRWR_TBL_I = 1
EMPTY_ROW = -1


class Router:
    def __init__(self, socket: socket.socket, table: List):
        self.table = table
        self.socket = socket
        self.socket.settimeout(TIMEOUT)

    def run(self):
        while True:
            adrs, info = self.recieve()
            self.forward(adrs, info)

    def recieve(self):
        while True:
            try:
                data = self.socket.recvfrom(BUFFERSIZE)
                return data[1], data[0] 
            except TimeoutError:
                continue

    def forward(self, adrs, info):
        address = self.find_forward_address(adrs, info)
        if address is not EMPTY_ROW:
            self.send(info, address)
            return
        print(self.socket.getsockname(), 'dropped packet', adrs, info)

    def find_forward_address(self, adrs, info):
        for row in self.table:
            if row[DEST_TBL_I] == adrs:
                return row[FRWR_TBL_I]
        return EMPTY_ROW

    def send(self, data, address):
        print(data, address)
        self.socket.sendto(data, address)
