import socket
import encode as enc
import constants as c

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(('client',c.PORT))
server_adrs = ('172.20.1.3',c.PORT)
reciever_adrs = ('172.20.2.3', c.PORT)
print(client.getsockname())

count = 0
while True:
  # if count % 3 ==0:
  #   IP_adrs = '172.20.2.3'
  # else:
  #   IP_adrs = '172.20.3.3'
  IP_adrs = input('ip: ')
  data = input('data: ')
  client.sendto(enc.encode('',(IP_adrs,c.PORT),data),server_adrs)
  count = count + 1
  if data=='bye':
    break
