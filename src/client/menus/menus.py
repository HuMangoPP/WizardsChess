import pygame as pg

from ..util.transitions import transition_in, transition_out, TRANSITION_TIME

from ..game.chess import Board
from ..game.cards import Hand, HiddenHand

DEFAULT_DISPLAY = 'default'
EFFECTS_DISPLAY = 'gaussian_blur'
OVERLAY_DISPLAY = 'black_alpha'

class StartMenu:
    def __init__(self, client):
        # import game
        self.width, self.height = client.res
        self.displays = client.displays
        self.font = client.font
        self.clock = client.clock

        # transition handler
        self.goto = 'wait'
    
    def on_load(self):
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
                self.goto = 'wait'
        
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

class WaitingRoom:
    def __init__(self, client):
        self.width, self.height = client.res
        self.displays = client.displays
        self.font = client.font
        self.clock = client.clock
        self.client = client

        # transition handler
        self.goto = 'game'

    def on_load(self):
        self.on_transition()
        
        self.client.create_new_connection()

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

        if self.transition_phase == 0:
            req = {
                'req_type': 'ready'
            }
            try:
                res = self.client.n.send(req)
                if res['game_state']:
                    self.goto = 'game'
                    self.transition_phase = 1
            except:
                self.goto = 'start'
                self.transition_phase = 1
        
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
        self.font.render(self.displays[DEFAULT_DISPLAY], 'Waiting for game to start...', self.width/2, self.height/2-100, 
                         (255, 255, 255), 30, style='center', box_width=self.width-100)
        self.font.render(self.displays[DEFAULT_DISPLAY], f'you are player {self.client.p_side}',
                         self.width/2, self.height/2+50, (255, 255, 255), 30, style='center')
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
    def __init__(self, client):
        # import game
        self.width, self.height = client.res
        self.displays = client.displays
        self.font = client.font
        self.clock = client.clock
        self.client = client
        
        # assets
        self.piece_collection = client.piece_collection
        self.card_collection = client.card_collection

        # transition handler
        self.goto = 'start'

        # chess board
        self.white_theme = 'gryffindor_red'
        self.black_theme = 'slytherin_green'
    
    def on_load(self):
        self.on_transition()
        
        self.p_side = self.client.p_side
        self.game_id = self.client.game_id

        req = {
            'req_type': 'board',
            'p_side': self.p_side
        }
        res = self.client.n.send(req)
        self.board = Board(self, res['board_state'], res['occupy'])

        req = {
            'req_type': 'hand',
            'p_side': self.p_side
        }
        res = self.client.n.send(req)
        self.p_hand = Hand(res['p_hand'], self.card_collection, self.white_theme)
        self.o_hand = HiddenHand(res['o_hand'], self.card_collection, self.white_theme)

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
        
        # get board state and update
        try:
            req = {
                'req_type': 'board',
                'p_side': self.p_side
            }
            res = self.client.n.send(req)
            self.board.update_board_state(res['board_state'], res['occupy'])
        except:
            pass
            
        # board update for getting legal moves and making moves
        req = self.board.update(events)
        if req:
            try:
                res = self.client.n.send(req)
                if res:
                    self.board.update_legal_moves(res['legal_moves'])
            except:
                pass

        # hand update
        self.p_hand.update(events)

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
        if self.board.can_move:
            self.font.render(self.displays[DEFAULT_DISPLAY], 'your turn', self.width/2, 30, 
                            (255, 255, 255), 25, style='center')
        else:
            self.font.render(self.displays[DEFAULT_DISPLAY], 'opponents turn', self.width/2, 30, 
                            (255, 255, 255), 25, style='center')
        
        self.board.render()
        self.p_hand.render(self.displays[DEFAULT_DISPLAY])
        self.o_hand.render(self.displays[DEFAULT_DISPLAY])

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

    