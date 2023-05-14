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
    conn.send(str.encode(json.dumps({
        'p': p,
        'game_id': game_id,
    })))
    
    reply : dict[str, str | list[str]] = {}
    while True:
        try:
            req = json.loads(conn.recv(4096).decode())
            if game_id in games:
                game = games[game_id]
                
                if req:
                    match req['req_type']:
                        case 'board':
                            reply = {
                                'board_state': game.get_board_state(),
                                'ffx_state': game.get_ffx_state(),
                                'occupy': game.get_occupation(req['p_side'])
                            }
                        case 'pickup':
                            legal_moves = game.get_legal_moves(req['square'])
                            reply = {
                                'legal_moves': legal_moves
                            }
                        case 'move':
                            game.make_move(req['move'])
                            reply = {'res': True}
                        case 'ready':
                            reply = {
                                'game_state': game.is_ready()
                            }
                        case 'hand':
                            reply = game.get_hand_state(req['p_side'])
                        case 'play_card':
                            game.play_card(req['card_play'])
                            reply = {'res': True}
                reply = json.dumps(reply)
                conn.sendall(str.encode(reply))
            else:
                break
        except Exception as e:
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