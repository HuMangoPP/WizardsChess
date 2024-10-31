import numpy as np
import pygame as pg


class _Settings:
    TRANSITION_TIME = 0.5

    def transition_out(overlay: pg.Surface, transition_time: float):
        width, height = overlay.get_size()
        transition_progress = 1.25 * transition_time / _Settings.TRANSITION_TIME
        topleft = [0, 0]
        bottomleft = [0, height]
        topright = [transition_progress * width , 0]
        bottomright = [transition_progress * width - 200, height]
        points = [
            topleft, bottomleft, bottomright, topright
        ]
        overlay.fill((0, 0, 0))
        pg.draw.polygon(overlay, (10, 10, 10), points)

    def transition_in(overlay: pg.Surface, transition_time: float):
        width, height = overlay.get_size()
        transition_progress = 1.25 * transition_time / _Settings.TRANSITION_TIME
        topleft = [transition_progress * width, 0]
        bottomleft = [transition_progress * width - 200, height]
        topright = [width, 0]
        bottomright = [width, height]
        points = [
            topleft, bottomleft, bottomright, topright
        ]
        overlay.fill((0, 0, 0))
        pg.draw.polygon(overlay, (10, 10, 10), points)

    GREY = (100, 100, 100)
    WHITE = (255, 255, 255)
    BLACK = (10, 10, 10)

    TILESIZE = 64
    COLOURS = dict()

class Menu:
    def __init__(self, client):
        self.resolution = client.resolution
        self.goto : str = None
    
    def _on_transition(self):
        # 0 = none
        # 1 = fade out
        # 2 = black screen
        # 3 = fade in
        self.transition_phase = 2
        self.transition_time = 0

    def on_load(self, client):
        self._on_transition()
    
    def update(self, client):
        # transition logic
        if self.transition_phase > 0:
            self.transition_time += client.dt
            if self.transition_phase == 1 and self.transition_time > _Settings.TRANSITION_TIME:
                return dict(exit=False, goto=self.goto)
            if self.transition_time > _Settings.TRANSITION_TIME:
                self.transition_time = 0
                self.transition_phase = (self.transition_phase + 1) % 4
        
        return dict()
    
    def _render_overlay(self, display: pg.Surface):
        if self.transition_phase == 1: # fade out
            _Settings.transition_out(display, self.transition_time)
        elif self.transition_phase == 2: # "black" screen
            display.fill(_Settings.BLACK)
        elif self.transition_phase == 3: # fade in
            _Settings.transition_in(display, self.transition_time)

    def render(self, client):
        # render overlay
        self._render_overlay(client.displays['overlay'])
        
        # fps
        client.font.render(
            client.displays['overlay'],
            f'{int(client.clock.get_fps())}',
            (10, 10),
            _Settings.WHITE,
            20,
            style='topleft'
        )


class MainMenu(Menu):
    def __init__(self, client):
        super().__init__(client)

        # menu setup
        self._setup_buttons()

        # override
        self.goto = 'game'
    
    def _setup_buttons(self):
        self.start_button = pg.Rect(0, 0, 200, 50)
        self.start_button.center = np.array(self.resolution) / 2
    
    def on_load(self, client):
        super().on_load(client)
    
    def update(self, client):
        # menu update
        for event in client.events:
            if event.type == pg.MOUSEBUTTONDOWN and self.start_button.collidepoint(event.pos):
                self.transition_phase = 1
                self.transition_time = 0

        return super().update(client)

    def render(self, client):
        # menu render
        default = client.displays['default']
        pg.draw.rect(default, _Settings.GREY, self.start_button)
        client.font.render(
            default, 
            'start', 
            self.start_button.center,
            _Settings.WHITE,
            20,
            style='center'
        )
        
        super().render(client)


class GameMenu(Menu):
    def __init__(self, client):
        super().__init__(client)

        # menu setup
        self.card_rects = {1: [], -1: []}

        # override
        self.goto = 'main'
    
    def _render_piece_move_indices(self, display, piece_move_indices: np.ndarray):
        center = np.array(self.resolution) / 2
        for piece_move_index in piece_move_indices:
            xy = np.array([piece_move_index % 8, piece_move_index // 8])
            xy = xy - 3.5
            xy = xy * _Settings.TILESIZE
            xy = center + xy

            pg.draw.circle(display, (255, 255, 255), xy.astype(float), _Settings.TILESIZE // 6)

    def _render_pieces(self, display, piece_assets: dict[str, pg.Surface], piece_keys: np.ndarray, piece_colours: np.ndarray):
        center = np.array(self.resolution) / 2

        for i, (piece_key, piece_colour) in enumerate(zip(piece_keys, piece_colours)):
            if piece_key == 'none':
                continue

            piece = piece_assets[piece_key].copy()
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
            display.blit(coloured_piece, topleft.astype(float))

    def _render_hands(
        self, 
        display,
        card_assets: dict[str, pg.Surface],
        my_hand: np.ndarray, 
        opponent_hand: np.ndarray, 
        my_hand_played_indices: list, 
        opponent_hand_played_indices: list
    ):
        render_offset = (1 - my_hand.size) / 2
        self.card_rects = {1: [], -1: []}
        for i, card_id in enumerate(my_hand):
            card = card_assets[card_id]
            card_rect = card.get_rect()
            card_rect.centerx = self.resolution[0] / 2 + (render_offset + i) * (card_rect.width + 10)
            card_rect.centery = self.resolution[1] - card_rect.height * (1 + (i in my_hand_played_indices))
            self.card_rects[1].append(card_rect)

            display.blit(card, card_rect)
        
        render_offset = (1 - opponent_hand.size) / 2
        for i, card_id in enumerate(opponent_hand):
            card = card_assets[card_id]
            card_rect = card.get_rect()
            card_rect.centerx = self.resolution[0] / 2 + (render_offset + i) * (card_rect.width + 10)
            card_rect.centery = card_rect.height * (1 + (i in opponent_hand_played_indices))
            self.card_rects[-1].append(card_rect)

            display.blit(card, card_rect)
    
    def on_load(self, client):
        super().on_load(client)
        client.server.reset()
    
    def update(self, client):
        # menu update
        # TODO client should not have server
        for event in client.events:
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                client.server.end_turn()
            if event.type == pg.MOUSEBUTTONDOWN:
                if client.assets.board_rect.collidepoint(event.pos):
                    xy = (np.array(event.pos) - np.array(client.assets.board_rect.topleft)) // _Settings.TILESIZE
                    board_index = xy[0] + xy[1] * 8
                    client.server.board_event(board_index)
                    client.server.hand_event({
                        'side': 0,
                        'board_index': board_index
                    })
                
                for i, card_rect in enumerate(self.card_rects[1]):
                    if card_rect.collidepoint(event.pos):
                        client.server.hand_event({
                            'side': 1,
                            'card_index': i
                        })
                
                for i, card_rect in enumerate(self.card_rects[-1]):
                    if card_rect.collidepoint(event.pos):
                        client.server.hand_event({
                            'side': -1,
                            'card_index': i
                        })

        return super().update(client)

    def render(self, client):
        # menu render
        default = client.displays['default']

        # render the board
        default.blit(client.assets.board, client.assets.board_rect)

        # TODO client should not have server

        # render pieces
        piece_keys, piece_colours, piece_move_indices = client.server.board_manager.get_render_data()
        self._render_pieces(default, client.assets.pieces, piece_keys, piece_colours)
        self._render_piece_move_indices(default, piece_move_indices)

        # render hand
        hands, played_indices = client.server.hand_manager.get_render_data()
        self._render_hands(
            default, 
            client.assets.cards, 
            hands[1], hands[-1], 
            played_indices[1], played_indices[-1]
        )
        
        super().render(client)
