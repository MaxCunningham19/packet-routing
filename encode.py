
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

def encode_data(dest_pref, soc):
    bytesToSend = []
    bytesToSend.append(bytes(dest_pref, 'utf-8'))
    bytesToSend.append(bytes(soc, 'utf-8'))
    sending = bytes.join(b'*',bytesToSend)
    return sending


def decode(message: bytes):
    byteArr = message.split(b'_')
    op = byteArr[0].decode()
    ip = byteArr[1].decode()
    port = int(byteArr[2],base=10)
    return op,(ip,port), byteArr[3]

def decode_data(data:bytes):
    byteArr = data.split(b'*')
    dest_pref = byteArr[0].decode()
    soc = int(byteArr[1],base=10)
    return dest_pref, soc
