import pygame as pg
import numpy as np

from ..vfx.particles import Bolt
from ..util.asset_loader import load_json, load_spritesheet

class _Settings:
    CARD_BORDER = pg.image.load('./assets/cards/border2.png')
    CARD_SLEEVE = pg.image.load('./assets/cards/sleeve2.png')
    CARD_RECT = CARD_BORDER.get_rect()

    COIN_BORDER = pg.image.load('./assets/cards/coin_border.png')
    COIN_SLEEVE = pg.image.load('./assets/cards/coin_sleeve.png')
    COIN_RECT = COIN_BORDER.get_rect()

    def pg_setup():
        _Settings.CARD_BORDER.convert()
        _Settings.CARD_SLEEVE.convert()
        _Settings.COIN_BORDER.convert()
        _Settings.COIN_SLEEVE.convert()

        _Settings.CARD_BORDER = pg.transform.scale(
            _Settings.CARD_BORDER, 
            np.array(_Settings.CARD_BORDER.get_size()) * 2
        )
        _Settings.CARD_SLEEVE = pg.transform.scale(
            _Settings.CARD_SLEEVE, 
            np.array(_Settings.CARD_SLEEVE.get_size()) * 2
        )
        _Settings.COIN_BORDER = pg.transform.scale(
            _Settings.COIN_BORDER, 
            np.array(_Settings.COIN_BORDER.get_size()) * 2
        )
        _Settings.COIN_SLEEVE = pg.transform.scale(
            _Settings.COIN_SLEEVE, 
            np.array(_Settings.COIN_SLEEVE.get_size()) * 2
        )
        
        _Settings.CARD_RECT = _Settings.CARD_BORDER.get_rect()
        _Settings.COIN_RECT = _Settings.COIN_BORDER.get_rect()

        _Settings.COIN_BORDER.set_colorkey((0,255,0))
        _Settings.COIN_SLEEVE.set_colorkey((0,255,0))


class CardsRenderer:
    def __init__(self, menu):
        self.menu = menu
        _Settings.pg_setup()
        self._create_cards()

        self._init_hand_variables()
        self.clear_animation()
    
    def _init_hand_variables(self):
        self.card_rects = []
        self.pickup_card = -1

        self.my_coin_rects = []
        self.opponent_coin_rects = []
        self.revealed_coins = []
    
    def clear_animation(self):
        self.animating = False
        self.bolt = None

    def _create_cards(self):
        self.cards = {}
        self.card_colours = {}
        card_data = load_json('./assets/cards/card_data.json')

        for card_id, data in card_data.items():
            front = _Settings.CARD_BORDER.copy()
            self.menu.client.font.render(
                front,
                data['display_name'],
                _Settings.CARD_RECT.width / 2,
                _Settings.CARD_RECT.height / 5,
                data['colour'],
                4,
                style='center',
                box_width=_Settings.CARD_RECT.width * 4 / 5
            )
            pg.draw.lines(
                front,
                data['colour'],
                False,
                np.array(data['path']) * _Settings.CARD_RECT.width / 2 + _Settings.CARD_RECT.center
            )

            desc = _Settings.CARD_BORDER.copy()
            self.menu.client.font.render(
                desc,
                data['description'],
                _Settings.CARD_RECT.width / 2,
                _Settings.CARD_RECT.height / 2,
                data['colour'],
                4,
                style='center',
                box_width=_Settings.CARD_RECT.width * 3 / 4
            )

            back = _Settings.CARD_SLEEVE.copy()

            self.cards[card_id] = [front, desc, back]
            self.card_colours[card_id] = data['colour']
    
        self._create_coins(card_data)

    def _create_coins(self, card_data: dict):
        self.coins = {}
        for card_id, data in card_data.items():
            front = _Settings.COIN_BORDER.copy()
            self.menu.client.font.render(
                front,
                data['display_name'],
                _Settings.COIN_RECT.width / 2,
                _Settings.COIN_RECT.height / 2,
                data['colour'],
                4,
                style='center',
                box_width=_Settings.COIN_RECT.width * 4 / 5
            )
            pg.draw.lines(
                front,
                data['colour'],
                False,
                np.array(data['path']) * _Settings.COIN_RECT.width / 2 + _Settings.COIN_RECT.center
            )

            back = _Settings.COIN_SLEEVE.copy()

            self.coins[card_id] = [front, back]
        
    def _render_my_hand(self, display: pg.Surface):
        my_hand = [self.cards[card_id] for card_id in self.menu.my_hand]
        
        center_offset = (len(my_hand) - 1) / 2
        self.card_rects = []
        for i, card in enumerate(my_hand):
            x = i - center_offset
            x = x * _Settings.CARD_RECT.width
            y = self.menu.client.screen_size[1] - _Settings.CARD_RECT.height

            if self.pickup_card == i:
                y -= _Settings.CARD_RECT.height
            
            if self.menu.card_queue[i][0] != -1:
                y -= _Settings.CARD_RECT.height

            card_rect = card[0].get_rect()
            card_rect.centerx = x + self.menu.client.screen_size[0] / 2
            card_rect.centery = y
            self.card_rects.append(card_rect)

            flip_state = 0
            if self.pickup_card == i:
                flip_state = 1
            elif card_rect.collidepoint(pg.mouse.get_pos()):
                flip_state = 1
            display.blit(card[flip_state], card_rect)
    
    def _render_opponent_hand(self, display: pg.Surface):
        opponent_hand = [self.cards[card_id] for card_id in self.menu.opponent_hand]

        center_offset = (len(opponent_hand) - 1) / 2
        opponent_side_effects = [
            side_effects['name'] for side_effects in
            self.menu.opponent_side_effects
        ]
        flip_state = 0 if 'reveal' in opponent_side_effects else 2
        for i, card in enumerate(opponent_hand):
            x = i - center_offset
            x = x * _Settings.CARD_RECT.width
            y = _Settings.CARD_RECT.height

            card_rect = card[flip_state].get_rect()
            card_rect.centerx = x + self.menu.client.screen_size[0] / 2
            card_rect.centery = y

            if flip_state == 0 and card_rect.collidepoint(pg.mouse.get_pos()):
                flip_state = 1
            display.blit(card[flip_state], card_rect)
    
    def _render_my_coins(self, display: pg.Surface):
        center_offset = (len(self.menu.my_coins) - 1) / 2
        self.my_coin_rects = []
        for i, coin_data in enumerate(self.menu.my_coins):
            x = i - center_offset
            x = x * _Settings.COIN_RECT.width
            y = self.menu.client.screen_size[1] - _Settings.COIN_RECT.height - 2 * _Settings.CARD_RECT.height

            coin_surfs = self.coins[coin_data['card_id']]
            coin_rect = coin_surfs[0].get_rect()
            coin_rect.centerx = x + self.menu.client.screen_size[0] / 2
            coin_rect.centery = y
            self.my_coin_rects.append(coin_rect)

            display.blit(coin_surfs[0], coin_rect)

    def _render_opponent_coins(self, display: pg.Surface):
        if len(self.menu.opponent_coins) > len(self.revealed_coins):
            self.revealed_coins = (
                self.revealed_coins + 
                [False for _ in range(len(self.menu.opponent_coins) - len(self.revealed_coins))]
            )
        else:
            self.revealed_coins = self.revealed_coins[:len(self.menu.opponent_coins)]

        center_offset = (len(self.menu.opponent_coins) - 1) / 2
        self.opponent_coin_rects = []
        for i, coin_data in enumerate(self.menu.opponent_coins):
            x = i - center_offset
            x = x * _Settings.COIN_RECT.width
            y = _Settings.COIN_RECT.height + 2 * _Settings.CARD_RECT.height

            coin_surfs = self.coins[coin_data['card_id']]
            coin_rect = coin_surfs[0].get_rect()
            coin_rect.centerx = x + self.menu.client.screen_size[0] / 2
            coin_rect.centery = y
            self.opponent_coin_rects.append(coin_rect)

            if self.revealed_coins[i]:
                display.blit(coin_surfs[0], coin_rect)
            else:
                display.blit(coin_surfs[1], coin_rect)

    def render(self, display: pg.Surface):
        self._render_my_hand(display)
        self._render_opponent_hand(display)
        self._render_my_coins(display)
        self._render_opponent_coins(display)
        if self.bolt is not None:
            self.bolt.render(display)

    def animate_reveal_coins(self):
        if np.all(self.revealed_coins):
            return True
            
        indices = np.where(self.revealed_coins)[0]
        if indices.size > 0:
            self.revealed_coins[indices[-1] + 1] = True
        else:
            self.revealed_coins[0] = True
        
        return False
    
    def create_spell_animation(self, t: float):
        if len(self.menu.my_coins) != len(self.menu.my_dummy_coins):
            rank,file = self.menu.my_coins[0]['target']
            self.bolt = Bolt(
                np.array(self.my_coin_rects[0].center),
                np.array(self.menu.board_renderer.piece_rects[rank][file].center),
                self.card_colours[self.menu.my_coins[0]['card_id']],
                t
            )
        else:
            rank,file = self.menu.opponent_coins[0]['target']
            self.bolt = Bolt(
                np.array(self.opponent_coin_rects[0].center),
                np.array(self.menu.board_renderer.piece_rects[rank][file].center),
                self.card_colours[self.menu.opponent_coins[0]['card_id']],
                t
            )
        self.animating = True

    def animate_spell(self, dt: float):
        if self.bolt is not None:
            if self.bolt.update(dt) and self.animating:
                self.menu.my_coins = self.menu.my_dummy_coins
                self.menu.opponent_coins = self.menu.opponent_dummy_coins
                self.animating = False
                return True
        
        return False

