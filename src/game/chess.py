import pygame as pg

WHITE_PIECES = 'PNBRQK'
BLACK_PIECES = 'pnbrqk'
STARTING_FEN_STR = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -1 0 1'
SIDE_MAP = {'w': 1, 'b': -1}
TILESIZE = 64

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

def get_piece_moves(board: list[str | int], piece: str, square: int, en_passant: int, 
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

def get_piece_attacks(board: list[str | int], piece: str, square: int) -> set[int]:
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

PIECE_OFFSETS = {
    'p': [[-1, -1], [0, -1], [1, -1]],
    'n': [[-1, -2], [1, -2], [2, -1], [2, 1], [1, 2], [-1, 2], [-2, 1], [-2, -1]],
    'b': [[-1, -1], [1, -1], [1, 1], [-1, 1]],
    'r': [[0, -1], [1, 0], [0, 1], [-1, 0]],
    'q': [[-1, -1], [1, -1], [1, 1], [-1, 1], [0, -1], [1, 0], [0, 1], [-1, 0]],
    'k': [[-1, -1], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0]]
}

class Board:
    def __init__(self, menu, fen_str: str=STARTING_FEN_STR):
        self.width, self.height = menu.width, menu.height
        self.display : pg.Surface = menu.displays['default']
        self.piece_collection : dict[str, dict[str, pg.Surface]] = menu.piece_collection
        self.white_palette = menu.white
        self.black_palette = menu.black

        self.board : list[str] = []
        self.white_occupied = set()
        self.black_occupied = set()
        # a piece will be designated as a character following pnbrqk 
        # with lower case denoting black and upper case denoting white
        # empty squares will be a space
        self.on_start(fen_str)

        # board display
        self.board_surf = pg.Surface((TILESIZE * 8, TILESIZE * 8))
        self.draw_board_surf()
        self.board_rect = self.board_surf.get_rect()
        self.board_rect.centerx = self.width/2
        self.board_rect.centery = self.height/2
        
        self.hovered_square = -1
        self.prev_square = -1
        self.held_piece = 0
        self.valid_moves = set()

        self.checked_squares = set()
    
    def on_start(self, fen_str: str):
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
                    self.king_positions[0] = square_index
                square_index += 1
            elif char == '/':
                continue
            else:
                num_empty = int(char)
                for i in range(num_empty):
                    self.board.append(0)
                square_index += num_empty

    def draw_board_surf(self):
        for i in range(len(self.board)):
            x = i % 8
            y = i // 8
            if (x + y) % 2 == 0:
                pg.draw.rect(self.board_surf, (214, 153, 255), 
                             pg.Rect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE))
            else:
                pg.draw.rect(self.board_surf, (52, 18, 74), 
                             pg.Rect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE))

    def update(self, events: list[pg.Event]):
        for event in events:
            if event.type == pg.MOUSEMOTION:
                zeroed_x = event.pos[0] - self.board_rect.left
                zeroed_y = event.pos[1] - self.board_rect.top
                chunked_x = zeroed_x // TILESIZE
                chunked_y = zeroed_y // TILESIZE
                if (chunked_x < 0 or chunked_x >= 8) or (chunked_y < 0 or chunked_y >= 8):
                    self.hovered_square = -1
                else:
                    self.hovered_square = chunked_x + chunked_y * 8
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.held_piece:
                    if self.hovered_square in self.valid_moves:
                        # update the occupations
                        if self.move == 1:
                            self.white_occupied.remove(self.prev_square)
                            self.white_occupied.add(self.hovered_square)
                            if self.hovered_square in self.black_occupied:
                                self.black_occupied.remove(self.hovered_square)
                        else:
                            self.black_occupied.remove(self.prev_square)
                            self.black_occupied.add(self.hovered_square)
                            if self.hovered_square in self.white_occupied:
                                self.white_occupied.remove(self.hovered_square)

                        # check if en passant capture
                        # otherwise, check if move makes en passant possible
                        # reset en passant
                        self.en_passant = -1
                        if self.held_piece in 'Pp':
                            orig_x = self.prev_square % 8
                            orig_y = self.prev_square // 8
                            new_x = self.hovered_square % 8
                            if orig_x != new_x:
                                if self.board[self.hovered_square] == 0:
                                    self.board[new_x + orig_y * 8] = 0
                                    if self.move == 1:
                                        self.black_occupied.remove(new_x + orig_y * 8)
                                    else:
                                        self.white_occupied.remove(new_x + orig_y * 8)
                            
                            new_y = self.hovered_square // 8
                            if new_y - orig_y == 2:
                                self.en_passant = orig_x + (orig_y + 1) * 8
                            elif orig_y - new_y == 2:
                                self.en_passant = orig_x + (orig_y - 1) * 8

                        # check if castle
                        # otherwise, king movement will remove castling privileges
                        if self.held_piece in 'Kk':
                            self.king_positions[int((1 - self.move) / 2)] = self.hovered_square
                            orig_x = self.prev_square % 8
                            new_x = self.hovered_square % 8
                            if new_x - orig_x == 2:
                                # kingside castle
                                y = self.hovered_square // 8
                                self.board[orig_x + 1 + y * 8] = self.board[new_x + 1 + y * 8]
                                self.board[new_x + 1 + y * 8] = 0
                                if self.move == 1:
                                    self.white_occupied.add(orig_x + 1 + y * 8)
                                    self.white_occupied.remove(new_x + 1 + y * 8)
                                else:
                                    self.black_occupied.add(orig_x + 1 + y * 8)
                                    self.black_occupied.remove(new_x + 1 + y * 8)
                            elif orig_x - new_x == 2:
                                # queenside castle
                                y = self.hovered_square // 8
                                self.board[orig_x - 1 + y * 8] = self.board[new_x - 2 + y * 8]
                                self.board[new_x - 2 + y * 8] = 0
                                if self.move == 1:
                                    self.white_occupied.add(orig_x - 1 + y * 8)
                                    self.white_occupied.remove(new_x - 2 + y * 8)
                                else:
                                    self.black_occupied.add(orig_x - 1 + y * 8)
                                    self.black_occupied.remove(new_x - 2 + y * 8)
                            queenside = 'Q' if self.held_piece == 'K' else 'q'
                            self.castling_priv[queenside] = False
                            self.castling_priv[self.held_piece] = False

                        # rook movements should also remove castling privileges
                        if self.held_piece in 'Rr':
                            orig_y = self.prev_square // 8
                            if orig_y == 0:
                                # queenside castle
                                queenside = 'Q' if self.held_piece == 'R' else 'q'
                                self.castling_priv[queenside] = False
                            elif orig_y == 7:
                                # kingside castle
                                kingside = 'K' if self.held_piece == 'R' else 'k'
                                self.castling_priv[kingside] = False

                        # reset the hold state
                        self.board[self.hovered_square] = self.held_piece
                        self.held_piece = 0
                        self.prev_square = -1
                        self.valid_moves = set()
                        self.move *= -1

                    else:
                        # snap back
                        self.board[self.prev_square] = self.held_piece
                        self.held_piece = 0
                        self.prev_square = -1
                        self.valid_moves = set()
                elif self.hovered_square != -1:
                    if self.board[self.hovered_square] != 0:
                        if ((self.move == 1 and self.board[self.hovered_square] in 'PNBRQK') or 
                            (self.move == -1 and self.board[self.hovered_square] in 'pnbrqk')):

                            self.held_piece = self.board[self.hovered_square]
                            self.prev_square = self.hovered_square
                            self.board[self.prev_square] = 0
                            self.valid_moves = set()
                            self.get_valid_moves()
    
    def render_pieces(self):
        for i, square in enumerate(self.board):
            if square != 0 and square != '/':
                piece = square.lower()
                x = (i % 8 + 0.5) * TILESIZE + self.board_rect.left
                y = (i // 8 + 0.85) * TILESIZE + self.board_rect.top
                if i == self.hovered_square and self.held_piece == 0:
                    y -= TILESIZE / 2
                if 'a' <= square and square <= 'z':
                    piece_surf = self.piece_collection[self.black_palette][piece]
                else:
                    piece_surf = self.piece_collection[self.white_palette][piece]
                piece_rect = piece_surf.get_rect()
                piece_rect.centerx = x
                piece_rect.bottom = y
                if i == self.hovered_square and self.held_piece == 0:
                    shadow = pg.Surface((TILESIZE, TILESIZE))
                    pg.draw.circle(shadow, (50, 50, 50), (TILESIZE/2, TILESIZE/2), 0.35 * TILESIZE)
                    shadow.set_colorkey((0, 0, 0))
                    shadow_rect = shadow.get_rect()
                    shadow_rect.centerx = x
                    shadow_rect.centery = y + 0.15 * TILESIZE
                    self.display.blit(shadow, shadow_rect, special_flags=pg.BLEND_RGB_SUB)
                self.display.blit(piece_surf, piece_rect)

    def render_held_piece(self):
        if self.held_piece:
            piece = self.held_piece.lower()
            x = pg.mouse.get_pos()[0]
            y = pg.mouse.get_pos()[1] + 0.35 * TILESIZE
            if 'a' <= self.held_piece and self.held_piece <= 'z':
                piece_surf = self.piece_collection[self.black_palette][piece]
            else:
                piece_surf = self.piece_collection[self.white_palette][piece]
            piece_rect = piece_surf.get_rect()
            piece_rect.centerx = x
            piece_rect.bottom = y

            self.display.blit(piece_surf, piece_rect)

    def get_checked_squares(self, board: list[str | int], occupied: set[int]):
        self.checked_squares = set()
        for occupation in occupied:
            piece = board[occupation]
            self.checked_squares = self.checked_squares.union(get_piece_attacks(board, piece, occupation))

    def render_checked_squares(self):
        if self.checked_squares:
            for checked_square in self.checked_squares:
                x = checked_square % 8 * TILESIZE + self.board_rect.left
                y = checked_square // 8 * TILESIZE + self.board_rect.top
                pg.draw.rect(self.display, (0, 0, 0), 
                             pg.Rect(x, y, TILESIZE, TILESIZE))

    def get_valid_moves(self):
        if self.held_piece:
            self.valid_moves = get_piece_moves(self.board, self.held_piece, self.prev_square,
                                               self.en_passant, self.castling_priv)
            illegal_moves = set()
            for valid_move in self.valid_moves:
                # "make the move" to test check
                board_copy = self.board.copy()
                black_occupied_copy = self.black_occupied.copy()
                white_occupied_copy = self.white_occupied.copy()
                if board_copy[valid_move] != 0:
                    if self.move == 1:
                        black_occupied_copy.remove(valid_move)
                    else:
                        white_occupied_copy.remove(valid_move)
                board_copy[valid_move] = self.held_piece
                board_copy[self.prev_square] = 0
                # en passant capture
                if self.held_piece in 'Pp':
                    new_x = valid_move % 8
                    prev_x = self.prev_square % 8
                    if prev_x != new_x:
                        prev_y = self.prev_square // 8
                        board_copy[new_x + prev_y * 8] = 0
                        if self.en_passant != -1:
                            if self.move == 1:
                                black_occupied_copy.remove(new_x + prev_y * 8)
                            else:
                                white_occupied_copy.remove(new_x + prev_y * 8)
                self.get_checked_squares(board_copy, black_occupied_copy if self.move == 1 else white_occupied_copy)
                if self.held_piece in 'Kk':
                    king_pos = valid_move
                else:
                    king_pos = self.king_positions[int((1 - self.move) / 2)]
                if king_pos in self.checked_squares:
                    illegal_moves.add(valid_move)
                
            self.valid_moves.difference_update(illegal_moves)
                
    def render_valid_moves(self):
        if self.valid_moves:
            for valid_move in self.valid_moves:
                x = valid_move % 8 * TILESIZE + self.board_rect.left
                y = valid_move // 8 * TILESIZE + self.board_rect.top
                pg.draw.rect(self.display, (255, 255, 255),
                             pg.Rect(x, y, TILESIZE, TILESIZE))

    def render(self):
        self.display.blit(self.board_surf, self.board_rect)
        self.render_valid_moves()
        self.render_checked_squares()
        self.render_pieces()
        self.render_held_piece()

