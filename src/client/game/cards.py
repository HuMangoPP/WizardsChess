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
        self.apparition = set()
        self.valid_targets = set()

    def update_hand(self, hand: list[str], queue: list[tuple[str, int]]):
        new_hand = [card for card in self.cards if card.spell in hand]
        [hand.remove(card.spell) for card in new_hand]
        [new_hand.append(Card(self.font, self.card_designs, spell, self.color_theme)) for spell in hand]
        self.cards = new_hand

        # a card in the queue is represented by [Card object, target square]
        self.queue = [card_play for card_play in self.queue if [card_play[0].spell, card_play[1], card_play[2]] in queue]

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
                        if isinstance(self.new_card_in_queue, list):
                            if target in self.apparition:
                                new_card_play = [self.new_card_in_queue[0], self.new_card_in_queue[1], target]
                                self.queue.append(new_card_play)
                                req = {
                                    'req_type': 'play_cards',
                                    'p_side': self.menu.p_side,
                                    'cards': [[card[0].spell, card[1], card[2]] for card in self.queue],
                                }
                            self.new_card_in_queue = None
                        elif self.new_card_in_queue.spell == 'apparition':
                            if target in self.valid_targets:
                                self.new_card_in_queue = [self.new_card_in_queue, target]
                            else:
                                self.new_card_in_queue = None
                        else:
                            if target in self.valid_targets:
                                new_card_play = [self.new_card_in_queue, target, -1]
                                self.queue.append(new_card_play)
                                req = {
                                    'req_type': 'play_cards',
                                    'p_side': self.menu.p_side,
                                    'cards': [[card[0].spell, card[1], card[2]] for card in self.queue],
                                }
                    if isinstance(self.new_card_in_queue, list):
                        self.menu.board.spell_targets = self.apparition
                    else:
                        self.new_card_in_queue = None
                        self.menu.board.spell_targets = set()
                        self.apparition = set()
                    self.valid_targets = set()
                    
                else:
                    # get the card in the hand that was clicked
                    card_queue = set([card_play[0] for card_play in self.queue])
                    to_queue = [card for card in self.cards if card.click(event.pos) and card not in card_queue]
                    if to_queue:
                        self.new_card_in_queue = to_queue[0]
                        req = {
                            'req_type': 'cast_spell',
                            'p_side': self.menu.p_side,
                            'card': self.new_card_in_queue.spell
                        }
                    # get the indices in queue that are to be returned to hand
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

SPELL_WAND_PATHS = load_json('./assets/cards/spell_paths.json')
SPELL_DESC = load_json('./assets/cards/spell_desc.json')
SPELL_COLORS = load_json('./assets/cards/spell_colors.json')

def draw_wand_path(card: pg.Surface, path: str):
    path = SPELL_WAND_PATHS[path]
    width, height = card.get_size()
    for i in range(len(path) - 1):
        pg.draw.line(card, (255, 255, 255), 
                     np.array([width/2, height/2]) + np.array([(width - 50) * path[i][0], (height-50) * path[i][1]]), 
                     np.array([width/2, height/2]) + np.array([(width - 50) * path[i+1][0], (height-50) * path[i+1][1]]), 5)

def render_card_name(font, card: pg.Surface, spell_name: str):
    width = card.get_width()
    text = spell_name.replace('_', ' ')
    font.render(card, text, width / 2, 40, (255, 255, 255), 10, 'center', box_width=width-20)

def trace_wand_path(card_rect: pg.Rect, path: str, t: int):
    anchor = np.array(SPELL_WAND_PATHS[path][t])
    width, height = card_rect.size
    return np.array(card_rect.center) + np.array([(width - 50), (height - 50)]) * anchor

def render_card_desc(font, card: pg.Surface, spell_name: str):
    font.render(card, SPELL_DESC[spell_name], 35, 50, (255, 255, 255), 10, box_width=card.get_width()-70)

class Card:
    def __init__(self, font, card_designs: dict[str, dict[str, pg.Surface]], spell: str, color_theme: str):
        card = card_designs[color_theme]['border'].copy()
        draw_wand_path(card, spell)
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
    
    def update(self, topleft: tuple[int, int], dt: float):
        self.draw_rect.left, self.draw_rect.top = topleft

        self.t += dt * 60
        if self.t >= len(SPELL_WAND_PATHS[self.spell]):
            self.t = 0
        new_anchor = trace_wand_path(self.draw_rect, self.spell, int(self.t))
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