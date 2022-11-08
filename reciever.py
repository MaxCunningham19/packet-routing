import socket
SERVER = "127.0.0.1"
PORT = 8080
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("127.0.0.1",8001))
server_adrs = (SERVER,PORT)
while True:
  msg = client.recv(1024)
  print(msg)