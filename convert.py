f = open("op_return.txt", "r")

op_return_list = f.readlines()

for script in op_return_list:
    script_bytes = bytes.fromhex(script.rstrip())[2:]
    try:
        print(script_bytes.decode('utf-8'))
    except:
        pass
