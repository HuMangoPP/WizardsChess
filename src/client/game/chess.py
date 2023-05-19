import pygame as pg

WHITE_PIECES = 'PNBRQK'
BLACK_PIECES = 'pnbrqk'
TILESIZE = 48

class Board:
    def __init__(self, menu, fen_str: str, occupy: list[int]):
        self.width, self.height = menu.width, menu.height
        self.display : pg.Surface = menu.displays['default']
        self.piece_collection : dict[str, dict[str, pg.Surface]] = menu.piece_collection
        self.white_palette = menu.white_theme
        self.black_palette = menu.black_theme
        self.menu = menu

        self.update_board_state(fen_str, occupy, (-1, -1))

        # board display
        self.board_surf = pg.Surface((TILESIZE * 8, TILESIZE * 8))
        self.flip = self.menu.p_side == 'b'
        self.draw_board_surf(flip=self.flip)
        self.board_rect = self.board_surf.get_rect()
        self.board_rect.centerx = self.width/2
        self.board_rect.centery = self.height/2
        
        self.hovered_square = -1
        self.prev_square = -1
        self.held_piece = ''
        self.legal_moves = set()
        self.spell_targets = set()
        self.displacements = set()

    def update_board_state(self, fen_str: str, occupy: list[int], queued_move: tuple[int, int]):
        self.board : list[str] = []
        self.read_fen_str(fen_str)
        self.occupied = set(occupy) # dont even know if i'll need

        self.queued_move = queued_move

    def update_legal_moves(self, legal_moves: list[int]):
        self.legal_moves = set(legal_moves)

    def draw_board_surf(self, flip: bool=False):
        for i, _ in enumerate(self.board):
            x = i % 8
            y = i // 8
            if flip:
                if (x + y) % 2 == 1:
                    pg.draw.rect(self.board_surf, (214, 153, 255), 
                                pg.Rect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE))
                else:
                    pg.draw.rect(self.board_surf, (52, 18, 74), 
                                pg.Rect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE))
            else:
                if (x + y) % 2 == 0:
                    pg.draw.rect(self.board_surf, (214, 153, 255), 
                                pg.Rect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE))
                else:
                    pg.draw.rect(self.board_surf, (52, 18, 74), 
                                pg.Rect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE))

    def read_fen_str(self, fen_str: str):
        # read the fen_str
        data = fen_str.split(' ')
        position = data[0]
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
                if char == 'K':
                    self.king_positions[0] = square_index
                square_index += 1
            elif char in BLACK_PIECES:
                self.board.append(char)
                if char == 'k':
                    self.king_positions[1] = square_index
                square_index += 1
            elif char == '/':
                continue
            else:
                num_empty = int(char)
                for i in range(num_empty):
                    self.board.append('')
                square_index += num_empty

    def input(self, events: list[pg.Event]) -> dict:
        req = {}
        for event in events:
            if event.type == pg.MOUSEMOTION:
                zeroed_x = event.pos[0] - self.board_rect.left
                zeroed_y = event.pos[1] - self.board_rect.top
                chunked_x = zeroed_x // TILESIZE
                if self.flip:
                    chunked_y = 7 - zeroed_y // TILESIZE
                else:
                    chunked_y = zeroed_y // TILESIZE
                if (chunked_x < 0 or chunked_x >= 8) or (chunked_y < 0 or chunked_y >= 8):
                    self.hovered_square = -1
                else:
                    self.hovered_square = chunked_x + chunked_y * 8
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.menu.p_hand.new_card_in_queue is None:
                    if self.held_piece:
                        if self.hovered_square in self.legal_moves:
                            # send data to server to make a move
                            req = {
                                'req_type': 'move_piece',
                                'p_side': self.menu.p_side,
                                'move': [self.prev_square, self.hovered_square]
                            }
                            self.prev_square = -1
                            self.held_piece = ''
                            self.legal_moves = set()
                        else:
                            self.prev_square = -1
                            self.held_piece = ''
                            self.legal_moves = set()
                    elif self.hovered_square in self.occupied:
                        # send data to server to retrieve info about legal moves
                        req = {
                            'req_type': 'pickup',
                            'square': self.hovered_square
                        }
                        self.prev_square = self.hovered_square
                        self.held_piece = self.board[self.hovered_square]
        return req

    def render_pieces(self):
        displace_from = [displacement[0] for displacement in self.displacements]
        displace_to = [displacement[1] for displacement in self.displacements]

        if self.flip:
            for square_index in range(len(self.board)-1, -1, -1):
                square = self.board[square_index]
                if square and square_index != self.queued_move[0] and square_index not in displace_from:
                    # square != 0
                    # square_index is not the queued move
                    # square index is not a displaced piece
                    piece = square.lower()
                    x = (square_index % 8 + 0.5) * TILESIZE + self.board_rect.left
                    y = (7 - square_index // 8 + 0.85) * TILESIZE + self.board_rect.top
                    if square_index == self.hovered_square:
                        y -= TILESIZE / 2
                    if 'a' <= square and square <= 'z':
                        piece_surf = self.piece_collection[self.black_palette][piece]
                    else:
                        piece_surf = self.piece_collection[self.white_palette][piece]
                    piece_rect = piece_surf.get_rect()
                    piece_rect.centerx = x
                    piece_rect.bottom = y
                    if square_index == self.hovered_square:
                        shadow = pg.Surface((TILESIZE, TILESIZE))
                        pg.draw.circle(shadow, (50, 50, 50), (TILESIZE/2, TILESIZE/2), 0.35 * TILESIZE)
                        shadow.set_colorkey((0, 0, 0))
                        shadow_rect = shadow.get_rect()
                        shadow_rect.centerx = x
                        shadow_rect.centery = y + 0.15 * TILESIZE
                        self.display.blit(shadow, shadow_rect, special_flags=pg.BLEND_RGB_SUB)
                    self.display.blit(piece_surf, piece_rect)

            for index in range(len(displace_to)-1, -1, -1):
                square_index = displace_to[index]
                square = self.board[displace_from[index]]
                piece = square.lower()
                x = (square_index % 8 + 0.5) * TILESIZE + self.board_rect.left
                y = (7 - square_index // 8 + 0.35) * TILESIZE + self.board_rect.top
                if 'a' <= square and square <= 'z':
                    piece_surf = self.piece_collection[self.black_palette][piece]
                else:
                    piece_surf = self.piece_collection[self.white_palette][piece]
                piece_rect = piece_surf.get_rect()
                piece_rect.centerx = x
                piece_rect.bottom = y
                shadow = pg.Surface((TILESIZE, TILESIZE))
                pg.draw.circle(shadow, (50, 50, 50), (TILESIZE/2, TILESIZE/2), 0.35 * TILESIZE)
                shadow.set_colorkey((0, 0, 0))
                shadow_rect = shadow.get_rect()
                shadow_rect.centerx = x
                shadow_rect.centery = y + 0.15 * TILESIZE
                self.display.blit(shadow, shadow_rect, special_flags=pg.BLEND_RGB_SUB)
                self.display.blit(piece_surf, piece_rect)

            # queued move
            if self.queued_move[1] != -1:
                x = (self.queued_move[1] % 8 + 0.5) * TILESIZE + self.board_rect.left
                y = (7 - self.queued_move[1] // 8 + 0.85) * TILESIZE + self.board_rect.top - TILESIZE / 2
                square = self.board[self.queued_move[0]]
                piece = square.lower()
                if 'a' <= square and square <= 'z':
                    piece_surf = self.piece_collection[self.black_palette][piece]
                else:
                    piece_surf = self.piece_collection[self.white_palette][piece]
                piece_rect = piece_surf.get_rect()
                piece_rect.centerx = x
                piece_rect.bottom = y
                shadow = pg.Surface((TILESIZE, TILESIZE))
                pg.draw.circle(shadow, (50, 50, 50), (TILESIZE/2, TILESIZE/2), 0.35 * TILESIZE)
                shadow.set_colorkey((0, 0, 0))
                shadow_rect = shadow.get_rect()
                shadow_rect.centerx = x
                shadow_rect.centery = y + 0.15 * TILESIZE
                self.display.blit(shadow, shadow_rect, special_flags=pg.BLEND_RGB_SUB)
                self.display.blit(piece_surf, piece_rect)
        else:
            for i, square in enumerate(self.board):
                if square and i != self.queued_move[0] and i not in displace_from:
                    piece = square.lower()
                    x = (i % 8 + 0.5) * TILESIZE + self.board_rect.left
                    y = (i // 8 + 0.85) * TILESIZE + self.board_rect.top
                    if i == self.hovered_square:
                        y -= TILESIZE / 2
                    if 'a' <= square and square <= 'z':
                        piece_surf = self.piece_collection[self.black_palette][piece]
                    else:
                        piece_surf = self.piece_collection[self.white_palette][piece]
                    piece_rect = piece_surf.get_rect()
                    piece_rect.centerx = x
                    piece_rect.bottom = y
                    if i == self.hovered_square:
                        shadow = pg.Surface((TILESIZE, TILESIZE))
                        pg.draw.circle(shadow, (50, 50, 50), (TILESIZE/2, TILESIZE/2), 0.35 * TILESIZE)
                        shadow.set_colorkey((0, 0, 0))
                        shadow_rect = shadow.get_rect()
                        shadow_rect.centerx = x
                        shadow_rect.centery = y + 0.15 * TILESIZE
                        self.display.blit(shadow, shadow_rect, special_flags=pg.BLEND_RGB_SUB)
                    self.display.blit(piece_surf, piece_rect)
            
            for index, square_index in enumerate(displace_to):
                square = self.board[displace_from[index]]
                piece = square.lower()
                x = (square_index % 8 + 0.5) * TILESIZE + self.board_rect.left
                y = (square_index // 8 + 0.35) * TILESIZE + self.board_rect.top
                if 'a' <= square and square <= 'z':
                    piece_surf = self.piece_collection[self.black_palette][piece]
                else:
                    piece_surf = self.piece_collection[self.white_palette][piece]
                piece_rect = piece_surf.get_rect()
                piece_rect.centerx = x
                piece_rect.bottom = y
                shadow = pg.Surface((TILESIZE, TILESIZE))
                pg.draw.circle(shadow, (50, 50, 50), (TILESIZE/2, TILESIZE/2), 0.35 * TILESIZE)
                shadow.set_colorkey((0, 0, 0))
                shadow_rect = shadow.get_rect()
                shadow_rect.centerx = x
                shadow_rect.centery = y + 0.15 * TILESIZE
                self.display.blit(shadow, shadow_rect, special_flags=pg.BLEND_RGB_SUB)
                self.display.blit(piece_surf, piece_rect)

            # queued move
            if self.queued_move[1] != -1:
                x = (self.queued_move[1] % 8 + 0.5) * TILESIZE + self.board_rect.left
                y = (self.queued_move[1] // 8 + 0.85) * TILESIZE + self.board_rect.top - TILESIZE / 2
                square = self.board[self.queued_move[0]]
                piece = square.lower()
                if 'a' <= square and square <= 'z':
                    piece_surf = self.piece_collection[self.black_palette][piece]
                else:
                    piece_surf = self.piece_collection[self.white_palette][piece]
                piece_rect = piece_surf.get_rect()
                piece_rect.centerx = x
                piece_rect.bottom = y
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
                
    def render_legal_moves(self):
        if self.legal_moves:
            if self.flip:
                for legal_move in self.legal_moves:
                    x = legal_move % 8 * TILESIZE + self.board_rect.left
                    y = (7 - legal_move // 8) * TILESIZE + self.board_rect.top
                    pg.draw.rect(self.display, (255, 255, 255),
                                pg.Rect(x, y, TILESIZE, TILESIZE))
            else:
                for legal_move in self.legal_moves:
                    x = legal_move % 8 * TILESIZE + self.board_rect.left
                    y = legal_move // 8 * TILESIZE + self.board_rect.top
                    pg.draw.rect(self.display, (255, 255, 255),
                                pg.Rect(x, y, TILESIZE, TILESIZE))

    def render_spell_targets(self):
        if self.spell_targets:
            if self.flip:
                for spell_target in self.spell_targets:
                    x = spell_target % 8 * TILESIZE + self.board_rect.left
                    y = (7 - spell_target // 8) * TILESIZE + self.board_rect.top
                    pg.draw.rect(self.display, (255, 255, 255),
                                pg.Rect(x, y, TILESIZE, TILESIZE))
            else:
                for spell_target in self.spell_targets:
                    x = spell_target % 8 * TILESIZE + self.board_rect.left
                    y = spell_target // 8 * TILESIZE + self.board_rect.top
                    pg.draw.rect(self.display, (255, 255, 255),
                                pg.Rect(x, y, TILESIZE, TILESIZE))

    def render(self):
        self.display.blit(self.board_surf, self.board_rect)
        self.render_legal_moves()
        self.render_spell_targets()
        # self.render_checked_squares()
        self.render_pieces()
        self.render_held_piece()

