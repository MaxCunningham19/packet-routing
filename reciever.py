import socket
import constants as c
import encode as enc
hostname = socket.gethostname()
print(hostname,socket.gethostbyname_ex(hostname))
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind((socket.gethostbyname_ex(hostname)[2][1],c.PORT))
print(client.getsockname())
ack = enc.encode(c.ACK,client.getsockname(),'')

while True:
  msg = client.recvfrom(1024)
  client.sendto(ack,msg[1])
  print(msg)