import socket
import constants as c
hostname = socket.gethostname()
print(hostname,socket.gethostbyname_ex(hostname))
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind((socket.gethostbyname_ex(hostname)[2][1],c.PORT))
print(client.getsockname())
while True:
  msg = client.recvfrom(1024)
  print(msg)