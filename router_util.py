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
            data, info = self.recieve()
            self.forward(data, info)

    def recieve(self):
        while True:
            try:
                data = self.socket.recvfrom(BUFFERSIZE)
                return data[0], data[1]
            except TimeoutError:
                continue

    def forward(self, data, info):
        address = self.find_forward_address(data, info)
        if address is not EMPTY_ROW:
            self.send(data, info, address)

    def find_forward_address(self, data, info):
        for row in self.table:
            if row[DEST_TBL_I] == data:
                return row[FRWR_TBL_I]
        return EMPTY_ROW

    def send(self, data, info, address):
        print(data, info, address)
        self.socket.sendto(data, address)
