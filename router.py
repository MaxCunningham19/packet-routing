import socket
import router_util as util
import constants as c
from typing import List

def is_controller_network(adrs):
    return adrs.startswith(c.CTRLNET)


PORT = 54321
bufferSize = 1024
hostname = socket.gethostname()
print(socket.gethostbyname_ex(hostname))
sockets : List[socket.socket]= []
contrl_con = None
table = []
for i in range(1,len(socket.gethostbyname_ex(hostname)[2])):
    if is_controller_network(socket.gethostbyname_ex(hostname)[2][i]):
        contrl_con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        contrl_con.bind((socket.gethostbyname_ex(hostname)[2][i],PORT))
    else:
        table.append([c.getPrefix(socket.gethostbyname_ex(hostname)[2][i]),c.IN_NETWORK,len(sockets)])#
        sockets.append(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        sockets[len(sockets)-1].bind((socket.gethostbyname_ex(hostname)[2][i],PORT))

# sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock1.bind(('router1', PORT)) #bind to all interfaces
print(table)
router = util.Router(sockets,contrl_con,c.CTLR_ADRS,table)
router.run()