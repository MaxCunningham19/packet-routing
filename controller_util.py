import socket
from typing import List
from collections import defaultdict
import constants as c
import encode as enc

BUFFERSIZE = 1024
TIMEOUT = 3.0
DEST_TBL_I = 0
FRWR_TBL_I = 1
EMPTY_ROW = -1


class Controller:
    def __init__(self, socket: socket.socket):
        self.socket = socket
        self.graph = {}
        self.socket.settimeout(TIMEOUT)

    def run(self):
        while True:
            cur_adrs, op, oth_adrs = self.recieve()
            if op == c.FIND:
                next_adrs = self.find_next_addrs(cur_adrs, oth_adrs)
                self.send(cur_adrs,c.ACK,next_adrs)
            elif op == c.ADD:
                self.add_edge([cur_adrs,oth_adrs])
                self.send(cur_adrs,c.ACK,'')
            else:
                self.send(cur_adrs,c.NAK,'')

    def recieve(self):
        while True:
            try:
                data = self.socket.recvfrom(BUFFERSIZE)
                op, info = enc.decode(data[0])
                return data[1], op, info
            except TimeoutError:
                continue

    def find_next_addrs(self, cur_adrs, dest_adrs):
        path = self.BFS_SP(cur_adrs, dest_adrs)
        if path is None :
            return c.DEST
        if path == -1:
            return c.DROP
        return path[1]
    
    def send(self, address, op, data):
        print(op, data, address)
        ret = enc.encode(op,data)
        self.socket.sendto(ret, address)

    def add_edge(self, edge):
        a, b = edge[0], edge[1]
        if self.graph.get(a) is None:
            self.graph[a] = {}
        self.graph[a][b] = 1
        if self.graph.get(b) is None:
            self.graph[b] = {}
        self.graph[b][a] = 1

    def BFS_SP(self, strt_adrs, dest_adrs):
        explored = []
        queue = [[strt_adrs]]
        if strt_adrs == dest_adrs:
            return None
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node not in explored:
                neighbours = self.get_neighbours(node)
                for neighbour in neighbours:
                    new_path = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)
                    if neighbour == dest_adrs:
                        return new_path
                explored.append(node)
        return -1

    def get_neighbours(self, node):
        neighbs = self.graph[node]
        if neighbs is None:
            return []
        return neighbs.keys()