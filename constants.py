FIND = 'FIND'
ACK = 'ACK'
ADD = 'ADD'
DEST = 'DEST'
DROP = ('0.0.0.0',0)
NAK = 'NAK'
FLOW = 'FLOW'
FLOWMOD = 'FLOWMOD'
HELLO = 'HELLO'
SEND = 'SEND'
IN_NETWORK = "in_network"
CTRLNET = '172.20.9.'
PORT = 54321
CTLR_ADRS = ('172.20.9.2',PORT)

def getPrefix(adrs:str):
    try:
        sp = adrs.split('.')
        pre = '.'.join(sp[:3])
        return pre
    except:
        return '0.0.0.0'