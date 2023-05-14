import pygame as pg
import numpy as np
import math

from ..vfx.particles import Sparks

class Hand:
    def __init__(self, font, hand: list[str], card_designs: dict[str, dict[str, pg.Surface]], color_theme: str):
        self.cards = [Card(font, card_designs, card_name, color_theme) for card_name in hand]
        # a card is a struct specifying a unique id (for reference),
        # a sprite, a descriptions, and some additional data representing
        # card functionality, perhaps a target (which can be a chess piece),
        # a timer (the duration left for the card's effect), an effect key
        # (to keep track of what the effect is), etc...
        self.card_width = card_designs['gryffindor_gold']['border'].get_width()
        self.card_height = card_designs['gryffindor_gold']['border'].get_height()

    def update(self, events: list[pg.Event], dt: float):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                [card.click(event.pos) for card in self.cards]
            
        [self.cards[i].update((self.card_width * (i - len(self.cards) / 2) + 500, 750), dt) for i in range(len(self.cards))]

    def render(self, displays: dict[str, pg.Surface]):
        [card.render(displays) for card in self.cards]

# this class will allow me to encapsulate some static functionality that i want for a card
# this dict maps spell names to a parametric function that determines the wand path
# each card is [name: str, num_moves: int, optional: int]
CARD_EFFECTS = {
    'avada_kedavra': ['death', 1], # literally dies
    'accio': ['move_close', 1, 1], # moves any of your pieces towards you 1 or 2 squares
    'depulso': ['move_away', 1, 1], # moves any of your pieces away from you 1 or 2 squares
    'confundus': ['move_random', 1], # randomly moves like a king
    'deprimo': ['remove_square', 2], # removes a square from being used for 2/3 moves, cannot be used on occupied squares
    'reducio': ['shrink', 2], # can move but cannot capture
    'expelliarmus': ['backfire', 3], # next attack from this piece fails
    'disillusionment': ['invisible', 2], # the chess piece becomes invisible for 2/3 moves
    'duro': ['cannot_move', 1], # turns to stone, cannot move for 1 move
    'engorgio': ['grow', 2], # counter spell for shrink
    # 'expecto_patronum': '', #
    'fiendfyre': ['area_attack', 1, 2], # used on a piece and allows it to capture any enemy piece in a given radius, the attacking piece is removed afterwards
    'finite_incantatem': ['remove', 1], # removes a random effect on a piece
    'flipendo': ['move_away', 1, 2], # similar to depulso, perhaps a stronger variant?
    'immobulus': ['cannot_move', 2], # stronger variant of duro
    'petrificus_totalus': ['cannot_move', 3], # strongest variant of duro
    'fumos': ['invisible', 2], # weaker variant, not true invisibility
    'apparition': ['move_anywhere', 1], # moves one of your pieces anywhere so long as the new square is not occupied
    'cruciatus': ['cannot_move', -1], # piece cannot be moved for the rest of the game
    'confringo': ['area_attack', 1, 1], # similar to fiendfyre
    'impedimenta': ['move_random', 1], # opponent piece randomly moves to unoccupied tile
    'imperius': ['control', 3], # allows player to control an enemy piece for 3 moves
    'locomotor': ['control', 1], # weaker variant of imperius
    'legilimens': ['reveal', 1], # permanently reveals one of opponent's cards (you know when they play the card)
    'revelio': ['reveal', 1], # reveals one of opponent's cards
    'obscuro': ['invisible', 1], # weaker
    'reparo': ['repair', 1], # repairs broken grid tiles
    'prior_incantato': ['echo', 1], # allows the user to use the last spell on the field (from either side)
    'protego': ['shield', 2], # target cannot be captured for 2 rounds, attempts to capture are stopped and opponent uses a move
    'stupefy': ['break', 1], # breaks a shield

}

SPELL_COLORS = {
    'avada_kedavra': (25, 50, 25),
    'accio': (25, 25, 25),
    'depulso': (25, 25, 25),
    'confundus': (40, 20, 25),
    'deprimo': (25, 40, 25),
    'reducio': (35, 20, 35),
    'expelliarmus': (50, 25, 25),
    'disillusionment': (25, 25, 25),
    'duro': (25, 25, 25),
    'engorgio': (20, 25, 40),
    'fiendfyre': (40, 30, 20),
    'finite_incantatem': (45, 25, 25),
    'flipendo': (35, 35, 20),
    'immobulus': (25, 25, 50),
    'petrificus_totalus': (25, 25, 25),
    'fumos': (20, 20, 20),
    'cruciatus': (50, 25, 25),
    'confringo': (40, 30, 20),
    'impedimenta': (20, 35, 35),
    'imperius': (30, 30, 30),
    'locomotor': (25, 25, 25),
    'legilimens': (25, 25, 25),
    'reparo': (25, 35, 45),
    'prior_incantato': (40, 35, 20),
    'protego': (30, 30, 30),
    'stupefy': (50, 25, 25),
    'apparition': (25, 25, 25),
    'revelio': (40, 40, 25),
    'obscuro': (25, 25, 25),
}

SPELL_WAND_PATHS = {
    'avada_kedavra': lambda t : (-0.3 * (t - math.floor(0.5 + t)), 0.6 * (t - 0.5)),
    'accio': lambda t : (-0.3 * math.cos(math.pi * t), -0.25 * math.sin(math.pi * t)),
    'depulso': lambda t : (-0.3 * math.cos(math.pi * t), 0.25 * math.sin(math.pi * t)),
    'confundus': lambda t : (min(0.25, t) * math.sin(2 * math.pi * t), 
                             -0.5 / (0.5 + t) * math.sin(5 * math.pi / 6 * t) + 0.3),
    'deprimo': lambda t : ((t + 1) / 4 * max(min(math.sin(2 * math.pi * (t + 0.1)), 0.6), -0.6),
                           0.5 / (t + 1) * max(min(math.cos(2 * math.pi * (t + 0.1)), 0.6), -0.6)),
    'reducio': lambda t : (0.8 * (t - 0.5), -1.25 * abs(t - 0.5) + 0.3),
    'expelliarmus': lambda t : (-0.5 / (5 * t + 1.1) * math.sin(12 / 3.2 * math.pi * t),
                                -0.35 / (5 * t + 1.1) * math.cos(12 / 3.2 * math.pi * t)),
    'disillusionment': lambda t : (-0.35 / (2 * t + 1.1) * math.cos(12 / 3.2 * math.pi * t),
                                   -0.5 / (5 * t + 1.1) * math.sin(12 / 3.2 * math.pi * t)),
    'duro': lambda t : (-0.2 if t < 0.5 else 0.5 * math.sin(2 * math.pi * (t - 0.5)) - 0.2, 
                        -0.35 * math.cos(2 * math.pi * (t - 0.5))),
    'engorgio': lambda t : (-0.3 * math.sin(2 * math.pi * t) if (0.1 <= t and t <= 0.9) else -0.3 * math.sin(2 * math.pi * min(max(t, 0.1), 0.9)),
                            -0.35 * math.cos(2 * math.pi * t) if (0.1 <= t and t <= 0.9) else -0.35),
    'fiendfyre': lambda t : (0.8 * (t - 0.5), t * (0.2 * round(math.sin(math.pi / 1.5 * t) - 0.4) + 0.1) if t <= 0.9 else -0.4),
    'finite_incantatem': lambda t : (-1.5 * (abs(t - 0.5) - 0.25),
                                     1.5 * (t - 0.25) if t <= 0.5 else 1.5 * (t - 0.75)),
    'flipendo': lambda t : (0.85 * (t - 0.5) if t <= 0.5 else -0.2 * math.cos(2 * math.pi * (t-0.5)) + 0.2, 
                            -2*abs(t-0.25) + 0.25 if t <= 0.5 else 0.25 * math.sin(2 * math.pi * (t - 0.5))),
    'immobulus': lambda t : (0.85 * (t - 0.5), -0.85 * ((math.sin(2 * math.pi * (t - 0.5)))**2 - 0.5)),
    'petrificus_totalus': lambda t : (-0.2 * math.cos(2 * math.pi * t) - 0.2 if t <= 0.5 else t - 0.5,
                                      0.2 * math.sin(2 * math.pi * t) if t <= 0.5 else 0),
    'fumos': lambda t : (0.4 / (t + 1) * math.sin(2.2 * math.pi * t), 
                         0.4 / (t + 1) * math.cos(2.2 * math.pi * t)),

    'cruciatus': lambda t : (-1.85 * (abs(t / 0.5 - math.floor(t / 0.5 + 0.5)) - 0.25), 0.85 * (t - 0.5)),
    'confringo': lambda t : (1.85 * (abs(t / 0.66 - math.floor(t / 0.66 + 0.5)) - 0.25),
                             0.6 * (1 / (1 + math.exp(-10 * (t - 0.5))) - 0.5)),
    'impedimenta': lambda t : (0.85 * (t - 0.5), 0),
    'imperius': lambda t : (-(abs(t - math.floor(t + 0.5)) - 0.25) if t <= 0.85 else 0.1,
                            0.25 if t <= 0.5 else -abs(t / 0.5 - math.floor(t / 0.5 + 0.5)) + 0.25),
    'locomotor': lambda t : (0.85 * (t - 0.5), -0.85 * (t - 0.5)),
    'legilimens': lambda t : (-1.9 * (abs(t - 0.5) - 0.25), -0.2 * math.sin(2 * math.pi * t)),
    'reparo': lambda t : (1.5 * (abs((t - 0.25) - math.floor((t - 0.25) + 0.5)) - 0.25),
                          -2 * abs(max(min(t, 0.75), 0.25) - 0.45) + 0.25),
    'prior_incantato': lambda t : (-0.45 * math.sin(2 * math.pi * t), -0.45 * math.cos(2 * math.pi * t)),
    'protego': lambda t : (0, -0.85 * (t - 0.5)),
    'stupefy': lambda t : (0, 0.85 * (t - 0.5)),
    'apparition': lambda t : (0.4 * t * math.cos(6 * math.pi * t), (0.4 * t * math.sin(6 * math.pi * t))),
    'revelio': lambda t : (-0.07 if t <= 0.1 else max(-0.2 * math.sin(2 * math.pi / 0.9 * (t - 0.6)), 0.85 * (t - 0.6)),
                           0.35 if t <= 0.1 else max(0.2 * math.cos(2 * math.pi / 0.9 * (t - 0.6)), 0.85 * (t - 0.6))),
    'obscuro': lambda t : (-0.35 * math.cos(2 * math.pi * (t - 0.1)) if t <= 0.75 else -2 * (t - 0.85),
                           0.35 * math.sin(2 * math.pi * (t - 0.1)) if t <= 0.75 else 2 * (t - 0.85))
}

SPELL_DESC = {
    'avada_kedavra': 'instantly kill an opponent piece. killing the king is checkmate.',
    'accio': 'instantly move a piece one square towards you.',
    'depulso': 'instantly move a piece one sqaure away from you',
    'confundus': 'instantly cause an opponent piece to move randomly to an empty square.',
    'deprimo': 'instantly destroy an empty tile, so it cannot be occupied for the rest of the game.',
    'reducio': 'shrink an opponent piece. shrunk pieces can move but cannot capture. counter spell for engorgio.',
    'expelliarmus': 'your opponents next spell will have no effect.',
    'disillusionment': 'target piece will become invisible for 2 rounds.',
    'duro': 'target piece cannot move for the next round.',
    'engorgio': 'enlarge a piece. enlarged pieces can capture an adjacent square. counter spell for reducio.',
    'fiendfyre': 'capture any piece as long as it is 2 squares away. this piece dies afterwards.',
    'finite_incantatem': 'general counter spell. remove any spell effect on a piece.',
    'flipendo': 'instantly move a piece two squares away from you.',
    'immobulus': 'target piece cannot move for the next 2 rounds.',
    'petrificus_totalus': 'target piece cannot move for the next 3 rounds.',
    'fumos': 'target piece will be invisible for the next round.',
    'cruciatus': 'target piece cannot move for the rest of the game.',
    'confringo': 'capture any piece so long as it is adjacent.',
    'impedimenta': 'instantly cause an opponent piece to move randomly one square.',
    'imperius': 'control the target piece for the next 3 rounds.',
    'locomotor': 'control the target piece for the next round.',
    'legilimens': 'reveal all cards in play.',
    'reparo': 'repair a broken tile.',
    'prior_incantato': 'use the last spell performed by either side.',
    'protego': 'shield a piece from the next spell. lasts 3 rounds.',
    'stupefy': 'quick cast. overcomes protego.',
    'apparition': 'instantly moves any piece on the board to any empty square.',
    'revelio': 'reveal your opponents entire hand.',
    'obscuro': 'opponent cannot see you cast a spell.',
}

def draw_wand_path(card: pg.Surface, path: callable):
    width, height = card.get_size()
    points = [path(t/20) for t in range(0, 20)]
    for i in range(len(points) - 1):
        pg.draw.line(card, (255, 255, 255), 
                     np.array([width/2, height/2]) + np.array([(width - 50) * points[i][0], (width-50) * points[i][1]]), 
                     np.array([width/2, height/2]) + np.array([(width - 50) * points[i+1][0], (width-50) * points[i+1][1]]), 5)

def render_card_name(font, card: pg.Surface, spell_name: str):
    width = card.get_width()
    text = spell_name.replace('_', ' ')
    font.render(card, text, width / 2, 40, (255, 255, 255), 10, 'center', box_width=width-20)

def trace_wand_path(card_rect: pg.Rect, path: callable, t: float):
    anchor = path(t)
    width, height = card_rect.size
    return np.array(card_rect.center) + (width - 50) * np.array([anchor[0], anchor[1]])

def render_card_desc(font, card: pg.Surface, spell_name: str):
    font.render(card, SPELL_DESC[spell_name], 35, 50, (255, 255, 255), 10, box_width=card.get_width()-70)

class Card:
    def __init__(self, font, card_designs: dict[str, dict[str, pg.Surface]], spell: str, color_theme: str):
        card = card_designs[color_theme]['border'].copy()
        draw_wand_path(card, SPELL_WAND_PATHS[spell])
        render_card_name(font, card, spell)
        text = card_designs[color_theme]['border'].copy()
        render_card_desc(font, text, spell)
        self.draw_rect = card.get_rect()

        self.card_faces = [
            card, # i can potentially draw this using vfx procedurally
            text, # this one is drawn
        ]
        
        self.spell = spell
        self.t = 0
        self.spell_color = SPELL_COLORS[spell]
        self.sparks = Sparks(self.draw_rect.center, self.spell_color)
        self.current_side_up = 0

        # status effects of the card
        self.card_effect = CARD_EFFECTS[spell]
    
    def update(self, topleft: tuple[int, int], dt: float):
        self.draw_rect.top = topleft[1]
        self.draw_rect.left = topleft[0]

        self.t += dt
        if self.t > 1:
            self.t -= 1
        new_anchor = trace_wand_path(self.draw_rect, SPELL_WAND_PATHS[self.spell], self.t)
        self.sparks.update(dt, new_anchor)

    def click(self, mouse: tuple[int, int]):
        if self.draw_rect.collidepoint(mouse):
            self.scroll_card_face()

    def scroll_card_face(self):
        self.current_side_up = (self.current_side_up + 1) % 2

    def render(self, displays: dict[str, pg.Surface]):
        displays['default'].blit(self.card_faces[self.current_side_up], self.draw_rect)
        if self.current_side_up == 0:
            self.sparks.render(displays['gaussian_blur'])

class HiddenHand:
    def __init__(self, hand_size: int, card_designs: dict[str, dict[str, pg.Surface]], color_theme: str):
        self.cards = [HiddenCard(card_designs, color_theme) for i in range(hand_size)]
        self.card_width = card_designs['gryffindor_gold']['border'].get_width()
        self.card_height = card_designs['gryffindor_gold']['border'].get_height()

    def update(self):
        [self.cards[i].update((self.card_width * (i - len(self.cards) / 2) + 500, 0)) for i in range(len(self.cards))]

    def render(self, display: pg.Surface):
        [card.render(display) for i, card in enumerate(self.cards)]

class HiddenCard:
    def __init__(self, card_designs: dict[str, dict[str, pg.Surface]], color_theme: str):
        self.card_face = card_designs[color_theme]['sleeve'].copy()
        self.draw_rect = self.card_face.get_rect()
    
    def update(self, topleft: tuple[int, int]):
        self.draw_rect.top = topleft[1]
        self.draw_rect.left = topleft[0]

    def render(self, display: pg.Surface):
        display.blit(self.card_face, self.draw_rect)