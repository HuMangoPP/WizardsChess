import socket, _thread, sys, json
from game import Game

server = '192.168.2.24'
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
print('Server has started, waiting for a connection...')

connected = set()
games : dict[int, Game] = {}
id_count = 0

def threaded_client(conn: socket.socket, p: str, game_id: int):
    global id_count 
    conn.send(str.encode(p))
    
    reply : dict[str, str | list[str]] = {}
    while True:
        try:
            req = json.loads(conn.recv(4096).decode())

            if game_id in games:
                game = games[game_id]
                
                if not req:
                    break
                else:
                    match req['req_type']:
                        case 'get':
                            reply = {
                                'board_state': game.get_board_state(),
                            }
                        case 'put':
                            game.make_move(req['move'])
                            reply = {
                                'board_state': game.get_board_state(),
                            }
                conn.sendall(json.dumps(reply))
            else:
                break
        except:
            break

    print('lost connection')
    try:
        del games[game_id]
        print(f'closing game {game_id}')
    except:
        pass
    id_count -= 1
    conn.close()

while True:
    conn, addr = s.accept()
    print(f'Connected to {addr}')

    p = 0
    game_id = id_count // 2
    id_count += 1
    if id_count % 2 == 1:
        games[game_id] = Game(game_id)
        print('creating a new game...')
    else:
        games[game_id].ready = True
        p = 1

    _thread.start_new_thread(threaded_client, (conn, 'w' if p == 0 else 'b', game_id))