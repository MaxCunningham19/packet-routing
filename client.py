import socket
SERVER = "127.0.0.1"
PORT = 8080
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_adrs = (SERVER,PORT)
while True:
  out_data = input()
  client.sendto(bytes(out_data,'UTF-8'),server_adrs)
  if out_data=='bye':
    break
