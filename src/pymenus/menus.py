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
        self.goto = 'lobby'
    
    def _setup_buttons(self):
        # bottons
        self.create_lobby_button = pg.Rect(0, 0, 200, 50)
        self.join_lobby_button = pg.Rect(0, 0, 200, 50)
        self.create_lobby_button.center = np.array(self.resolution) * np.array([1/2,4/9])
        self.join_lobby_button.center = np.array(self.resolution) * np.array([1/2,5/9])
        
        # lobby
        self.lobby_type = 'create'
    
    def on_load(self, client):
        super().on_load(client)
    
    def update(self, client):
        # menu update
        for event in client.events:
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.create_lobby_button.collidepoint(event.pos):
                    self.lobby_type = 'create'
                    self.transition_phase = 1
                    self.transition_time = 0
                if self.join_lobby_button.collidepoint(event.pos):
                    self.lobby_type = 'join'
                    self.transition_phase = 1
                    self.transition_time = 0
            
        return super().update(client)

    def render(self, client):
        # menu render
        default = client.displays['default']
        pg.draw.rect(default, _Settings.GREY, self.create_lobby_button)
        client.font.render(
            default, 
            'create lobby', 
            self.create_lobby_button.center,
            _Settings.WHITE,
            12,
            style='center'
        )
        pg.draw.rect(default, _Settings.GREY, self.join_lobby_button)
        client.font.render(
            default, 
            'join lobby', 
            self.join_lobby_button.center,
            _Settings.WHITE,
            12,
            style='center'
        )
        
        super().render(client)


class LobbyMenu(Menu):
    def __init__(self, client):
        super().__init__(client)

        # menu setup
        self._setup_boxes()

        # override
        self.goto = 'game'
    
    def _setup_boxes(self):
        self.code_length = 6
        offset = self.code_length / 2 + 1 /2
        boxsize = 50
        margin = 10
        self.code = ''
        self.boxes = [
            pg.Rect(
                self.resolution[0] / 2 + (boxsize + margin) * (i - offset) - boxsize / 2,
                self.resolution[1] / 2 - boxsize / 2,
                boxsize, boxsize
            ) for i in np.arange(self.code_length)
        ]

    def on_load(self, client):
        super().on_load(client)

        self.lobby_type = client._get_lobby_type()
    
    def update(self, client):
        # menu update
        for event in client.events:
            if event.type == pg.TEXTINPUT:
                if len(self.code) < 6:
                    self.code = f'{self.code}{event.text.lower()}'
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_BACKSPACE:
                    self.code = self.code[:-1]
                if (
                    event.key == pg.K_RETURN and
                    len(self.code) == self.code_length and
                    client.server.validate_code(self.code, self.lobby_type)
                ):
                    self.transition_phase = 1
                    self.transition_time = 0

        return super().update(client)

    def render(self, client):
        # menu render
        default = client.displays['default']

        # top text
        client.font.render(
            default,
            f'{self.lobby_type} lobby',
            np.array(self.resolution) * np.array([1/2, 1/5]),
            _Settings.WHITE,
            50,
            style='center'
        )

        # boxes
        for i, box in enumerate(self.boxes):
            pg.draw.rect(default, _Settings.GREY, box)
            if len(self.code) > i:
                client.font.render(
                    default,
                    self.code[i],
                    box.center,
                    _Settings.WHITE,
                    40,
                    style='center'
                )
        
        super().render(client)


class GameMenu(Menu):
    def __init__(self, client):
        super().__init__(client)

        # menu setup
        self.card_rects = {1: [], -1: []}

        self._setup_animations()

        self.code = None

        # override
        self.goto = 'main'
    
    def _setup_animations(self):
        self.animations = []
        self.animation_time = 1

        from .vfx import Sparks
        self.sparks = Sparks()

    def on_load(self, client):
        super().on_load(client)
        
        self.code = client._get_game_id()
    
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
                self.animations = client.server.end_turn(self.code)
            if event.type == pg.MOUSEBUTTONDOWN:
                if client.assets.board_rect.collidepoint(event.pos):
                    xy = (np.array(event.pos) - np.array(client.assets.board_rect.topleft)) // _Settings.TILESIZE
                    board_index = xy[0] + xy[1] * 8
                    client.server.board_event(self.code, board_index)
                    client.server.hand_event(self.code, {
                        'side': 0,
                        'board_index': board_index
                    })
                
                for i, card_rect in enumerate(self.card_rects[1]):
                    if card_rect.collidepoint(event.pos):
                        client.server.hand_event(self.code, {
                            'side': 1,
                            'card_index': i
                        })
                
                for i, card_rect in enumerate(self.card_rects[-1]):
                    if card_rect.collidepoint(event.pos):
                        client.server.hand_event(self.code, {
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

    def _render_pieces(
        self, display: pg.Surface, piece_assets: dict[str, pg.Surface], 
        old_keys: np.ndarray, old_colors: np.ndarray,
        new_keys: np.ndarray, new_colors: np.ndarray
    ):
        center = np.array(self.resolution) / 2

        for i in np.arange(64):
            piece_key = new_keys[i]
            piece_colour = new_colors[i]

            xy = center + _Settings.get_xy(i)
            alpha = 1
            if self.animations:
                animation = self.animations[0]
                animation_type = animation[0]
                if animation_type == 'move_piece':
                    old_index, new_index = animation[1:]
                    if i == old_index:
                        old_xy = center + _Settings.get_xy(old_index)
                        new_xy = center + _Settings.get_xy(new_index)
                        xy = _Settings.lerp(new_xy, old_xy, self.animation_time)
                        piece_key = old_keys[i]
                        piece_colour = old_colors[i]
                        alpha = 1
                    elif i == new_index:
                        piece_key = old_keys[i]
                        piece_colour = old_colors[i]
                        alpha = _Settings.lerp(0, 1, self.animation_time)
                elif animation_type == 'tile_effects':
                    board_indices = animation[1]
                    if i in board_indices:
                        alpha = _Settings.lerp(0, 1, self.animation_time)
                        piece_key = old_keys[i]
                        piece_colour = old_colors[i]
                    
                for animation in self.animations[1:]:
                    animation_type = animation[0]
                    if animation_type == 'move_piece':
                        if i in animation[1:]:
                            piece_key = old_keys[i]
                            piece_colour = old_colors[i]
                            alpha = 1
                    if animation_type == 'tile_effects':
                        board_indices = animation[1]
                        if i in board_indices:
                            piece_key = old_keys[i]
                            piece_colour = old_colors[i]
                            alpha = 1
            
            if piece_key == 'none':
                continue

            piece = piece_assets[piece_key].copy()
            piece.set_colorkey((0, 255, 0))
            coloured_piece = pg.Surface(piece.get_size())
            coloured_piece.fill((100, 0, 0)) if piece_colour else coloured_piece.fill((0, 0, 100))
            coloured_piece.blit(piece, (0, 0))
            coloured_piece.set_colorkey((0, 0, 0))
            coloured_piece.set_alpha(int(alpha * 255))

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
                color, board_index, from_side = animation[1:]
                destination = center + _Settings.get_xy(board_index)
                anchor = center * np.array([1, from_side + 1])
                xy = _Settings.lerp(anchor, destination, 1 - self.animation_time)
                self.sparks.add_new_particles(
                    np.array([xy]),
                    2 * np.pi * np.random.rand(1),
                    np.array([color])
                )
            elif animation_type == 'tile_effects':
                board_indices = animation[1]
                xys = center + np.array([
                    _Settings.get_xy(board_index)
                    for board_index in board_indices
                ])
                self.sparks.add_new_particles(
                    xys,
                    2 * np.pi * np.random.rand(xys.shape[0]),
                    np.full((xys.shape[0],3), (255,255,255))
                )
        self.sparks.render(display)

    def render(self, client):
        # menu render
        default = client.displays['default']
        effects = client.displays['gaussian_blur']

        # render the board
        default.blit(client.assets.board, client.assets.board_rect)

        # TODO client should not have server
        render_data = client.server.get_render_data(self.code)

        # render pieces
        self._render_pieces(
            default, client.assets.pieces, 
            render_data['board']['old_keys'], render_data['board']['old_colors'],
            render_data['board']['new_keys'], render_data['board']['new_colors']
        )
        self._render_piece_move_indices(default, render_data['board']['move_indices'])

        # render hand
        hands, played_indices = render_data['hand']
        self._render_hands(
            default, 
            client.assets.cards, 
            hands[1], hands[-1], 
            played_indices[1], played_indices[-1]
        )

        # vfx
        self._render_vfx(effects)
        
        super().render(client)
