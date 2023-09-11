import pygame as pg
import numpy as np

from ..util.asset_loader import load_json, load_spritesheet


class _Settings:
    TILESIZE = 32

    COLOUR_THEMES = load_json('./assets/chess/colour_themes.json')

    EMPTY = 0


def _get_paletted_pieces(
    pieces: dict[int, pg.Surface], 
    colour_theme: dict, 
    neg: int = 1
):
    paletted_pieces = {}
    for piece_enum, piece_surf in pieces.items():
        paletted_piece_surf = pg.Surface(piece_surf.get_size())
        paletted_piece_surf.fill(colour_theme['main'])
        paletted_piece_surf.blit(piece_surf, (0,0))
        paletted_piece_surf.set_colorkey((0,0,0))
        
        paletted_pieces[neg * piece_enum] = paletted_piece_surf
    
    return paletted_pieces


class BoardRenderer:
    def __init__(self, menu):
        self.menu = menu
        self._create_checker_board()
        self._create_pieces()
        self.clear_animation()

    def clear_animation(self):
        self.slide_vel = np.zeros(2,np.float32)
        self.movement = np.full((2,2), -1)

    def _create_checker_board(self):
        self.checker_board = pg.Surface((_Settings.TILESIZE * 8, _Settings.TILESIZE * 8))
        self.colour_theme = _Settings.COLOUR_THEMES[self.menu.theme]
        self.other_colour_theme = _Settings.COLOUR_THEMES[self.menu.other_theme]

        for rank in np.arange(8):
            for file in np.arange(8):
                if (rank + file) % 2 == 0:
                    colour = self.colour_theme['light']
                else:
                    colour = self.colour_theme['dark']
                pg.draw.rect(
                    self.checker_board,
                    colour,
                    pg.Rect(
                        rank * _Settings.TILESIZE,
                        file * _Settings.TILESIZE,
                        _Settings.TILESIZE,
                        _Settings.TILESIZE
                    )
                )
        
        self.board_rect = self.checker_board.get_rect()
        self.board_rect.center = (np.array(self.menu.client.screen_size) / 2)

    def _create_pieces(self):
        pieces = load_spritesheet(
            './assets/chess/pieces.png', 
            [1,2,3,4,5,6],
            scale=2,
            colorkey=(0,255,0)
        )
        self.pieces = {
            **_get_paletted_pieces(pieces, self.colour_theme),
            **_get_paletted_pieces(pieces, self.other_colour_theme, -1)
        }

        self.hovering = [-1,-1]
        self.holding = [-1, -1]

        self.piece_rects = [
            [
                pg.Rect(
                    file * _Settings.TILESIZE, 
                    (rank - 1) * _Settings.TILESIZE, 
                    _Settings.TILESIZE, 
                    2 * _Settings.TILESIZE
                ) 
                for file in np.arange(8)
            ]
            for rank in np.arange(8)
        ]

    def _render_pieces(self, display: pg.Surface):
        fixed = self.menu.board_state == self.menu.dummy_board_state
        for rank, state_row in enumerate(self.menu.board_state):
            for file, tile in enumerate(state_row):
                if np.all(np.array([rank,file]) == self.movement[1]):
                    continue

                if fixed[rank,file]:
                    self.piece_rects[rank][file].topleft = [
                        file * _Settings.TILESIZE,
                        (rank - 1) * _Settings.TILESIZE
                    ]
                
                if tile == _Settings.EMPTY:
                    continue
                
                if self.holding[0] == rank and self.holding[1] == file:
                    self.piece_rects[rank][file].center = pg.mouse.get_pos() - np.array(self.board_rect.topleft)
                elif (self.hovering[0] == rank and self.hovering[1] == file and self.holding[0] == -1):
                    self.piece_rects[rank][file].top = (rank - 2) * _Settings.TILESIZE
                
                self.piece_rects[rank][file].topleft = self.piece_rects[rank][file].topleft + np.array(self.board_rect.topleft)

                piece = self.pieces[tile]

                drawpos = self.piece_rects[rank][file].topleft
                
                display.blit(piece, drawpos)

    def _render_possible_moves(self, display: pg.Surface):
        for rank, row in enumerate(self.menu.possible_moves):
            for file, tile in enumerate(row):
                if tile:
                    drawpos = (
                        np.array(self.board_rect.center) + 
                        (np.array([file, rank]) - 7 / 2) * _Settings.TILESIZE
                    )
                    pg.draw.circle(
                        display, 
                        (0, 255, 0),
                        drawpos,
                        _Settings.TILESIZE / 4
                    )

    def render(self, display: pg.Surface):
        display.blit(
            self.checker_board,
            self.board_rect
        )

        self._render_possible_moves(display)
        self._render_pieces(display)

    def create_board_move_animation(self, t: float):
        fixed = self.menu.board_state == self.menu.dummy_board_state
        different = np.column_stack(np.where(np.invert(fixed)))
        if different.size == 0:
            return

        if different.shape[0] > 2:
            ...
        else:
            if self.menu.dummy_board_state[tuple(different[0])] == _Settings.EMPTY:
                # moved from 0
                self.movement = different.copy()
                self.slide_vel = np.diff(self.movement, axis=0) * _Settings.TILESIZE / t
            else:
                # moved from 1
                self.movement = different[::-1]
                self.slide_vel = np.diff(self.movement, axis=0) * _Settings.TILESIZE / t
            self.slide_vel = self.slide_vel[0,::-1]

    def animate_board_move(self, dt: float):
        if self.movement[0][0] != -1:
            rank,file = self.movement[0]
            xy = self.piece_rects[rank][file].topleft - np.array(self.board_rect.topleft) + self.slide_vel * dt

            if not np.all(np.logical_and(
                    (np.min(self.movement[:,::-1], axis=0) - np.array([0,1])) * _Settings.TILESIZE <= xy,
                    xy <= (np.max(self.movement[:,::-1], axis=0) - np.array([0,1]))  * _Settings.TILESIZE
                )
            ):
                xy = (self.movement[1,::-1] - np.array([0,1])) * _Settings.TILESIZE
                self.menu.board_state = self.menu.dummy_board_state
                self.clear_animation()
            
            self.piece_rects[rank][file].topleft = xy
                
    def create_death_animation(self, t: float):
        ...

    def animate_death(self, dt: float):
        self.menu.board_state = self.menu.dummy_board_state
