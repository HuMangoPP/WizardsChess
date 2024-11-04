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

    def get_xy(index: int):
        xy = np.array([index % 8, index // 8]) # get xy
        xy = xy - 8 / 2 + 1 / 2 # align pieces
        xy = xy * _Settings.TILESIZE # scale
        return xy

    def lerp(u: np.ndarray, v: np.ndarray, t: float):
        return u + (v - u) * t

    GREY = (100, 100, 100)
    WHITE = (255, 255, 255)
    BLACK = (10, 10, 10)

    TILESIZE = 48
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

        self._setup_animations()

        # override
        self.goto = 'main'
    
    def _setup_animations(self):
        self.animations = []
        self.animation_time = 1

        from .vfx import Sparks
        self.sparks = Sparks()

    def on_load(self, client):
        super().on_load(client)
        client.server.reset()
    
    def _animate(self, client):
        if self.animation_time <= 0:
            self.animation_time = 1
            self.animations = self.animations[1:]
        else:
            self.animation_time -= client.dt

    def _input(self, client):
        # TODO client should not have server
        for event in client.events:
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                self.animations = client.server.end_turn()
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

    def update(self, client):
        # menu update
        if self.animations:
            self._animate(client)
        else:
            self._input(client)
        self.sparks.update(client.dt)

        return super().update(client)

    def _render_piece_move_indices(self, display: pg.Surface, piece_move_indices: np.ndarray):
        center = np.array(self.resolution) / 2
        for piece_move_index in piece_move_indices:
            xy = center + _Settings.get_xy(piece_move_index)

            pg.draw.circle(display, (255, 255, 255), xy.astype(float), _Settings.TILESIZE // 6)

    def _render_pieces(self, display: pg.Surface, piece_assets: dict[str, pg.Surface], piece_keys: np.ndarray, piece_colours: np.ndarray):
        center = np.array(self.resolution) / 2

        for i, (piece_key, piece_colour) in enumerate(zip(piece_keys, piece_colours)):
            xy = center + _Settings.get_xy(i)
            if self.animations:
                animation = self.animations[0]
                animation_type = animation[0]
                if animation_type == 'move_piece':
                    old_index, new_index = animation[1:]
                    if i == new_index:
                        old_xy = center + _Settings.get_xy(old_index)
                        new_xy = center + _Settings.get_xy(new_index)
                        xy = _Settings.lerp(old_xy, new_xy, 1 - self.animation_time)
                if animation_type == 'tile_effects':
                    board_indices = animation[1]
                    index = np.where(i == board_indices)[0]
                    if index.size > 0:
                        piece_key = animation[2][index[0]]
                        piece_colour = animation[3][index[0]]
                for animation in self.animations[1:]:
                    animation_type = animation[0]
                    if animation_type == 'move_piece':
                        old_index, new_index = animation[1:]
                        if i == new_index:
                            xy = center + _Settings.get_xy(old_index)
                    if animation_type == 'tile_effects':
                        board_indices = animation[1]
                        index = np.where(i == board_indices)[0]
                        if index.size > 0:
                            piece_key = animation[2][index[0]]
                            piece_colour = animation[3][index[0]]
            
            if piece_key == 'none':
                continue

            piece = piece_assets[piece_key].copy()
            piece.set_colorkey((0, 255, 0))
            coloured_piece = pg.Surface(piece.get_size())
            coloured_piece.fill((100, 0, 0)) if piece_colour else coloured_piece.fill((0, 0, 100))
            coloured_piece.blit(piece, (0, 0))
            coloured_piece.set_colorkey((0, 0, 0))

            topleft = xy - np.array(coloured_piece.get_size()) * np.array([1/2, 4/5])
            display.blit(coloured_piece, topleft.astype(float))

    def _render_hands(
        self, 
        display: pg.Surface,
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
    
    def _render_vfx(self, display: pg.Surface):
        if self.animations:
            center = np.array(self.resolution) / 2
            animation = self.animations[0]
            animation_type = animation[0]
            if animation_type == 'cast_spell':
                board_index, from_side = animation[1:]
                destination = center + _Settings.get_xy(board_index)
                anchor = center * np.array([1, from_side + 1])
                xy = _Settings.lerp(anchor, destination, 1 - self.animation_time)
                self.sparks.add_new_particles(
                    np.array([xy]),
                    2 * np.pi * np.random.rand(1)
                )
            elif animation_type == 'tile_effects':
                board_indices = animation[1]
                xys = center + np.array([
                    _Settings.get_xy(board_index)
                    for board_index in board_indices
                ])
                self.sparks.add_new_particles(
                    xys,
                    2 * np.pi * np.random.rand(xys.shape[0])
                )
        self.sparks.render(display)

    def render(self, client):
        # menu render
        default = client.displays['default']
        effects = client.displays['gaussian_blur']

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

        # vfx
        self._render_vfx(effects)
        
        super().render(client)
