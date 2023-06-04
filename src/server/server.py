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

                if game.current_phase == 2:
                    game.resolve_turn()
                
                if req:
                    match req['req_type']:
                        case 'ready':
                            reply = {
                                'game_state': game.is_ready()
                            }
                        case 'turn':
                            # this returns the current phase of the turn
                            # main phase, response phase, resolve phase, ...
                            reply = game.get_turn_phase(req['p_side'])
                        case 'board':
                            # this returns the current board state, which is the fen string
                            # and the field effects
                            reply = {
                                'board_state': game.get_board_state(),
                                'occupy': game.get_occupation(req['p_side']),
                                'queued_move': game.get_queued_move(),
                                'displacements': game.get_displacements()
                            }
                        case 'hand':
                            # this returns the current hand states, including the players hand
                            # and the opponents hand
                            reply = game.get_hand_state(req['p_side'])
                        case 'pickup':
                            # this returns the legal moves for this players pieces
                            reply = {
                                'legal_moves': game.get_legal_moves(req['square'])
                            }
                        case 'move_piece':
                            game.queue_move(req['move'])
                            reply = {
                                'board_state': game.get_board_state(),
                                'occupy': game.get_occupation(req['p_side']),
                                'queued_move': game.get_queued_move()
                            }
                        case 'cast_spell':
                            reply = {
                                'valid_targets': game.cast_spell(req['p_side'], req['card'])
                            }
                        case 'play_cards':
                            reply = {
                                'quick_projection': game.queue_cards(req['p_side'], req['cards'])
                            }
                        case 'end_phase':
                            game.end_phase()
                            reply = {
                                'board_state': game.get_board_state(),
                                'occupy': game.get_occupation(req['p_side']),
                                'queued_move': game.get_queued_move()
                            }
                            if req['p_side'] == 'w':
                                game.playing_animation[0] = True
                            if req['p_side'] == 'b':
                                game.playing_animation[1] = True
                        case 'animation_finished':
                            if req['p_side'] == 'w':
                                game.playing_animation[0] = True
                            if req['p_side'] == 'b':
                                game.playing_animation[1] = True
                            reply = {
                                'success': True
                            }
                reply = json.dumps(reply)
                conn.sendall(str.encode(reply))
            else:
                break
        except Exception as e:
            print(e)
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