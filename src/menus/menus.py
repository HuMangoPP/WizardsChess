import pygame as pg

from ..util.transitions import transition_in, transition_out, TRANSITION_TIME
from ..chess.chess import Board

DEFAULT_DISPLAY = 'default'
EFFECTS_DISPLAY = 'gaussian_blur'
OVERLAY_DISPLAY = 'black_alpha'

class StartMenu:
    def __init__(self, game):
        # import game
        self.width, self.height = game.res
        self.displays = game.displays
        self.font = game.font
        self.clock = game.clock

        # transition handler
        self.goto = 'game'
        self.on_transition()
    
    def on_transition(self):
        # 0 -> no transition
        # 1 -> transition out
        # 2 -> black screen
        # 3 -> transition in
        self.transition_phase = 2
        self.transition_time = 0

    def update(self, events: list[pg.Event]):
        dt = self.clock.get_time() / 1000
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                self.transition_phase = 1
                self.transition_time = 0
                self.goto = 'game'
        
        # handle transitions
        if self.transition_phase > 0:
            self.transition_time += dt
            if self.transition_phase == 1 and self.transition_time > TRANSITION_TIME:
                return {
                    'exit': False,
                    'goto': self.goto
                }
            if self.transition_time > TRANSITION_TIME:
                self.transition_time = 0
                self.transition_phase = (self.transition_phase + 1) % 4
        return {}

    def render(self) -> list[str]:
        self.displays[DEFAULT_DISPLAY].fill((20, 26, 51))
        self.font.render(self.displays[DEFAULT_DISPLAY], 'Wizards Chess', self.width/2, 100, 
                         (255, 255, 255), 50, style='center')

        match self.transition_phase:
            case 1: 
                transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
            case 2:
                self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
            case 3:
                transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)
        
        displays_to_render = [DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        return displays_to_render
            
class GameMenu:
    def __init__(self, game):
        # import game
        self.width, self.height = game.res
        self.displays = game.displays
        self.font = game.font
        self.clock = game.clock
        self.piece_collection = game.piece_collection

        # transition handler
        self.goto = 'start'
        self.on_transition()

        # chess board
        self.white = 'gryffindor_red'
        self.black = 'slytherin_green'
        self.board = Board(self, fen_str='r3k2r/8/p7/8/p7/p7/PPPPPPPP/R3K2R w KQkq 43 0 1')
        
    def on_transition(self):
        # 0 -> no transition
        # 1 -> transition out
        # 2 -> black screen
        # 3 -> transition in
        self.transition_phase = 2
        self.transition_time = 0
    
    def update(self, events: list[pg.Event]):
        dt = self.clock.get_time() / 1000
        for event in events:
            ...
        
        self.board.update(events)

        if self.transition_phase > 0:
            self.transition_time += dt
            if self.transition_phase == 1 and self.transition_time > TRANSITION_TIME:
                return {
                    'exit': False,
                    'goto': self.goto
                }
            if self.transition_time > TRANSITION_TIME:
                self.transition_time = 0
                self.transition_phase = (self.transition_phase + 1) % 4
        return {}

    def render(self) -> list[str]:
        self.displays[DEFAULT_DISPLAY].fill((20, 26, 51))
        self.font.render(self.displays[DEFAULT_DISPLAY], 'Game', self.width/2, 100, 
                         (255, 255, 255), 50, style='center')
        
        self.board.render()

        match self.transition_phase:
            case 1: 
                transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
            case 2:
                self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
            case 3:
                transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)
        
        displays_to_render = [DEFAULT_DISPLAY]

        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        
        return displays_to_render

    