import socket
import encode as enc
import constants as c

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(('client',0))
server_adrs = ('router1',c.PORT)
reciever_adrs = ('172.20.2.3',c.PORT)
print(client.getsockname())
while True:
  out_data = input()
  client.sendto(enc.encode('',reciever_adrs,out_data),server_adrs)
  if out_data=='bye':
    break
