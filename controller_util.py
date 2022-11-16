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
    def __init__(self, socket: socket.socket, graph_table,flow_table:dict):
        self.socket = socket
        self.graph = {}
        self.flow_table = flow_table
        self.build_graph(graph_table)
        self.socket.settimeout(TIMEOUT)

    def run(self):
        while True:
            cur_adrs, op, oth_adrs,info = self.recieve()
            if op == c.FIND:
                next_adrs = self.find_next_addrs(cur_adrs, oth_adrs)
                self.send(cur_adrs,c.ACK,next_adrs)
            elif op == c.FLOW:
                self.send_table(cur_adrs)
            else:
                self.send(cur_adrs,c.NAK,'')

    def recieve(self):
        while True:
            try:
                data = self.socket.recvfrom(BUFFERSIZE)
                op, dest_adrs ,info = enc.decode(data[0])
                return data[1], op, dest_adrs, info
            except TimeoutError:
                continue

    def find_next_addrs(self, cur_adrs, dest_adrs): 
        cur_table = self.flow_table.get(cur_adrs)
        

        # path = self.BFS_SP(cur_adrs, dest_adrs)
        # if path is None :
        #     return c.DEST
        # if path == -1:
        #     return c.DROP
        # return path[1]
    
    def send(self, address, op, data):
        print(op, data, address)
        ret = enc.encode(op,data)
        self.socket.sendto(ret, address)

    def send_table(self, cur_address):
        cur_table = self.flow_table.get(cur_address)
        if cur_table is not None:
            for row in cur_table:
                self.send_row(cur_address,row[0],row[1],row[2])
        else:
            self.send(cur_address, c.NAK,'')

    def send_row(self,cur_address,prefix,dest_adrs,interface):
        data = enc.encode_data(prefix,interface)
        msg = enc.encode(c.FLOWMOD,dest_adrs,data)
        while True:
            try:
                self.socket.sendto(msg,cur_address)
                recived,recived_adrs = self.socket.recvfrom(BUFFERSIZE)
                if self.equal_address(recived_adrs,cur_address):
                    op, _, _ = enc.decode(recived)
                    if op == c.ACK:
                        return
            except TimeoutError:
                continue

    def equal_address(self, adrs1, adrs2):
        return adrs1[0] == adrs2[0] and adrs1[1] == adrs2[1]

    def build_graph(self,table):
        for row in table:
            self.add_edge([row[0],row[1]])

    def add_edge(self, edge):
        a, b = edge[0], edge[1]
        if self.graph.get(a) is None:
            self.graph[a] = {}
        self.graph[a][b] = 1
        if self.graph.get(b) is None:
            self.graph[b] = {}
        self.graph[b][a] = 1

    def remove_edge(self,edge):
        try:
            del self.graph[edge[0]][edge[1]]
            del self.graph[edge[1]][edge[0]]
        except:
            return

    def remove_node(self,node):
        try:
            del self.graph[node]
            for n in self.graph.keys():
                del self.graph[n][node] 
        except:
            return

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