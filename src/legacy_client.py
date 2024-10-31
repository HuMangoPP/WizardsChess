import pygame as pg
import numpy as np
import pandas as pd
from .pyfont.font import Font


class _Settings:
    TILESIZE = 64

    COLOURS = {

    }


class Client:
    def __init__(self):
        pg.init()

        self.window = pg.display.set_mode((1920, 1080))
        self.clock = pg.time.Clock()
        pg.display.set_caption('Wizard Chess')

        self.font = Font(pg.image.load('./src/pyfont/font.png').convert())

        self._prerender_board()
        self._load_pieces()

        self._load_cards()
        self.card_rects = {1: [], -1: []}
    
    def _prerender_board(self):
        self.board = pg.Surface((8 * _Settings.TILESIZE, 8 * _Settings.TILESIZE))
        center = np.array(self.board.get_size()) / 2
        for i in np.arange(64):
            xy = np.array([i % 8, i // 8])
            colour = (181, 136, 99) if np.sum(xy) % 2 == 0 else (240, 217, 181)
            xy = xy - 3.5
            xy[1] *= -1
            xy = xy * _Settings.TILESIZE
            xy = center + xy
            topleft = xy - _Settings.TILESIZE / 2
            pg.draw.rect(self.board, colour, pg.Rect(
                *topleft.astype(float),
                _Settings.TILESIZE, _Settings.TILESIZE
            ))
        self.board_rect = self.board.get_rect()
        self.board_rect.center = (np.array(self.window.get_size()) / 2).astype(float)

    def _load_pieces(self):
        pieces = pg.image.load('./assets/chess/pieces.png').convert()
        piece_width = pieces.get_width() / 6
        piece_height = pieces.get_height()
        piece_names = ['king', 'queen', 'bishop', 'knight', 'rook', 'pawn']
        scale = _Settings.TILESIZE / 16 * 3 / 4
        self.pieces = {
            piece_name: pg.transform.scale_by(pieces.subsurface(pg.Rect(i * piece_width, 0, piece_width, piece_height)), scale)
            for i, piece_name in enumerate(piece_names)
        }
        [piece.set_colorkey((0, 0, 0)) for piece in self.pieces.values()]

    def _load_cards(self):
        card_data = pd.read_csv('./assets/cards/card_data.csv', index_col=0)
        self.cards = {}
        card_size = (200, 100)
        for row in card_data.itertuples():
            card = pg.Surface(card_size)
            card.fill((100, 100, 100))
            self.font.render(
                card,
                row[1],
                (card_size[0] / 2, card_size[1] / 2),
                (255, 255, 255),
                10, 
                style='center'
            )
            self.cards[row[0]] = card

    def _render_piece_move_indices(self, piece_move_indices: np.ndarray):
        center = np.array(self.window.get_size()) / 2
        for piece_move_index in piece_move_indices:
            xy = np.array([piece_move_index % 8, piece_move_index // 8])
            xy = xy - 3.5
            xy = xy * _Settings.TILESIZE
            xy = center + xy

            pg.draw.circle(self.window, (255, 255, 255), xy.astype(float), _Settings.TILESIZE // 6)

    def _render_pieces(self, piece_keys: np.ndarray, piece_colours: np.ndarray):
        center = np.array(self.window.get_size()) / 2

        for i, (piece_key, piece_colour) in enumerate(zip(piece_keys, piece_colours)):
            if piece_key == 'none':
                continue

            piece = self.pieces[piece_key].copy()
            piece.set_colorkey((0, 255, 0))
            coloured_piece = pg.Surface(piece.get_size())
            coloured_piece.fill((100, 0, 0)) if piece_colour else coloured_piece.fill((0, 0, 100))
            coloured_piece.blit(piece, (0, 0))
            coloured_piece.set_colorkey((0, 0, 0))

            xy = np.array([i % 8, i // 8])
            xy = xy - 3.5
            xy = xy * _Settings.TILESIZE
            xy = center + xy
            topleft = xy - np.array(coloured_piece.get_size()) * np.array([1/2, 4/5])
            self.window.blit(coloured_piece, topleft.astype(float))

    def _render_hands(
        self, 
        my_hand: np.ndarray, 
        opponent_hand: np.ndarray, 
        my_hand_played_indices: list, 
        opponent_hand_played_indices: list
    ):
        render_offset = (1 - my_hand.size) / 2
        self.card_rects = {1: [], -1: []}
        for i, card_id in enumerate(my_hand):
            card = self.cards[card_id]
            card_rect = card.get_rect()
            card_rect.centerx = self.window.get_width() / 2 + (render_offset + i) * (card_rect.width + 10)
            card_rect.centery = self.window.get_height() - card_rect.height * (1 + (i in my_hand_played_indices))
            self.card_rects[1].append(card_rect)

            self.window.blit(card, card_rect)
        
        render_offset = (1 - opponent_hand.size) / 2
        for i, card_id in enumerate(opponent_hand):
            card = self.cards[card_id]
            card_rect = card.get_rect()
            card_rect.centerx = self.window.get_width() / 2 + (render_offset + i) * (card_rect.width + 10)
            card_rect.centery = card_rect.height * (1 + (i in opponent_hand_played_indices))
            self.card_rects[-1].append(card_rect)

            self.window.blit(card, card_rect)

    def update(self, server):
        dt = self.clock.tick(60) / 1000

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return False
            
                if event.key == pg.K_RETURN:
                    server.end_turn()
            
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.board_rect.collidepoint(event.pos):
                    xy = (np.array(event.pos) - np.array(self.board_rect.topleft)) // _Settings.TILESIZE
                    board_index = xy[0] + xy[1] * 8
                    server.board_event(board_index)
                    server.hand_event({
                        'side': 0,
                        'board_index': board_index
                    })
                
                for i, card_rect in enumerate(self.card_rects[1]):
                    if card_rect.collidepoint(event.pos):
                        server.hand_event({
                            'side': 1,
                            'card_index': i
                        })
                
                for i, card_rect in enumerate(self.card_rects[-1]):
                    if card_rect.collidepoint(event.pos):
                        server.hand_event({
                            'side': -1,
                            'card_index': i
                        })

        return True
    
    def render(self, server):
        self.window.fill((0, 0, 0))

        # render the board
        self.window.blit(self.board, self.board_rect)

        # render pieces
        piece_keys, piece_colours, piece_move_indices = server.board_manager.get_render_data()
        self._render_pieces(piece_keys, piece_colours)
        self._render_piece_move_indices(piece_move_indices)

        # render hand
        hands, played_indices = server.hand_manager.get_render_data()
        self._render_hands(hands[1], hands[-1], played_indices[1], played_indices[-1])

        pg.display.flip()