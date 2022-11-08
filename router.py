import socket
import router_util as util
IP = "127.0.0.1"
PORT = 8080
bufferSize = 1024
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP, PORT))
print("Router started @",IP,PORT)

router = util.Router(sock,[(("127.0.0.1",8000),("127.0.0.1",8001))])
router.run()