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


class Controller():
    def __init__(self, socket: socket.socket, graph:dict, info_table:dict, connect_table:list):
        self.socket = socket
        self.graph = graph
        self.conn_table = connect_table
        # self.build_graph(connect_table)
        self.info_table = info_table
        self.socket.settimeout(TIMEOUT)

    def run(self):
        while True:
            cur_adrs, op, oth_adrs, _ = self.recieve()
            if op == c.FIND:
                next_adrs = self.find_next_addrs(cur_adrs, oth_adrs)
                self.send(cur_adrs, c.ACK, next_adrs)
            # elif op == c.FLOW:
            #     self.send_table(cur_adrs)
            # elif op == c.ADD:
            #     self.add_node(cur_adrs)
            else:
                self.send(cur_adrs, c.NAK, '')

    def recieve(self):
        while True:
            try:
                data = self.socket.recvfrom(BUFFERSIZE)
                op, dest_adrs, info = enc.decode(data[0])
                return data[1], op, dest_adrs, info
            except TimeoutError:
                continue

    # def add_node(self, cur_adrs):

    #     if not self.in_table(cur_adrs):
    #         while True:
    #             try:
    #                 data = self.socket.recvfrom(BUFFERSIZE)
    #                 if self.equal_address(data[1],cur_adrs):
    #                     op, adrs, info = enc.decode(data[0])
    #                     if op == c.ADD:
    #                         net_work, soc = enc.decode_data(info)
    #                         self.add_to_table()

    #             except TimeoutError:
    #                 continue
    #     else:
    #          self.sendNAK(cur_adrs)

    # def in_table(self, adrs):

    # def sendNAK(self,cur_adrs):
    #     try:
    #         self.socket.sendto(enc.encode(c.NAK,cur_adrs,''),cur_adrs)
    #     except TimeoutError:
    #         return

    # def sendACK(self,cur_adrs):
    #     try:
    #         self.socket.sendto(enc.encode(c.ACK,cur_adrs,''),cur_adrs)
    #     except TimeoutError:
    #         return

    def find_next_addrs(self, cur_adrs, dest_adrs):
        dest_indxs = self.find_possible_dests(dest_adrs)
        start_indx = self.find_start_index(cur_adrs)
        if len(dest_indxs) == 0 or start_indx == -1:
            return c.DROP
        path = self.BFS_SP(start_indx, dest_indxs)
        if path is None:
            return dest_adrs
        if path == -1:
            return c.DROP
        return self.get_next_hop(path)

    def find_possible_dests(self, dest_adrs):
        adrses = []
        len_pref = -1
        for row in self.conn_table:
            if dest_adrs[0].startswith(row[1]):
                if len(row[1]) > len_pref and len(row[0])>=1:
                    adrses = []
                    for v in row[0]:
                        adrses.append(v)
                    len_pref = len(row[1])
        return adrses

    def find_start_index(self, cur_adrs):
        keys = self.info_table.keys()
        for adrs in keys:
            if cur_adrs[0] == adrs:
                return adrs
        return -1

    def get_next_hop(self, path):
        cur = path[0]
        next = path[1]
        info_cur = self.info_table.get(cur)
        info_next = self.info_table.get(next)
        for adrs in info_cur:
            tmp = adrs[0].split('.')
            tmp = tmp[0:3]
            tmp = '.'.join(tmp)
            for adrs2 in info_next:
                if adrs2[0].startswith(tmp):
                    return adrs2
        return c.DROP

    def send(self, address, op, next_adrs):
        print(op, next_adrs, address)
        ret = enc.encode(op, next_adrs, '')
        self.socket.sendto(ret, address)

    # def send_table(self, cur_address):
    #     cur_table = self.flow_table.get(cur_address)
    #     if cur_table is not None:
    #         for row in cur_table:
    #             self.send_row(cur_address, row[0], row[1], row[2])
    #     else:
    #         self.send(cur_address, c.NAK, '')

    def send_row(self, cur_address, prefix, dest_adrs, interface):
        data = enc.encode_data(prefix, interface)
        msg = enc.encode(c.FLOWMOD, dest_adrs, data)
        while True:
            try:
                self.socket.sendto(msg, cur_address)
                recived, recived_adrs = self.socket.recvfrom(BUFFERSIZE)
                if self.equal_address(recived_adrs, cur_address):
                    op, _, _ = enc.decode(recived)
                    if op == c.ACK:
                        return
            except TimeoutError:
                continue

    def equal_address(self, adrs1, adrs2):
        return adrs1[0] == adrs2[0] and adrs1[1] == adrs2[1]

    def build_graph(self, conn_table):
        self.graph = {}
        for row in conn_table:
            for i in range(len(row[0])):
                for j in range(i+1, len(row[0])):
                    self.add_edge([row[0][i], row[0][j]])

    def add_edge(self, edge):
        a, b = edge[0], edge[1]
        if self.graph.get(a) is None:
            self.graph[a] = {}
        self.graph[a][b] = 1
        if self.graph.get(b) is None:
            self.graph[b] = {}
        self.graph[b][a] = 1

    def remove_edge(self, edge):
        try:
            del self.graph[edge[0]][edge[1]]
            del self.graph[edge[1]][edge[0]]
        except:
            return

    def remove_node(self, node):
        try:
            if self.graph.get(node) is not None:
                del self.graph[node]
            for n in self.graph.keys():
                if self.graph.get(n).get(node) is not None:
                    del self.graph[n][node]
        except:
            return

    def BFS_SP(self, strt_adrs, dest_adrses: list):
        explored = []
        queue = [[strt_adrs]]
        if self.isIncluded(strt_adrs, dest_adrses):
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
                    if self.isIncluded(neighbour, dest_adrses):
                        return new_path
                explored.append(node)
        return -1

    def isIncluded(self, adrs, dest_adrses: List):
        for x in dest_adrses:
            if x == adrs:
                return True
        return False

    def get_neighbours(self, node):
        neighbs = self.graph[node]
        if neighbs is None:
            return []
        return list(neighbs)
