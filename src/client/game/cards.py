import pygame as pg
import math

class Hand:
    def __init__(self, card_designs: dict[str, pg.Surface], color_theme: tuple[int, int, int]):
        self.cards = [Card(card_designs, 'avada_kedavra', color_theme)]
        # a card is a struct specifying a unique id (for reference),
        # a sprite, a descriptions, and some additional data representing
        # card functionality, perhaps a target (which can be a chess piece),
        # a timer (the duration left for the card's effect), an effect key
        # (to keep track of what the effect is), etc...

# this class will allow me to encapsulate some static functionality that i want for a card
# this dict maps spell names to a parametric function that determines the wand path
CARD_FUNCS = {
    'avada_kedavra': 'death'
}
SPELL_WAND_PATHS = {
    'avada_kedavra': lambda t : (-2 * (t - math.floor(0.5 + t)), 3 * t)
}
def draw_wand_path(card: pg.Surface, path: callable):
    t = 0
    dt = 0.05
    ...
class Card:
    def __init__(self, card_designs: dict[str, pg.Surface], spell: str, color_theme: tuple[int, int, int]):
        card = pg.Surface(card_designs['border'])
        draw_wand_path(card, SPELL_WAND_PATHS[self.spell])

        self.card_faces = [
            card, # i can potentially draw this using vfx procedurally
            card_designs['border'].copy(), # this one is drawn
            card_designs['sleeve'] # this one is drawn
        ]
        self.current_side_up = 0

        # status effects of the card
        self.card_func = CARD_FUNCS[self.spell]
    
    def scroll_card_face(self):
        self.current_side_up = (self.current_side_up + 1) % 3

    def render(self, display: pg.Surface):
        display.blit(self.card_faces[self.current_side_up], (0, 0))