import struct
import datetime
import socket

from utils import reverse_hash, getCompactSize, checksum

PROTOCOL_VERSION = 70004

def prepareVersionMessage(host, port):
    version_message = struct.pack('i', PROTOCOL_VERSION)
    version_message += struct.pack('Q', 4)
    version_message += struct.pack('q', int(datetime.datetime.now().timestamp()))
    version_message += struct.pack('Q', 1)
    version_message += struct.pack('>16s', b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'+socket.inet_aton(host))
    version_message += struct.pack('>H', port)
    version_message += struct.pack('Q', 4)
    version_message += struct.pack('>16s', b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff'+socket.inet_aton("127.0.0.1"))
    version_message += struct.pack('>H', port)
    version_message += struct.pack('Q', 0)
    version_message += struct.pack('B', 0)
    version_message += struct.pack('i', 0)
    version_message += struct.pack('?', False)

    return version_message

def prepareGetBlockMessage(hash):
    get_blocks_message = struct.pack('i', PROTOCOL_VERSION)
    get_blocks_message += struct.pack('B', 1)
    get_blocks_message += struct.pack('32s', reverse_hash(bytes.fromhex(hash)))
    get_blocks_message += struct.pack('>32s', b'\x00'*32)

    return get_blocks_message

def preparePayload(message, command):
    #payload = struct.pack('4s', b'\xfc\xc1\xb7\xdc')
    payload = struct.pack('4s', b'\xc0\xc0\xc0\xc0')
    payload += struct.pack('12s', command)
    payload += struct.pack('I', len(message))
    payload += struct.pack('4s', checksum(message)[0:4])
    payload += message

    return payload

def unpackBlock(block_message, auxpow_activated=False):
    txouts = []

    #print(block_message.hex())

    header = struct.unpack('80s', block_message[0:80])[0]
    offset = 80

    version = struct.unpack('I', block_message[0:4])[0]

    if auxpow_activated and version >= 6422787:
        # We want to the auxpow header
        version = struct.unpack('I', block_message[offset:offset+4])
        offset += 4

        num_txin, o = getCompactSize(block_message[offset:offset+9])
        offset += o

        for txin_i in range(num_txin):
            previous_output = struct.unpack('36s',block_message[offset:offset+36])[0]
            offset += 36
            signature_size, o = getCompactSize(block_message[offset:offset+9])
            offset += o

            signature_script = struct.unpack('{}s'.format(signature_size), block_message[offset:offset+signature_size])[0]
            offset += signature_size
            sequence = struct.unpack('I'.format(signature_size), block_message[offset:offset+4])[0]
            offset += 4

        # Reading TXOUTs
        num_txout, o = getCompactSize(block_message[offset:offset+9])
        offset += o

        for txout_i in range(num_txout):
            value = struct.unpack('Q', block_message[offset:offset+8])[0]
            offset += 8

            pk_script_size, o = getCompactSize(block_message[offset:offset+9])
            offset += o

            pk_script = struct.unpack('{}s'.format(pk_script_size), block_message[offset:offset+pk_script_size])[0]
            offset += pk_script_size

        lock_time = struct.unpack('I', block_message[offset:offset+4])[0]
        offset += 4

        parent_hash = struct.unpack('32s',block_message[offset:offset+32])[0]
        offset += 32
        num_merkle_branch, o = getCompactSize(block_message[offset:offset+9])
        offset += o

        for i_branch in range(num_merkle_branch):
            merkle_hash = struct.unpack('32s',block_message[offset:offset+32])[0]
            offset += 32

        bitmask = struct.unpack('4s',block_message[offset:offset+4])[0]
        offset += 4

        num_merkle_branch, o = getCompactSize(block_message[offset:offset+9])
        offset += o

        for i_branch in range(num_merkle_branch):
            merkle_hash = struct.unpack('32s',block_message[offset:offset+32])[0]
            offset += 32

        bitmask = struct.unpack('4s',block_message[offset:offset+4])[0]
        offset += 4

        parent_block_header = struct.unpack('80s', block_message[offset:offset+80])[0]
        offset += 80

        ###### END OF AUX POW BLOCK ######

    # Getting number of txs in block
    l, o = getCompactSize(block_message[offset:offset+9])
    offset += o


    for tx_i in range(l):
        version = struct.unpack('I',block_message[offset:offset+4])
        offset += 4

        # Reading TXINs
        num_txin, o = getCompactSize(block_message[offset:offset+9])
        offset += o


        for txin_i in range(num_txin):
            previous_output = struct.unpack('36s',block_message[offset:offset+36])[0]
            offset += 36
            signature_size, o = getCompactSize(block_message[offset:offset+9])
            offset += o


            signature_script = struct.unpack('{}s'.format(signature_size), block_message[offset:offset+signature_size])[0]
            offset += signature_size
            sequence = struct.unpack('I'.format(signature_size), block_message[offset:offset+4])[0]
            offset += 4

        # Reading TXOUTs
        num_txout, o = getCompactSize(block_message[offset:offset+9])
        offset += o

        for txout_i in range(num_txout):
            value = struct.unpack('Q', block_message[offset:offset+8])[0]
            offset += 8

            pk_script_size, o = getCompactSize(block_message[offset:offset+9])
            offset += o

            pk_script = struct.unpack('{}s'.format(pk_script_size), block_message[offset:offset+pk_script_size])[0]
            offset += pk_script_size

            txouts.append(pk_script)

        lock_time = struct.unpack('I', block_message[offset:offset+4])[0]
        offset += 4

    return txouts
