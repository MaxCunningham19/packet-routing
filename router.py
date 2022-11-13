import socket
import router_util as util
import constants as c
from typing import List

PORT = 54321
bufferSize = 1024
hostname = socket.gethostname()
print(socket.gethostbyname_ex(hostname))
sockets : List[socket.socket]= []
for i in range(1,len(socket.gethostbyname_ex(hostname)[2])):
    sockets.append(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
    sockets[len(sockets)-1].bind((socket.gethostbyname_ex(hostname)[2][i],PORT))

# sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock1.bind(('router1', PORT)) #bind to all interfaces
d_name = input("docker name: ")
if d_name == "router1":
    table = [
        ["172.20.1",c.IN_NETWORK,1],
        ["172.20.2",c.IN_NETWORK,0],
        ["172.20.3",('172.20.2.4',c.PORT),0],
    ]
else:
    table = [
        ["172.20.1",('172.20.2.2',c.PORT),0],
        ["172.20.2",c.IN_NETWORK,0],
        ["172.20.3",c.IN_NETWORK,1]
    ]

router = util.Router(sockets,table)
router.run()