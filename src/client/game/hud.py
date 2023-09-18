import pygame as pg
import numpy as np


class TurnIndicator:
    def __init__(self, menu):
        self.menu = menu
        self._create_turn_tokens()
        self._setup_state()
    
    def _create_turn_tokens(self):
        width, height = self.menu.client.screen_size
        self.movement_tokens = {
            1: (
                np.full((3, 2), np.array([width - width / 10, height / 2])) +
                np.array([
                    [0, 1],
                    [-(3 / 4) ** (1 / 2), -1 / 2],
                    [(3 / 4) ** (1 / 2), -1 / 2],
                ]) * width / 20
            ),
            -1: (
                np.full((3, 2), np.array([width - width / 10, height / 2])) +
                np.array([
                    [0, -1],
                    [-(3 / 4) ** (1 / 2), 1 / 2],
                    [(3 / 4) ** (1 / 2), 1 / 2],
                ]) * width / 20
            )
        }
        self.spell_token_offset = np.array([0, width / 10])
    
        self.piece_icon = pg.image.load('./assets/ui/piece_icon.png').convert()
        self.piece_icon = pg.transform.scale(self.piece_icon, (width / 40, width / 20))
        self.piece_icon.set_colorkey((0,255,0))
        self.piece_icon_rect = self.piece_icon.get_rect()
        self.piece_icon_rect.center = np.array(self.menu.client.screen_size) * np.array([9 / 10, 1 / 2])

        self.spell_icon = pg.image.load('./assets/ui/spell_icon.png').convert()
        self.spell_icon = pg.transform.scale(self.spell_icon, (width / 50, width / 50))
        self.spell_icon.set_colorkey((0,255,0))
        self.spell_icon_rect = self.spell_icon.get_rect()

    def _setup_state(self):
        self.movement_index = 0
        self.spell_index = 0

    def update(self):
        if self.menu.phase == 0:
            if self.menu.my_turn:
                self.movement_index = 1
            else:
                self.movement_index = -1
        else:
            self.movement_index = 0

        if self.menu.my_turn:
            self.spell_index = 1
        else:
            self.spell_index = -1
        
        if self.menu.phase == 2:
            self.spell_index = 0

    def render(self, display: pg.Surface):
        if self.movement_index == 0:
            pg.draw.circle(
                display, 
                (255,255,255), 
                np.array(self.menu.client.screen_size) * np.array([9 / 10, 1 / 2]),
                self.menu.client.screen_size[0] / 20
            )
        else:
            pg.draw.polygon(
                display,
                (255,255,255),
                self.movement_tokens[self.movement_index]
            )
        display.blit(
            self.piece_icon,
            self.piece_icon_rect
        )
        
        if self.spell_index != 0:
            center = np.array(self.menu.client.screen_size) * np.array([9 / 10, 1 / 2]) + self.spell_token_offset * self.spell_index
            pg.draw.circle(
                display,
                (255,255,255),
                center,
                self.menu.client.screen_size[0] / 50
            )
            self.spell_icon_rect.center = center
            display.blit(
                self.spell_icon,
                self.spell_icon_rect
            )
        

class TooltipIndicator:
    def __init__(self, menu):
        self.menu = menu
        self.setup_tooltip()
    
    def setup_tooltip(self, text: str = ''):
        width, height = self.menu.client.screen_size
        if text:
            num_chars = len(text)
            chars_per_line = width / 3 / 6
            num_lines = int(np.ceil(num_chars / chars_per_line))
            self.tooltip_surf = pg.Surface((width // 3, num_lines * 10))
            self.menu.client.font.render(
                self.tooltip_surf,
                text,
                width // 6,
                num_lines * 5,
                (255,255,255),
                4,
                'center',
                box_width=width // 3
            )
            self.show_tooltip = True
        else:
            self.tooltip_surf = pg.Surface((10,10))
            self.show_tooltip = False
    
    def render(self, display: pg.Surface):
        if self.show_tooltip:
            width, height = self.menu.client.screen_size
            mx, my = pg.mouse.get_pos()
            rect = self.tooltip_surf.get_rect()
            if mx <= width / 2:
                rect.left = mx
                if my <= height / 2:
                    rect.top = my
                else:
                    rect.bottom = my
            else:
                rect.right = mx
                if my <= height / 2:
                    rect.top = my
                else:
                    rect.bottom = my

            display.blit(
                self.tooltip_surf,
                rect
            )
