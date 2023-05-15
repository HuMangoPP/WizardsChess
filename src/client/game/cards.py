import pygame as pg
import numpy as np
import math

from ..vfx.particles import Sparks
from ..util.asset_loader import load_json

TILESIZE = 48

class Hand:
    def __init__(self, menu, hand: list[str]):
        self.menu = menu
        self.font = menu.font
        self.card_designs = menu.card_collection
        self.color_theme = menu.white_theme
        self.cards = []
        self.queue = []
        self.update_hand(hand, [])

        self.card_width = self.card_designs['gryffindor_gold']['border'].get_width()
        self.card_height = self.card_designs['gryffindor_gold']['border'].get_height()

        self.new_card_in_queue = None

    def update_hand(self, hand: list[str], queue: list[tuple[str, int]]):
        new_hand = [card for card in self.cards if card.spell in hand]
        [hand.remove(card.spell) for card in new_hand]
        [new_hand.append(Card(self.font, self.card_designs, spell, self.color_theme)) for spell in hand]
        self.cards = new_hand

        # a card in the queue is represented by [Card object, target square]
        self.queue = [card_play for card_play in self.queue if [card_play[0].spell, card_play[1]] in queue]

    def input(self, events: list[pg.Event]) -> dict:
        req = {}
        for event in events:
            if event.type == pg.MOUSEBUTTONUP:
                # determine which cards in queue were clicked
                if self.new_card_in_queue:
                    zeroed_x = event.pos[0] - self.menu.board.board_rect.left
                    zeroed_y = event.pos[1] - self.menu.board.board_rect.top
                    chunked_x = zeroed_x // TILESIZE
                    if self.menu.board.flip:
                        chunked_y = 7 - zeroed_y // TILESIZE
                    else:
                        chunked_y = zeroed_y // TILESIZE
                    if (0 <= chunked_x and chunked_x < 8) and (0 <= chunked_y and chunked_y < 8):
                        target = chunked_x + chunked_y * 8
                        new_card_play = [self.new_card_in_queue, target]
                        self.queue.append(new_card_play)
                        req = {
                            'req_type': 'play_cards',
                            'p_side': self.menu.p_side,
                            'cards': [[card[0].spell, card[1]] for card in self.queue],
                        }
                    self.new_card_in_queue = None
                    
                else:
                    # get the card in the hand that was clicked
                    card_queue = set([card_play[0] for card_play in self.queue])
                    to_queue = [card for card in self.cards if card.click(event.pos) and card not in card_queue]
                    if to_queue:
                        self.new_card_in_queue = to_queue[0]

                    # get the indices in queue that are to be returned
                    to_hand = {i for i, card in enumerate(self.queue) if card[0].click(event.pos)}
                    [self.queue.pop(i) for i in to_hand]
                

        return req

    def update(self, events: list[pg.Event], dt: float):
        for event in events:
            if event.type == pg.MOUSEBUTTONUP:
                [card.scroll_card_face(event.pos) for card in self.cards]
        card_queue = set([card_play[0] for card_play in self.queue])
        [card.update((self.card_width * (i - len(self.cards) / 2) + 500, 650 if card in card_queue else 750), dt) for i, card in enumerate(self.cards)]

    def render(self, displays: dict[str, pg.Surface]):
        [card.render(displays) for card in self.cards]

# this class will allow me to encapsulate some static functionality that i want for a card
# this dict maps spell names to a parametric function that determines the wand path
# each card is [name: str, num_moves: int, optional: int]
# TODO: move these into a .json file
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
SPELL_DESC = load_json('./assets/cards/spell_desc.json')
SPELL_COLORS = load_json('./assets/cards/spell_colors.json')
SPELL_EFFECTS = load_json('./assets/cards/spell_effects.json')

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
        self.card_effect = SPELL_EFFECTS[spell]
    
    def update(self, topleft: tuple[int, int], dt: float):
        self.draw_rect.left, self.draw_rect.top = topleft

        self.t += dt
        if self.t > 1:
            self.t -= 1
        new_anchor = trace_wand_path(self.draw_rect, SPELL_WAND_PATHS[self.spell], self.t)
        self.sparks.update(dt, new_anchor)

    def click(self, mouse: tuple[int, int]) -> bool:
        if self.draw_rect.collidepoint(mouse):
            return True
        return False

    def scroll_card_face(self, mouse: tuple[int, int]):
        if self.draw_rect.collidepoint(mouse):
            self.current_side_up = (self.current_side_up + 1) % 2

    def render(self, displays: dict[str, pg.Surface]):
        displays['default'].blit(self.card_faces[self.current_side_up], self.draw_rect)
        if self.current_side_up == 0:
            self.sparks.render(displays['gaussian_blur'])

class HiddenHand:
    def __init__(self, menu, hand_size: int):
        self.card_designs = menu.card_collection
        self.color_theme = menu.white_theme
        self.cards = []
        self.update_hand(hand_size)
        self.card_width = self.card_designs['gryffindor_gold']['border'].get_width()
        self.card_height = self.card_designs['gryffindor_gold']['border'].get_height()

    def update_hand(self, hand_size: int):
        self.cards = [HiddenCard(self.card_designs, self.color_theme) for _ in range(hand_size)]

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