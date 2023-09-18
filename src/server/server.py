#!/usr/bin/env python
import socket, _thread, sys, json, os
from game import Game

server = os.getenv('SERVER')
port = int(os.getenv('PORT'))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.settimeout(1.0)
s.listen(2)
print('Server has started, waiting for a connection...')

games : dict[int, Game] = {}
id_count = 0

def threaded_client(conn: socket.socket):
    req = json.loads(conn.recv(4096).decode())
    if req['connection'] == 'create':
        # generate gameid and create game
        side = 1
        game_id = -1
        for i in range(100):
            if i not in games:
                game_id = i
                break
        if game_id == -1:
            conn.send(str.encode(json.dumps({
                'status': 'server_is_busy'
            })))
            return
        games[game_id] = Game(game_id)
    else:
        game_id = req['game_id']
        if game_id not in games:
            conn.send(str.encode(json.dumps({
                'status': 'game_does_not_exist'
            })))
            return
        side = -1

    conn.send(str.encode(json.dumps({
        'status': 'success',
        'side': side,
        'game_id': game_id,
    })))
    
    while True:
        try:
            req = json.loads(conn.recv(4096).decode())
            if game_id in games:
                game = games[game_id]
                
                game.connected[side] = True
                
                if not all([connected for connected in game.connected.values()]):
                    res = {
                        'status': 'wait'
                    }
                elif 'method' in req:
                    res = game.request(req)
                else:
                    res = {
                        'status': 'success'
                    }

                res = json.dumps(res)
                conn.sendall(str.encode(res))
            else:
                break
        except Exception as e: 
            print('Exception in threaded_client()')
            print(e)
            break

    print('lost connection')
    try:
        del games[game_id]
        print(f'closing game {game_id}')
    except:
        pass
    conn.close()

if __name__ == '__main__':
    while True:
        conn = None
        try:
            conn, addr = s.accept()
            print(f'Connected to {addr}')

            _thread.start_new_thread(threaded_client, (conn,))
        except socket.timeout:
            pass
        except KeyboardInterrupt:
            if conn is not None:
                conn.close()
            break