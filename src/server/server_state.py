
WHITE_PIECES = 'PNBRQK'
BLACK_PIECES = 'pnbrqk'
STARTING_FEN_STR = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -1 0 1'
SIDE_MAP = {'w': 1, 'b': -1}

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
    def __init__(self, fen_str: str=STARTING_FEN_STR):
        self.board : list[str] = []
        self.white_occupied = set()
        self.black_occupied = set()
        self.on_start(fen_str)

        # these might not be need to be stored permanently
        # can be calculated and returned when the player requests
        self.valid_moves = set()
        self.checked_squares = set()
    
    def on_start(self, fen_str):
        # read the fen_str
        data = fen_str.split(' ')
        position = data[0]
        self.move = SIDE_MAP[data[1]]
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
        fen_str += 'w ' if self.move == 1 else 'b '

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

    def make_board_move(self, move: list[int, int]):
        old_square = move[0]
        new_square = move[1]
        moved_piece = self.board[old_square]

        # update occupations
        if self.move == 1:
            self.white_occupied.remove(old_square)
            self.white_occupied.add(new_square)
            if new_square in self.black_occupied:
                self.black_occupied.remove(new_square)
        else:
            self.black_occupied.remove(old_square)
            self.black_occupied.add(new_square)
            if new_square in self.white_occupied:
                self.white_occupied.remove(new_square)
        
        # pawn move
        en_passant = self.en_passant
        self.en_passant = -1
        if moved_piece in 'Pp':
            if new_square == en_passant: # en passant capture
                if self.move == 1:
                    self.black_occupied.remove(en_passant + 8)
                else:
                    self.white_occupied.remove(en_passant - 8)
                self.board[en_passant] = 0
            elif new_square - old_square == 16:
                self.en_passant = old_square + 8
            elif old_square - new_square == 16:
                self.en_passant = old_square - 8
        
        # castling
        if moved_piece in 'Kk':
            self.king_positions[int((1 - self.move) / 2)] = new_square
            if new_square - old_square == 2: # kingside castle
                self.board[new_square - 1] = self.board[new_square + 1]
                self.board[new_square + 1] = 0
                if self.move == 1:
                    self.white_occupied.add(new_square - 1)
                    self.white_occupied.remove(new_square + 1)
                else:
                    self.black_occupied.add(new_square - 1)
                    self.black_occupied.remove(new_square + 1)
            elif old_square - new_square == 2: # queenside castle
                self.board[new_square + 1] = self.board[new_square - 2]
                self.board[new_square - 2] = 0 
                if self.move == 1:
                    self.white_occupied.add(new_square + 1)
                    self.white_occupied.remove(new_square - 2)
                else:
                    self.black_occupied.add(new_square + 1)
                    self.black_occupied.remove(new_square - 1)
            # remove castling privileges
            if self.move == 1:
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
        self.move *= -1

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
                if self.move == 1:
                    black_occupied_cp.remove(pl_move)
                else:
                    white_occupied_cp.remove(pl_move)
            # update the board state
            board_cp[pl_move] = piece
            board_cp[square] = 0

            # en passant capture
            if piece in 'Pp':
                if pl_move == self.en_passant:
                    if self.move == 1:
                        black_occupied_cp.remove(self.en_passant + 8)
                    else:
                        white_occupied_cp.remove(self.en_passant - 8)
            
            attacked_squares = get_attacked_squares(board_cp, black_occupied_cp if self.move == 1 else white_occupied_cp)
            if piece in 'Kk':
                king_pos = pl_move
            else:
                king_pos = self.king_positions[int((1 - self.move) / 2)]
            if king_pos in attacked_squares:
                illegal_moves.add(pl_move)
        
        legal_moves = pseudo_legal_moves.difference(illegal_moves)
        return legal_moves
                
    
