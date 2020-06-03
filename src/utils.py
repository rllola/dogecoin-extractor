import hashlib
import struct
import time

def wait_for(s, command_expected):
    waiting = True
    while waiting:
        #print("Waiting for {}".format(command_expected))
        data = b''
        empty_call = 0
        while len(data) < 24:
            # we might not have 24 bytes...
            data_received = s.recv(24 - len(data))
            if data_received == b'':
                empty_call += 1
                time.sleep(1)
                if empty_call > 120:
                    print("Receiving nothing !")
                    print(data.hex())
                    return 0
            data += data_received
        if len(data) == 24:
            magic, command, m_length, chcksm = struct.unpack('4s12sI4s', data)
            message = b''
            if command_expected in command:
                waiting = False
                #print("Recived {} message".format(command_expected))
                while len(message) < m_length:
                    message_recv = s.recv(m_length - len(message))
                    message += message_recv
                data = data + message
                if m_length != len(message):
                    print(len(message))
                    print(m_length)
                    raise Exception('Invalid message length')
            else:
                f = open("unknown.txt", "w")
                f.write(data.hex()+'\n')
                trash = s.recv(m_length)
                f.write(trash.hex()+'\n')
                f.close()

    return data

def checksum(m):
    hash = hashlib.sha256()
    hash.update(m)
    rehash = hashlib.sha256()
    rehash.update(hash.digest())
    return rehash.digest()

def reverse_hash(hash):
    reversed_hash = b''
    for b in hash:
        reversed_hash = b.to_bytes(1, byteorder='big') + reversed_hash
    return reversed_hash

def getCompactSize(data):
    size = data[0]
    offset = 1
    if size == 253:
        size = struct.unpack('H',data[offset:offset+2])[0]
        offset += 2
    elif size == 254:
        size = struct.unpack('I',data[offset:offset+4])[0]
        offset += 4
    elif size == 255:
        size = struct.unpack('Q',data[offset:offset+8])[0]
        offset += 8

    return size, offset
