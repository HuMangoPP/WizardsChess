import pygame as pg
import moderngl as mgl

from .network import Network

from .pymgl.graphics_engine import GraphicsEngine
from .pyfont.font import Font
from .util.asset_loader import load_sprites

from .menus.menus import StartMenu, GameMenu, WaitingRoom

MENU_MAP = {
    'start': 0,
    'wait': 1,
    'game': 2
}

COLOR_PALETTES = {
    'gryffindor_red': (174,0,1),
    'gryffindor_gold': (238,186,48),
    'slytherin_silver': (170,170,170),
    'slytherin_green': (42,98,61),
    'ravenclaw_blue': (29,42,84),
    'ravenclaw_silver': (126,126,126),
    'hufflepuff_yellow': (240,199,94),
    'hufflepuff_black': (55,46,41)
}

def get_chess_piece_palettes(chess_pieces: dict[str, pg.Surface]) -> dict[str, dict[str, pg.Surface]]:
    piece_collection = {}
    for color in COLOR_PALETTES:
        piece_set = {}
        for piece in chess_pieces:
            colored_piece = pg.Surface(chess_pieces[piece].get_size())
            colored_piece.fill(COLOR_PALETTES[color])
            colored_piece.blit(chess_pieces[piece], (0, 0))
            colored_piece.set_colorkey((0, 0, 0))
            piece_set[piece] = colored_piece
        
        piece_collection[color] = piece_set
    
    return piece_collection

def get_spell_card_palettes(card_designs: dict[str, pg.Surface]) -> dict[str, dict[str, pg.Surface]]:
    card_collection = {}
    for color in COLOR_PALETTES:
        card_set = {}
        for card in card_designs:
            colored_card = pg.Surface(card_designs[card].get_size())
            colored_card.fill(COLOR_PALETTES[color])
            colored_card.blit(card_designs[card], (0, 0))
            card_set[card] = colored_card
        
        card_collection[color] = card_set
    
    return card_collection

class Client:
    def __init__(self):
        pg.init()
        self.res = (960, 1000)

        pg.display.set_mode(self.res, pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = (
            mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        )
        self.graphics_engine = GraphicsEngine(self.ctx, self.res, './src/client')
        self.font = Font(pg.image.load('./src/client/pyfont/font.png').convert())
        self.displays = {
            'default': pg.Surface(self.res),
            'gaussian_blur': pg.Surface(self.res),
            'black_alpha': pg.Surface(self.res)
        }
        self.clock = pg.time.Clock()

        self.piece_collection = get_chess_piece_palettes(load_sprites(path='./assets/chess_pieces', scale=4, colorkey=(0, 255, 0)))
        self.card_collection = get_spell_card_palettes(load_sprites(path='./assets/cards', scale=4, colorkey=(0, 0, 0)))

        self.menus = [StartMenu(self), WaitingRoom(self), GameMenu(self)]
        self.current_menu = 0
    
    def create_new_connection(self):
        self.n = Network()
        self.p_side = self.n.get_p()
        # self.game_id = self.n.get_game_id()
        self.game_id = -1

    def update(self):
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                return {
                    'exit': True
                }
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return {
                    'exit': True
                }
        
        return self.menus[self.current_menu].update(events)
        
    def render(self):
        self.ctx.clear(0.08, 0.1, 0.2)
        displays_to_render = self.menus[self.current_menu].render()
        [self.graphics_engine.render(self.displays[display], self.displays[display].get_rect(),
                                     shader=display) for display in displays_to_render]
        
    def run(self):
        self.menus[self.current_menu].on_load()
        while True:
            exit_status = self.update()
            if exit_status:
                if exit_status['exit']:
                    pg.quit()
                    return
                else:
                    self.current_menu = MENU_MAP[exit_status['goto']]
                    self.menus[self.current_menu].on_load()
            self.render()
            self.clock.tick()
            pg.display.flip()

            pg.display.set_caption(f'fps: {self.clock.get_fps()}')