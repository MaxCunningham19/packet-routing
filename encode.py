
def encode(op: str, dest_address,data:bytes):
    bytesToSend = []

    bytesToSend.append(bytes(op, 'utf-8'))
    bytesToSend.append(bytes(dest_address[0], 'utf-8'))
    bytesToSend.append(bytes(str(dest_address[1]), 'utf-8'))

    if type(data) == str:
        bytesToSend.append(bytes(data, 'utf-8'))
    elif type(data) == bytes:
        bytesToSend.append(data)
    sending = bytes.join(b'_',bytesToSend)
    return sending


def decode(message: bytes):
    byteArr = message.split(b'_')
    op = byteArr[0].decode()
    ip = byteArr[1].decode()
    port = int(byteArr[2],base=10)
    return op,(ip,port), byteArr[3]

