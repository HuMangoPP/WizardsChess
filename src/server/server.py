import socket, _thread, sys, json

server = '192.168.2.24'
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
print('Server has started, waiting for a connection...')

def threaded_client(conn: socket.socket):
    conn.send(str.encode(json.dumps({
        'res': 'connected'
    })))
    reply = ''
    while True:
        try:
            data = json.loads(conn.recv(2048).decode())
            reply = data

            if not data:
                print('disconnected')
                break
            else:
                print(f'received {reply}')
                print(f'sending {reply}')

            conn.sendall(str.encode(json.dumps(reply)))
        except:
            break
    
    print('lost connection')
    conn.close()

while True:
    conn, addr = s.accept()
    print(f'Connected to {addr}')

    _thread.start_new_thread(threaded_client, (conn, ))