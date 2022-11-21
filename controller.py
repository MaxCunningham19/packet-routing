import socket
import controller_util as util
import constants as c
bufferSize = 1024
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((socket.gethostbyname_ex(socket.gethostname())[2][1],c.PORT))
print("Controller started @",sock.getsockname())

router1 = '172.20.9.3'
router2 = '172.20.9.4'

graph = {
    router1:{router2},
    router2:{router1},
    # '172.20.5.5':{'172.20.5.3'}
}

conn_table = [
    [[router1],'172.20.1'],
    [[router1,router2],'172.20.2'],
    [[router2,],'172.20.3'],
    # [['172.20.5.5'],'172.20.4'],
]

info_table = {
    router1:[('172.20.1.2',c.PORT),('172.20.2.2',c.PORT)],
    router2:[('172.20.2.4',c.PORT),('172.20.3.2',c.PORT)],
    #'172.20.5.4':[('172.20.3.2',c.PORT),('172.20.4.1',c.PORT)],
}

controller = util.Controller(sock,graph,info_table,conn_table)
controller.run()
