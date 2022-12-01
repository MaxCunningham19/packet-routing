import socket
import controller_util as util
import constants as c
bufferSize = 1024
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((socket.gethostbyname_ex(socket.gethostname())[2][1],c.PORT))
print("Controller started @",sock.getsockname())

router1 = '172.20.9.3'
router2 = '172.20.9.4'

# graph = {
#     router1:{router2},
#     router2:{router1},
#     # '172.20.5.5':{'172.20.5.3'}
# }

# conn_table = {
#     '172.20.1':[router1],
#     '172.20.2':[router1,router2],
#     '172.20.3':[router2],
#     # [['172.20.5.5'],'172.20.4'],
# }

router1 = '172.20.9.3'
router1_info = [('172.20.1.2',c.PORT),('172.20.2.2',c.PORT)]
router2 = '172.20.9.4'
router2_info = [('172.20.2.3',c.PORT),('172.20.3.2',c.PORT)]
# info_table = {
#     router1:[('172.20.1.2',c.PORT),('172.20.2.2',c.PORT)],
#     router2:[('172.20.2.3',c.PORT),('172.20.3.2',c.PORT)],
#     '172.20.9.5':[('172.20.3.2',c.PORT),('172.20.4.1',c.PORT)],
# }

controller = util.Controller(sock)
controller.print_info()
controller.add_router(router1,router1_info)
controller.print_info()
print(controller.find_next_addrs((router1,c.PORT),('172.20.3.6',c.PORT)))
controller.add_router(router2,router2_info)
controller.print_info()
print(controller.find_next_addrs((router1,c.PORT),('172.20.3.6',c.PORT)))
controller.remove_router(router1)
controller.print_info()
print(controller.find_next_addrs((router1,c.PORT),('172.20.3.6',c.PORT)))