import socket
import struct
import sys
import time

from op_codes import OPCODES
from utils import wait_for, getCompactSize, checksum
from messages import prepareVersionMessage, preparePayload, prepareGetBlockMessage, unpackBlock

MSG_BLOCK_TYPE = 2
HOST = "127.0.0.1"
PORT = 22556
GENESIS_BLOCK_HASH = "1a91e3dace36e2be3bf030a65679fe821aa1d6ef92e7c9902eb318182c355691"
BEST_HEIGHT = 3254000

file = open("scripts.txt","a")
last_hash_file = open("last_hash.txt","r")

blocks_count_saved = last_hash_file.readline()
last_hash = last_hash_file.readline()

last_hash_file.close()

# Connect to Dogecoin node
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

# Prepare Version Message
version_message = prepareVersionMessage(HOST, PORT)
payload = preparePayload(version_message, b'version')
# Send Version Message
s.send(payload)

# Received Version Message
# TODO: get start_height from version answer !
wait_for(s, b'version')

payload = preparePayload(b'', b'verack')
s.send(payload)
wait_for(s, b'verack')

blocks_count = 0

if len(last_hash) == 64:
    next_hash = last_hash
    blocks_count = int(blocks_count_saved)
else:
    next_hash = GENESIS_BLOCK_HASH

tmp = next_hash

blocks_list = []

while blocks_count < BEST_HEIGHT:

    # Wait 1min between batch to avoid overwhelming the node?
    #time.sleep(0.1)


    print("Asking for a new batch")
    get_blocks_message = prepareGetBlockMessage(next_hash)
    payload = preparePayload(get_blocks_message, b'getblocks')
    s.send(payload)

    l = 0
    while l <= 1:
        # if 1 count it means it juste tell usa about a new block
        inv_message = wait_for(s, b'inv')[24:]
        l, offset = getCompactSize(inv_message[0:9])

    print("l value is {}".format(l))

    if l == 501:
        # There are giving us an extra block (probably the latest block discover)
        l = 500

    for i in range(l):
        (type, hash) = struct.unpack('I32s', inv_message[offset+(36*i):offset+(36*(i+1))])
        blocks_list.append(hash[::-1].hex())
        # do we really need that ?
        assert(type == MSG_BLOCK_TYPE)
        if i == l-1:
            next_hash = hash[::-1].hex()

    # We can send the message now
    payload = preparePayload(inv_message, b'getdata')
    s.send(payload)
    count = l

    log = ''

    # Wait for 500 responses !
    while count > 0:

        # Received Inv Message
        data = wait_for(s, b'block')

        if data == 0:
            print("ERROR : missing block")
            sys.exit()

        # verify data
        magic, command, m_length, chcksm = struct.unpack('4s12sI4s', data[0:24])
        if b'block' not in command:
            print("ERROR : wrong command")
            sys.exit()

        if len(data[24:]) != m_length:
            print("ERROR : Wrong length")
            sys.exit()


        block_message = data[24:]
        count -= 1

        hash = checksum(block_message[0:80])[::-1].hex()

        blocks_list.remove(hash)

        print("Count : {} - Block hash {}".format(blocks_count + 500 - count, hash))
        log += "----- {} -----\n".format(hash)

        auxpow_activated = False
        if blocks_count + 500 - count > 371336:
            auxpow_activated = True

        try:
            txouts = unpackBlock(block_message, auxpow_activated)
        except Exception as e:
            bug_file = open("bug/{}.txt".format(hash), "w")
            print(e)
            bug_file.write(data.hex())
            sys.exit()


        for txout in txouts:
            log += "{}\n".format(txout.hex())

    if len(blocks_list) > 0:
        print("SOMETHING WENT REALLY WRONG")
        sys.exit()
    else :
        # Write by batch of 500 to speed up
        file.write(log)
        last_hash_file = open("last_hash.txt","w")
        last_hash_file.write(str(blocks_count+l))
        last_hash_file.write('\n')
        last_hash_file.write(next_hash)
        last_hash_file.close()

        tmp = next_hash
        blocks_count += l
