import socket
from typing import List
from collections import defaultdict
import constants as c
import encode as enc
import time

BUFFERSIZE = 1024
DEST_TBL_I = 0
FRWR_TBL_I = 1
EMPTY_ROW = -1
MAX_TIME = c.TIMEOUT * c.TIMEOUT_MUL * 3

class Controller():
    def __init__(self, socket: socket.socket ):
        self.timers = {}
        self.socket = socket
        self.info_table = {}
        self.graph = {}
        self.conn_table = {}
        self.socket.settimeout(c.TIMEOUT*2)

    def print_info(self):
        print('\n',self.info_table,'\n\n', self.conn_table, '\n\n', self.graph, '\n')

    def run(self):
        while True:
            cur_adrs, op, oth_adrs, _ = self.recieve()
            if not self.is_router(cur_adrs):
                self.new_router(cur_adrs)
                self.timers[cur_adrs[0]] = time.time()
            else:
                self.timers[cur_adrs[0]] = time.time()
            if op == c.FIND:
                    next_adrs = self.find_next_addrs(cur_adrs, oth_adrs)
                    print(cur_adrs, c.FLOWMOD, next_adrs)
                    self.send(cur_adrs, c.FLOWMOD, next_adrs)
            elif op == c.HELLO:
                
                self.send(cur_adrs, c.ACK, cur_adrs)
            else:
                self.send(cur_adrs, c.NAK, cur_adrs)

    def new_router(self, adrs):
        router_info : set = set()
        while True:
            try:
                self.socket.sendto(enc.encode(c.FLOW,adrs,''),adrs)
                (data,cur_adrs) = self.socket.recvfrom(BUFFERSIZE)
                if self.equal_address(cur_adrs,adrs):
                    op,addy, _ = enc.decode(data)
                    if op == c.FLOWMOD:
                        router_info.add(addy)
                        self.socket.sendto(enc.encode(c.ACK,addy,''),adrs)
                        break
                else:
                    self.socket.sendto(enc.encode(c.NAK,cur_adrs,''),cur_adrs)
            except TimeoutError:
                continue

        while True:
            try:
                (data,cur_adrs) = self.socket.recvfrom(BUFFERSIZE)
                if self.equal_address(cur_adrs,adrs):
                    op,addy, _ = enc.decode(data)
                    if op == c.FLOWMOD:
                        router_info.add(addy)
                        self.socket.sendto(enc.encode(c.ACK,addy,''),adrs)
                    if op == c.ACK and self.equal_address(addy, c.DROP):
                        self.socket.sendto(enc.encode(c.ACK,c.DROP,''),cur_adrs)
                        break
                else:
                    self.socket.sendto(enc.encode(c.NAK,cur_adrs,''),cur_adrs)
            except TimeoutError:
                continue

        inf = []
        for val in router_info:
            inf.append(val)
        self.add_router(adrs[0],inf)

    def recieve(self):
        count = 0
        while True:
            try:
                data = self.socket.recvfrom(BUFFERSIZE)
                op, dest_adrs, info = enc.decode(data[0])
                return data[1], op, dest_adrs, info
            except TimeoutError:
                self.print_info()
                if count%5 == 0:
                    self.check_timers()
                count = count + 1
                continue

    def check_timers(self):
        to_be_removed = []
        for router in self.timers.keys():
            if self.timers[router] + MAX_TIME < time.time():
                print('removing',router)
                to_be_removed.append(router)

        for r in to_be_removed:
            del self.timers[r]
            self.remove_router(r)

    def is_router(self, adrs):
        return self.info_table.get(adrs[0]) != None

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
        for key in self.conn_table:
            if dest_adrs[0].startswith(key):
                if len(key) > len_pref and len(key) >= 1:
                    adrses = []
                    for v in self.conn_table[key]:
                        adrses.append(v)
                    len_pref = len(key)
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
        try:
            ret = enc.encode(op, next_adrs, '')
            self.socket.sendto(ret, address)
        except TimeoutError:
            return

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

    def build_connection_table(self):
        self.conn_table = {}
        for router in self.info_table:
            for adrs in self.info_table[router]:
                pref = c.getPrefix(adrs[0])
                if self.conn_table.get(pref) is not None:
                    self.conn_table[pref].add(router)
                else:
                    self.conn_table[pref] = {router}

    def build_graph(self):
        self.graph = {}
        for key in self.conn_table:
            for c1 in self.conn_table[key]:
                for c2 in self.conn_table[key]:
                    if c1 is not c2:
                        self.add_edge([c1,c2])

    def add_edge(self, edge):
        a, b = edge[0], edge[1]
        if self.graph.get(a) is None:
            self.graph[a] = {b}
        else:
            self.graph[a].add(b)
        if self.graph.get(b) is None:
            self.graph[b] = {a}
        else:
            self.graph[b].add(a)

    def remove_edge(self, edge):
        try:
            del self.graph[edge[0]][edge[1]]
            del self.graph[edge[1]][edge[0]]
        except:
            return

    def add_router(self, router_address:tuple, router_info:list):
        self.info_table[router_address] = router_info
        self.add_to_conn_table_and_graph(router_address, router_info)
    
    def add_to_conn_table_and_graph(self,router_address:tuple, router_info:list):
        for (address,_) in router_info:
            pref = c.getPrefix(address)
            if self.conn_table.get(pref) is not None:
                for adrs in self.conn_table[pref]:
                    self.add_edge([adrs,router_address])
                self.conn_table[pref].add(router_address)
            else:
                self.conn_table[pref] = {router_address}


    def remove_router(self, router_address):
            if self.info_table.get(router_address) is not None:
                del self.info_table[router_address]
                self.remove_node(router_address)
                self.remove_conns(router_address)

    def remove_node(self, router_address):
        if self.graph.get(router_address) is not None:
            del self.graph[router_address]
        
        for key in self.graph.keys():
            if router_address in self.graph[key]:
                self.graph[key].remove(router_address)
        return

    def remove_conns(self,router_address):
        to_be_deleted = []
        for pref in self.conn_table.keys():
            if router_address in self.conn_table[pref]:
                to_be_deleted.append((pref,router_address))
        
        for (pref,r_adrs) in to_be_deleted:
            self.conn_table[pref].remove(r_adrs)
            if len(self.conn_table[pref]) == 0:
                del self.conn_table[pref]


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
