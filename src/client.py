import numpy as np
import pandas as pd
import pygame as pg

from .pymenus import *


class _Settings:
    RESOLUTION = (1280, 720)
    MENU_MAP = dict(main=0, game=1, lobby=2)
    WINDOW_NAME = 'Wizard Chess'

    TILESIZE = 48
    COLOURS = dict()


class Client:
    def __init__(self, use_mgl: bool = False):
        self.use_mgl = use_mgl
        self._pg_init()
        self.assets = self.Assets('./assets', self.resolution)
        self._setup_menus()
        self._setup_server()
    
    def _pg_init(self):
        # init
        pg.init()

        # get window and ctx
        self.resolution = _Settings.RESOLUTION
        if self.use_mgl:
            import moderngl as mgl
            from .pymgl import GraphicsEngine
            pg.display.set_mode(self.resolution, pg.OPENGL | pg.DOUBLEBUF)
            self.ctx = mgl.create_context()
            self.ctx.enable(mgl.BLEND)
            self.ctx.blend_func = (
                mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
            )

            # get graphics engine, font, and displays
            self.graphics_engine = GraphicsEngine(self.ctx, self.resolution, './src')

            # create displays
            self.displays = dict(
                default=pg.Surface(self.resolution),
                gaussian_blur=pg.Surface(self.resolution),
                overlay=pg.Surface(self.resolution)
            )
        else:
            # get window
            self.window = pg.display.set_mode(self.resolution, pg.DOUBLEBUF)

            # create displays
            self.displays = dict(
                default=pg.Surface(self.resolution),
                overlay=pg.Surface(self.resolution)
            )
            self.displays['overlay'].set_colorkey((0, 0, 0))
        
        # font
        from .pyfont import Font
        self.font = Font(pg.image.load('./src/pyfont/font.png').convert())

        # window title
        pg.display.set_caption(_Settings.WINDOW_NAME)

        # clock
        self.clock = pg.time.Clock()
        self.dt = 0
        
        # events
        self.events = []
    
    def _setup_menus(self):
        # menus
        self.menus : list[Menu] = [
            MainMenu(self),
            GameMenu(self),
            LobbyMenu(self)
        ]
        self.current_menu = 0
    
    def _setup_server(self):
        from .server import Server
        self.server = Server()

    def _get_lobby_type(self):
        return self.menus[0].lobby_type

    def _get_game_id(self):
        return self.menus[2].code

    def update(self):
        # quit client
        for event in self.events:
            if event.type == pg.QUIT:
                return dict(exit=True)
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return dict(exit=True)
        
        # not done loading assets
        if not self.assets.finished_loading:
            self.assets.load_assets(self)
            self.menus[self.current_menu].transition_time = 0
        
        # menu update
        return self.menus[self.current_menu].update(self)

    def render(self):
        if self.use_mgl:
            self.ctx.clear(0.08, 0.1, 0.2)
        else:
            self.window.fill((0, 0, 0))

        # render to pg surface
        [display.fill((0, 0, 0)) for display in self.displays.values()]
        self.menus[self.current_menu].render(self)

        # not done loading assets
        if not self.assets.finished_loading:
            font_size = 25
            num_dots = (self.assets.progress // 5) % 3 + 1
            self.font.render(
                self.displays['overlay'],
                "loading",
                np.array(self.resolution) / 2 + np.array([-font_size * 1.5, 0]),
                (255, 255, 255),
                font_size,
                style='center'
            )
            self.font.render(
                self.displays['overlay'],
                "." * num_dots,
                np.array(self.resolution) / 2 + np.array([font_size * 2, -self.font.char_height(font_size) / 2]),
                (255, 255, 255),
                font_size,
                style='topleft'
            )
        
        # render cursor
        # self.displays['overlay'].blit(self.assets.cursor, pg.mouse.get_pos())

        if self.use_mgl:
            # render using graphics engine to screen
            [self.graphics_engine.render(
                display, 
                shader=shader
            ) for shader, display in self.displays.items()]
        else:
            [self.window.blit(display, (0, 0)) for display in self.displays.values()]

    def run(self):
        # on load
        self.menus[self.current_menu].on_load(self)
        while True:
            # update
            self.dt = self.clock.get_time() / 1000
            self.clock.tick()
            self.events = pg.event.get()
            exit_status = self.update()
            if exit_status:
                if exit_status['exit']:
                    pg.quit()
                    return
                else: # menu transitions
                    self.current_menu = _Settings.MENU_MAP[exit_status['goto']]
                    self.menus[self.current_menu].on_load(self)
            
            # render
            self.render()
            pg.display.flip()

    class Assets:
        def __init__(self, path: str, resolution: tuple):
            self.path = path

            # progress
            self.finished_loading = False
            self.progress = 0
        
        def _load_pieces(self):
            pieces = pg.image.load(f'{self.path}/chess/pieces.png').convert()
            piece_width = pieces.get_width() / 6
            piece_height = pieces.get_height()
            piece_names = ['king', 'queen', 'bishop', 'knight', 'rook', 'pawn']
            scale = _Settings.TILESIZE / 16 * 3 / 4
            self.pieces = {
                piece_name: pg.transform.scale_by(pieces.subsurface(pg.Rect(i * piece_width, 0, piece_width, piece_height)), scale)
                for i, piece_name in enumerate(piece_names)
            }
            [piece.set_colorkey((0, 0, 0)) for piece in self.pieces.values()]

        def _load_cards(self, client):
            card_data = pd.read_csv(f'{self.path}/cards/card_data.csv', index_col=0)
            self.cards = {}
            card_size = (200, 100)
            for row in card_data.itertuples():
                card = pg.Surface(card_size)
                card.fill((100, 100, 100))
                client.font.render(
                    card,
                    row[1],
                    (card_size[0] / 2, card_size[1] / 2),
                    (255, 255, 255),
                    10, 
                    style='center'
                )
                self.cards[row[0]] = card

        def _prerender_board(self, client):
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
            self.board_rect.center = (np.array(client.resolution) / 2).astype(float)

        def load_assets(self, client):
            # load assets
            self._load_pieces()
            self._load_cards(client)
            self._prerender_board(client)

            # check load completion
            if True:
                self.finished_loading = True
            else:
                self.progress += 1
