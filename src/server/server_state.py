
class FieldEffectsState:
    def __init__(self):
        # field effects are kept track of in a master list
        # the index of each element corresponds to the square number
        # and each element is a list of strings which is the
        # effect_id (name)
        self.effects = []
        self.on_start()
    
    def on_start(self):
        for i in range(64):
            self.effects.append([])

    def get_field_effects(self, square: int):
        return self.effects[square]

    def get_entire_field(self):
        return self.effects

    def update_field_effects(self, square: int, new_effects: list[str], func: str='write'):
        match func:
            case 'add':
                [self.effects[square].append(new_effect) for new_effect in new_effects]
            case 'del':
                [self.effects[square].remove(new_effect) for new_effect in new_effects]
            case 'write':
                self.effects[square] = new_effects

WHITE_PIECES = 'PNBRQK'
BLACK_PIECES = 'pnbrqk'
STARTING_FEN_STR = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -1 0 1'
SIDE_MAP = {'w': 0, 'b': 1}

def is_sliding_piece(piece: str) -> bool:
    if piece in 'brq':
        return True
    else:
        return False

def is_same_team(piece: str, other_piece: str | int) -> bool:
    if ('a' <= piece and piece <= 'z') and ('a' <= other_piece and other_piece <= 'z'):
        return True
    if ('A' <= piece and piece <= 'Z') and ('A' <= other_piece and other_piece <= 'Z'):
        return True
    return False

def get_piece_moves(board: list[str], piece: str, square: int, en_passant: int, 
                    castling_priv: dict[str, bool]) -> set[int]:
    moves = set() 
    piece_key = piece.lower()
    sliding = is_sliding_piece(piece_key)
    offsets = PIECE_OFFSETS[piece_key]
    x = square % 8
    y = square // 8
    if piece_key == 'p':
        new_y = y + 1 if piece == 'p' else y - 1
        # left capture, must be enemy piece or en passant
        new_x = x - 1
        if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
            if board[new_x + new_y * 8] != 0 and not is_same_team(piece, board[new_x + new_y * 8]):
                moves.add(new_x + new_y * 8)
            if new_x + new_y * 8 == en_passant: 
                moves.add(new_x + new_y * 8)
        # right capture, must be enemy or en passant
        new_x = x + 1
        if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
            if board[new_x + new_y * 8] != 0 and not is_same_team(piece, board[new_x + new_y * 8]):
                moves.add(new_x + new_y * 8)
            if new_x + new_y * 8 == en_passant: 
                moves.add(new_x + new_y * 8)
        # move forward, must be empty
        new_x = x
        if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
            if board[new_x + new_y * 8] == 0:
                moves.add(new_x + new_y * 8)
                # two square move
                new_y = y + 2 if piece == 'p' else y - 2
                if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
                    if board[new_x + new_y * 8] == 0:
                        if piece == 'P' and y == 6:
                            moves.add(new_x + new_y * 8)
                        if piece == 'p' and y == 1:
                            moves.add(new_x + new_y * 8)
    elif piece_key == 'k':
        # get the normal offsets for king
        for offset in offsets:
            new_x = x + offset[0]
            new_y = y + offset[1]
            if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
                # same team, cannot come to the square
                if board[new_x + new_y * 8] != 0 and is_same_team(piece, board[new_x + new_y * 8]):
                    continue
                moves.add(new_x + new_y * 8)
                # capture, cannot go further
                if board[new_x + new_y * 8] != 0 and not is_same_team(piece, board[new_x + new_y * 8]):
                    continue
        
        # check castling privileges
        # TODO: check through castle
        king_side = piece
        if castling_priv[king_side] and all([board[x + i + y * 8] == 0 for i in [1, 2]]):
            moves.add(x + 2 + y * 8)
        queen_side = 'q' if piece == 'k' else 'Q'
        if castling_priv[queen_side] and all([board[x + i + y * 8] == 0 for i in [-1, -2, -3]]):
            moves.add(x - 2 + y * 8)
    elif sliding:
        # sliding pieces can move as many as allowed, so this has some different logic
        for offset in offsets:
            i = 1
            new_x = x + offset[0] * i
            new_y = y + offset[1] * i
            while (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
                # same team, cannot come to the square
                if board[new_x + new_y * 8] != 0 and is_same_team(piece, board[new_x + new_y * 8]):
                    break
                moves.add(new_x + new_y * 8)
                # capture, cannot go further
                if board[new_x + new_y * 8] != 0 and not is_same_team(piece, board[new_x + new_y * 8]):
                    break
                i += 1
                new_x = x + offset[0] * i
                new_y = y + offset[1] * i
    else:
        # normal pieces only move at fixed offsets
        for offset in offsets:
            new_x = x + offset[0]
            new_y = y + offset[1]
            if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
                # same team, cannot come to the square
                if board[new_x + new_y * 8] != 0 and is_same_team(piece, board[new_x + new_y * 8]):
                    continue
                moves.add(new_x + new_y * 8)
    
    return moves

def get_piece_attacks(board: list[str], piece: str, square: int) -> set[int]:
    attacks = set()
    piece_key = piece.lower()
    sliding = is_sliding_piece(piece_key)
    offsets = PIECE_OFFSETS[piece_key]
    x = square % 8
    y = square // 8
    if piece_key == 'p':
        new_y = y + 1 if piece == 'p' else y - 1
        # left capture, must be enemy piece or en passant
        new_x = x - 1
        if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
            attacks.add(new_x + new_y * 8)
        # right capture, must be enemy or en passant
        new_x = x + 1
        if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
            attacks.add(new_x + new_y * 8)
    elif piece_key == 'k':
        # get the normal offsets for king
        for offset in offsets:
            new_x = x + offset[0]
            new_y = y + offset[1]
            if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
                attacks.add(new_x + new_y * 8)
    elif sliding:
        # sliding pieces can move as many as allowed, so this has some different logic
        for offset in offsets:
            i = 1
            new_x = x + offset[0] * i
            new_y = y + offset[1] * i
            while (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
                attacks.add(new_x + new_y * 8)
                # piece is here, cannot attack further
                if board[new_x + new_y * 8] != 0:
                    break
                i += 1
                new_x = x + offset[0] * i
                new_y = y + offset[1] * i
    else:
        # normal pieces only move at fixed offsets
        for offset in offsets:
            new_x = x + offset[0]
            new_y = y + offset[1]
            if (0 <= new_x and new_x < 8) and (0 <= new_y and new_y < 8):
                attacks.add(new_x + new_y * 8)
    
    return attacks

def get_attacked_squares(board: list[str], occupations: set[int]):
    attacked_squares = set()
    for occupation in occupations:
        piece = board[occupation]
        attacked_squares = attacked_squares.union(get_piece_attacks(board, piece, occupation))

    return attacked_squares

PIECE_OFFSETS = {
    'p': [[-1, -1], [0, -1], [1, -1]],
    'n': [[-1, -2], [1, -2], [2, -1], [2, 1], [1, 2], [-1, 2], [-2, 1], [-2, -1]],
    'b': [[-1, -1], [1, -1], [1, 1], [-1, 1]],
    'r': [[0, -1], [1, 0], [0, 1], [-1, 0]],
    'q': [[-1, -1], [1, -1], [1, 1], [-1, 1], [0, -1], [1, 0], [0, 1], [-1, 0]],
    'k': [[-1, -1], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0]]
}

class BoardState:
    def __init__(self, field_effects: FieldEffectsState, fen_str: str=STARTING_FEN_STR):
        # store the board state and occupied squares of either white or black
        self.board : list[str] = []
        self.white_occupied = set()
        self.black_occupied = set()
        self.on_start(fen_str)

        # store the next move to be played once the round ends
        self.queued_move = [-1, -1]

        self.field_effects = field_effects
    
    def on_start(self, fen_str: str):
        # read the fen_str
        data = fen_str.split(' ')
        position = data[0] # fen string
        self.move = SIDE_MAP[data[1]] # who is the leading player in the round
        self.castling_priv = {
            char: char in data[2] for char in 'KQkq'
        } 
        self.en_passant = int(data[3])
        self.half_moves = int(data[4])
        self.full_moves = int(data[5])
        self.king_positions = [-1, -1]

        square_index = 0
        for char in position:
            if char in WHITE_PIECES:
                self.board.append(char)
                self.white_occupied.add(square_index)
                if char == 'K':
                    self.king_positions[0] = square_index
                square_index += 1
            elif char in BLACK_PIECES:
                self.board.append(char)
                self.black_occupied.add(square_index)
                if char == 'k':
                    self.king_positions[1] = square_index
                square_index += 1
            elif char == '/':
                continue
            else:
                num_empty = int(char)
                for i in range(num_empty):
                    self.board.append(0)
                square_index += num_empty

    def get_fen_str(self) -> str:
        fen_str = ''
        # board state
        empty_counter = 0
        for i, square in enumerate(self.board):
            if i != 0 and i % 8 == 0:
                if empty_counter > 0:
                    fen_str += str(empty_counter)
                    empty_counter = 0
                fen_str += '/'
            if square == 0:
                empty_counter += 1
            else:
                if empty_counter > 0:
                    fen_str += str(empty_counter)
                    empty_counter = 0
                fen_str += square
        fen_str += ' '
        
        # which move
        fen_str += 'w ' if self.move == 0 else 'b '

        # castling privileges
        for castle in self.castling_priv:
            if self.castling_priv[castle]:
                fen_str += castle
            else:
                fen_str += '0'
        fen_str += ' '

        # en passant
        fen_str += str(self.en_passant)
        fen_str += ' '

        # half moves and full moves
        fen_str += f'{self.half_moves} {self.full_moves}'

        return fen_str

    def make_board_move(self) -> bool:
        old_square = self.queued_move[0]
        new_square = self.queued_move[1]

        if old_square == -1 or new_square == -1:
            return False
        moved_piece = self.board[old_square]

        # update occupations
        if self.move == 0:
            self.white_occupied.remove(old_square)
            self.white_occupied.add(new_square)
            if new_square in self.black_occupied:
                self.black_occupied.remove(new_square)
        else:
            self.black_occupied.remove(old_square)
            self.black_occupied.add(new_square)
            if new_square in self.white_occupied:
                self.white_occupied.remove(new_square)
        
        # update field effects for piece
        self.field_effects.update_field_effects(new_square, self.field_effects.get_field_effects(old_square))
        self.field_effects.update_field_effects(old_square, [])

        # pawn move
        en_passant = self.en_passant
        self.en_passant = -1
        if moved_piece in 'Pp':
            if new_square == en_passant: # en passant capture
                if self.move == 0:
                    self.black_occupied.remove(en_passant + 8)
                    self.field_effects.update_field_effects(en_passant + 8, [])
                else:
                    self.white_occupied.remove(en_passant - 8)
                    self.field_effects.update_field_effects(en_passant - 8, [])
                self.board[en_passant] = 0
            elif new_square - old_square == 16:
                self.en_passant = old_square + 8
            elif old_square - new_square == 16:
                self.en_passant = old_square - 8
        
        # castling
        if moved_piece in 'Kk':
            self.king_positions[self.move] = new_square
            if new_square - old_square == 2: # kingside castle
                self.board[new_square - 1] = self.board[new_square + 1]
                self.board[new_square + 1] = 0
                if self.move == 0:
                    self.white_occupied.add(new_square - 1)
                    self.white_occupied.remove(new_square + 1)
                else:
                    self.black_occupied.add(new_square - 1)
                    self.black_occupied.remove(new_square + 1)
                # update the field effect location
                self.field_effects.update_field_effects(new_square - 1, self.field_effects.get_field_effects(new_square + 1))
                self.field_effects.update_field_effects(new_square + 1, [])
            elif old_square - new_square == 2: # queenside castle
                self.board[new_square + 1] = self.board[new_square - 2]
                self.board[new_square - 2] = 0 
                if self.move == 0:
                    self.white_occupied.add(new_square + 1)
                    self.white_occupied.remove(new_square - 2)
                else:
                    self.black_occupied.add(new_square + 1)
                    self.black_occupied.remove(new_square - 2)
                self.field_effects.update_field_effects(new_square + 1, self.field_effects.get_field_effects(new_square - 2))
                self.field_effects.update_field_effects(new_square - 2, [])
            # remove castling privileges
            if self.move == 0:
                self.castling_priv['K'] = False
                self.castling_priv['Q'] = False
            else:
                self.castling_priv['k'] = False
                self.castling_priv['q'] = False
        
        # rook movements take away castling privileges
        if moved_piece == 'Rr':
            if old_square == 0:
                self.castling_priv['q'] = False
            elif old_square == 7:
                self.castling_priv['k'] = False
            elif old_square == 63:
                self.castling_priv['K'] = False
            elif old_square == 56:
                self.castling_priv['Q'] = False
        
        self.board[new_square] = moved_piece
        self.board[old_square] = 0
        self.queued_move = [-1, -1]
        self.move = (self.move + 1) % 2
        self.full_moves += self.half_moves
        self.half_moves = self.move

        return True

    def pickup_piece(self, square: int) -> set[int]:
        piece = self.board[square]
        pseudo_legal_moves = get_piece_moves(self.board, piece, square, self.en_passant, self.castling_priv)
        illegal_moves = set()
        for pl_move in pseudo_legal_moves:
            # "simulate making the move" to test whether it is legal or not
            board_cp = self.board.copy()
            white_occupied_cp = self.white_occupied.copy()
            black_occupied_cp = self.black_occupied.copy()

            # check capture and remove occupations
            if board_cp[pl_move] != 0:
                if self.move == 0:
                    black_occupied_cp.remove(pl_move)
                else:
                    white_occupied_cp.remove(pl_move)
            # update the board state
            board_cp[pl_move] = piece
            board_cp[square] = 0

            # en passant capture
            if piece in 'Pp':
                if pl_move == self.en_passant:
                    if self.move == 0:
                        black_occupied_cp.remove(self.en_passant + 8)
                    else:
                        white_occupied_cp.remove(self.en_passant - 8)
            
            attacked_squares = get_attacked_squares(board_cp, black_occupied_cp if self.move == 0 else white_occupied_cp)
            if piece in 'Kk':
                king_pos = pl_move
            else:
                king_pos = self.king_positions[self.move]
            if king_pos in attacked_squares:
                illegal_moves.add(pl_move)
        
        legal_moves = pseudo_legal_moves.difference(illegal_moves)
        return legal_moves

    def queue_move(self, move: tuple[int, int]):
        self.queued_move = move

class HandState:
    def __init__(self, field_effects: FieldEffectsState):
        # each hand is represented by a list of
        # strings, each of which is a card_id (name)
        self.white_hand = ['cruciatus', 'confringo', 'impedimenta', 'imperius']
        self.black_hand = ['locomotor', 'legilimens', 'reparo', 'prior_incantato']

        self.w_queue = []
        self.b_queue = []

        self.field_effects = field_effects

    def queue_cards(self, p_side: str, cards: list[str]):
        if p_side == 'w':
            self.white_hand = list(set(self.white_hand).union(set(self.w_queue)))
            self.w_queue = cards
            self.white_hand = list(set(self.white_hand).difference(set(self.w_queue)))
        else:
            self.black_hand = list(set(self.black_hand).union(set(self.b_queue)))
            self.b_queue = cards
            self.black_hand = list(set(self.black_hand).difference(set(self.b_queue)))

    def make_card_plays(self):
        self.w_queue = []
        self.b_queue = []

    def get_hands_data(self, p_side: str) -> dict:
        if p_side == 'w':
            return {
                'p_hand': self.white_hand,
                'o_hand': len(self.black_hand),
                'queued': self.w_queue
            }
        else:
            return {
                'p_hand': self.black_hand,
                'o_hand': len(self.white_hand),
                'queued': self.b_queue
            }
