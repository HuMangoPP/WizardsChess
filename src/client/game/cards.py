import pygame as pg
import math

class Hand:
    def __init__(self, hand: list[str], card_designs: dict[str, dict[str, pg.Surface]], color_theme: str):
        self.cards = [Card(card_designs, card_name, color_theme) for card_name in hand]
        # a card is a struct specifying a unique id (for reference),
        # a sprite, a descriptions, and some additional data representing
        # card functionality, perhaps a target (which can be a chess piece),
        # a timer (the duration left for the card's effect), an effect key
        # (to keep track of what the effect is), etc...
        self.card_width = card_designs['gryffindor_gold']['border'].get_width()
        self.card_height = card_designs['gryffindor_gold']['border'].get_height()

    def update(self, events: list[pg.Event]):
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                for i in range(len(self.cards)):
                    card_rect = pg.Rect(0, self.card_height * i, self.card_width, self.card_height)
                    if card_rect.collidepoint(event.pos[0], event.pos[1]):
                        self.cards[i].scroll_card_face()


    def render(self, display: pg.Surface):
        [card.render(display, (0, self.card_height * i)) for i, card in enumerate(self.cards)]
# this class will allow me to encapsulate some static functionality that i want for a card
# this dict maps spell names to a parametric function that determines the wand path
CARD_EFFECTS = {
    'avada_kedavra': 'death', # literally dies
    'accio': 'move_close', # moves any of your pieces towards you 1 or 2 squares
    'depulso': 'move_away', # moves any of your pieces away from you 1 or 2 squares
    'confundus': 'move_random', # randomly moves like a king
    'deprimo': 'remove_square', # removes a square from being used for 2/3 moves, cannot be used on occupied squares
    'reducio': 'shrink', # can move but cannot capture
    'expelliarmus': '', #
    'disillusionment': 'invisible', # the chess piece becomes invisible for 2/3 moves
    'duro': 'cannot_move', # turns to stone, cannot move for 1 move
    'engorgio': 'grow', # counter spell for shrink
    'expecto_patronum': '', #
    
    'fiendfyre': 'capture_radius', # used on a piece and allows it to capture any enemy piece in a given radius, the attacking piece is removed afterwards
    'finite_incantatem': 'remove', # removes a random effect on a piece
    'flippendo': 'move_away', # similar to depulso, perhaps a stronger variant?
    'immobulus': 'cannot_move', # stronger variant of duro
    'petrificus_totalus': 'cannot_move', # strongest variant of duro
    'fumos': 'invisible', # weaker variant, not true invisibility
    'apparition': 'move_anywhere', # moves one of your pieces anywhere so long as the new square is not occupied
    'cruciatus': 'cannot_move', # piece cannot be moved for the rest of the game
    'firestorm': 'capture_radius', # similar to fiendfyre
    'glacius': 'cannot_move', #
    'impedimenta':'move_random', #
    'imperius': 'control', # allows player to control an enemy piece for 3 moves
    'locomotor': 'control', # weaker variant of imperius
    'legilimens': 'reveal', # permanently reveals one of opponent's cards (you know when they play the card)
    'revelio': 'reveal', # reveals one of opponent's cards
    'obscuro': 'invisible', # weaker
    'reparo': 'repair', # repairs broken grid tiles
    'prior_incantato': 'echo', # allows the user to use the last spell on the field (from either side)
    'protego': 'shield', # target cannot be captured for 2 rounds, attempts to capture are stopped and opponent uses a move
    'stupefy': 'break', # breaks a shield

}

SPELL_WAND_PATHS = {
    'avada_kedavra': lambda t : (-0.3 * (t - math.floor(0.5 + t)), 0.6 * (t - 0.5)),
    'accio': lambda t : (-0.3 * math.cos(math.pi * t), -0.25 * math.sin(math.pi * t)),
    'depulso': lambda t : (-0.3 * math.cos(math.pi * t), 0.25 * math.sin(math.pi * t)),
    'confundus': lambda t : (min(0.25, t) * math.sin(2 * math.pi * t), 
                             -0.5 / (0.5 + t) * math.sin(5 * math.pi / 6 * t) + 0.3),
    'deprimo': lambda t : ((t + 1) / 4 * max(min(math.sin(2 * math.pi * (t + 0.1)), 0.6), -0.6),
                           0.5 / (t + 1) * max(min(math.cos(2 * math.pi * (t + 0.1)), 0.6), -0.6)),
    'reducio': lambda t : (0.8 * (t - 0.5), -1.5 * abs(t - 0.5) + 0.3),
    'expelliarmus': lambda t : (-0.5 / (5 * t + 1.1) * math.sin(12 / 3.2 * math.pi * t),
                                -0.5 / (5 * t + 1.1) * math.cos(12 / 3.2 * math.pi * t)),
    'disillusionment': lambda t : (-0.5 / (2 * t + 1.1) * math.cos(12 / 3.2 * math.pi * t),
                                   -0.5 / (5 * t + 1.1) * math.sin(12 / 3.2 * math.pi * t)),
    
    'duro': lambda t : (-0.2 if t < 0.5 else 0.5 * math.sin(2 * math.pi * (t - 0.5)) - 0.2, 
                        -0.35 * math.cos(2 * math.pi * (t - 0.5))),
    'engorgio': lambda t : (-0.35 * math.sin(2 * math.pi * t) if (0.1 <= t and t <= 0.9) else -0.35 * math.sin(2 * math.pi * min(max(t, 0.1), 0.9)),
                            -0.35 * math.cos(2 * math.pi * t) if (0.1 <= t and t <= 0.9) else -abs(0.5 - t)),
    'fiendfyre': lambda t : (0.8 * (t - 0.5), t * (0.2 * round(math.sin(math.pi / 1.5 * t) - 0.4) + 0.1) if t <= 0.9 else 0.4)
    
}

def draw_wand_path(card: pg.Surface, path: callable):
    width, height = card.get_size()
    points = [path(t/20) for t in range(0, 20)]
    for i in range(len(points) - 1):
        pg.draw.line(card, (255, 255, 255), 
                     (width * (points[i][0] + 0.5), height * (points[i][1] + 0.5)),
                     (width * (points[i+1][0] + 0.5), height * (points[i+1][1] + 0.5)), 5)
    

class Card:
    def __init__(self, card_designs: dict[str, dict[str, pg.Surface]], spell: str, color_theme: str):
        card = card_designs[color_theme]['border'].copy()
        draw_wand_path(card, SPELL_WAND_PATHS[spell])
        text = card_designs[color_theme]['border'].copy()

        self.card_faces = [
            card, # i can potentially draw this using vfx procedurally
            text, # this one is drawn
        ]
        self.current_side_up = 0

        # status effects of the card
        self.card_effect = CARD_EFFECTS[spell]
    
    def scroll_card_face(self):
        self.current_side_up = (self.current_side_up + 1) % 2

    def render(self, display: pg.Surface, pos: tuple[int, int]):
        display.blit(self.card_faces[self.current_side_up], pos)

class HiddenHand:
    def __init__(self, hand_size: int, card_designs: dict[str, dict[str, pg.Surface]], color_theme: str):
        self.cards = [HiddenCard(card_designs, color_theme) for i in range(hand_size)]
        self.card_width = card_designs['gryffindor_gold']['border'].get_width()
        self.card_height = card_designs['gryffindor_gold']['border'].get_height()

    def render(self, display: pg.Surface):
        [card.render(display, (960-self.card_width, self.card_height * i)) for i, card in enumerate(self.cards)]

class HiddenCard:
    def __init__(self, card_designs: dict[str, pg.Surface], color_theme: str):
        self.card_face = card_designs[color_theme]['sleeve'].copy()
    
    def render(self, display: pg.Surface, pos: tuple[int, int]):
        display.blit(self.card_face, pos)