import pygame as pg
import numpy as np

from ..util.transitions import transition_in, transition_out, TRANSITION_TIME
# from ..game.cards import Hand, HiddenHand, trace_wand_path, SPELL_COLORS, SPELL_WAND_PATHS

# from ..vfx.particles import Sparks

DEFAULT_DISPLAY = 'default'
EFFECTS_DISPLAY = 'gaussian_blur'
OVERLAY_DISPLAY = 'black_alpha'


def lerp(v1: np.ndarray, v2: np.ndarray, t: float):
    return (v2 - v1) * t + v1


class Menu:
    def __init__(self, client):
        self.client = client
        self.goto : str = None
    
    def _on_transition(self):
        # 0 -> no transition
        # 1 -> transition out
        # 2 -> black screen
        # 3 -> transition in
        self.transition_phase = 2
        self.transition_time = 0

    def on_load(self):
        self._on_transition()
    
    def update(self, events: list[pg.Event], dt: float):
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
        self.client.displays[DEFAULT_DISPLAY].fill((20, 26, 51))

        displays_to_render = [DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        return displays_to_render
        
    def render_overlay(self):
        if self.transition_phase == 1: 
            transition_out(self.client.displays[OVERLAY_DISPLAY], self.transition_time)
        elif self.transition_phase == 2:
            self.client.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
        elif self.transition_phase == 3:
            transition_in(self.client.displays[OVERLAY_DISPLAY], self.transition_time)


class StartMenu(Menu):
    def __init__(self, client):
        # init Menu
        super().__init__(client)
        self._create_buttons()
        self._create_num_pad()
        
        # override
        self.goto = 'wait'

    def _create_buttons(self):
        # TODO: put these into file and load them instead?
        btn_size = np.array(self.client.screen_size) * np.array([1 / 3, 1 / 8])
        self.create_game_btn = pg.Rect(0, 0, *btn_size)
        self.create_game_btn.center = np.array(self.client.screen_size) * np.array([1 / 4, 1 / 2])
        self.join_game_btn = pg.Rect(0, 0, *btn_size)
        self.join_game_btn.center = np.array(self.client.screen_size) * np.array([3 / 4, 1 / 2])

        self.create_game_colour = np.array([0,0,150])
        self.create_game_hover_colour = np.array([0,0,255])
        self.join_game_colour = np.array([0,150,0])
        self.join_game_hover_colour = np.array([0,255,0])

        self.create_game_blend = 0
        self.join_game_blend = 0
    
    def _create_num_pad(self):
        self.show_num_pad = False
        self.num_pad_rect = pg.Rect(
            0, 0, 
            *np.array(self.client.screen_size) / 2
        )
        self.num_pad_rect.center = np.array(self.client.screen_size) / 2

        rect_centers = np.array([
            [0,2],
            [-1,-1],
            [0,-1],
            [1,-1],
            [-1,0],
            [0,0],
            [1,0],
            [-1,1],
            [0,1],
            [1,1]
        ])
        self.num_rects = []
        for center in rect_centers:
            rect = pg.Rect(
                0, 0, *np.array(self.client.screen_size) / 12
            )
            rect.center = center * np.array(self.client.screen_size) / 12 + np.array(self.client.screen_size) / 2
            self.num_rects.append(rect)
        
        self.num_pad_value = ''

    def update(self, events: list[pg.Event], dt: float):
        if not self.show_num_pad:
            for event in events:
                if event.type == pg.MOUSEBUTTONDOWN:
                    if self.create_game_btn.collidepoint(event.pos):
                        self.client.create_new_network()
                        self.transition_phase = 1
                        self.transition_time = 0
                        self.goto = 'wait'
                    if self.join_game_btn.collidepoint(event.pos):
                        self.show_num_pad = True

            mpos = pg.mouse.get_pos()
            if self.create_game_btn.collidepoint(mpos):
                self.create_game_blend = np.minimum(
                    self.create_game_blend + 5 * dt,
                    1.0
                )
            else:
                self.create_game_blend = np.maximum(
                    self.create_game_blend - 5 * dt,
                    0.0
                )
            
            if self.join_game_btn.collidepoint(mpos):
                self.join_game_blend = np.minimum(
                    self.join_game_blend + 5 * dt,
                    1.0
                )
            else:
                self.join_game_blend = np.maximum(
                    self.join_game_blend - 5 * dt,
                    0.0
                )
        else:
            for event in events:
                if event.type == pg.MOUSEBUTTONDOWN:
                    for i, num_rect in enumerate(self.num_rects):
                        if num_rect.collidepoint(event.pos):
                            self.num_pad_value = f'{self.num_pad_value}{i}'
                
                if event.type == pg.KEYDOWN:
                    self.client.create_new_network(game_id=int(self.num_pad_value))
                    self.transition_phase = 1
                    self.transition_time = 0
                    self.goto = 'wait'

        return super().update(events, dt)

    def render(self) -> list[str]:
        displays_to_render = super().render()
        self.client.font.render(
            self.client.displays[DEFAULT_DISPLAY], 
            'Wizards Chess', 
            self.client.screen_size[0] / 2, 
            100, 
            (255, 255, 255), 
            50, 
            style='center'
        )

        if self.show_num_pad:
            pg.draw.rect(
                self.client.displays[DEFAULT_DISPLAY],
                (0,0,0),
                self.num_pad_rect
            )
            self.client.font.render(
                self.client.displays[DEFAULT_DISPLAY],
                self.num_pad_value,
                self.num_pad_rect.left + 50,
                self.num_pad_rect.top + 50,
                (255,255,255),
                20,
                style='left'
            )
            for i, num_rect in enumerate(self.num_rects):
                pg.draw.rect(
                    self.client.displays[DEFAULT_DISPLAY],
                    (50,50,50),
                    num_rect
                )
                self.client.font.render(
                    self.client.displays[DEFAULT_DISPLAY],
                    f'{i}',
                    num_rect.centerx,
                    num_rect.centery,
                    (255,255,255),
                    20,
                    style='center'
                )
        else:
            pg.draw.rect(
                self.client.displays[DEFAULT_DISPLAY],
                lerp(
                    self.create_game_colour,
                    self.create_game_hover_colour,
                    self.create_game_blend
                ),
                self.create_game_btn
            )
            self.client.font.render(
                self.client.displays[DEFAULT_DISPLAY],
                'Create Game',
                self.create_game_btn.centerx,
                self.create_game_btn.centery,
                (255,255,255),
                20,
                style='center'
            )

            pg.draw.rect(
                self.client.displays[DEFAULT_DISPLAY],
                lerp(
                    self.join_game_colour,
                    self.join_game_hover_colour,
                    self.join_game_blend
                ),
                self.join_game_btn
            )
            self.client.font.render(
                self.client.displays[DEFAULT_DISPLAY],
                'Join Game',
                self.join_game_btn.centerx,
                self.join_game_btn.centery,
                (255,255,255),
                20,
                style='center'
            )


        super().render_overlay()
        
        return displays_to_render


class WaitingRoom(Menu):
    def __init__(self, client):
        # init Menu
        super().__init__(client)
        
        # override
        self.goto = 'game'

    def on_load(self):
        super().on_load()
        if self.client.net.game_id == -1:
            self.goto = 'start'
            self.transition_phase = 1

    def update(self, events: list[pg.Event], dt: float):
        if self.transition_phase == 0:
            try:
                res = self.client.send_req({})
                if not res:
                    self.goto = 'start'
                    self.transition_phase = 1
                else:
                    if res['status'] == 'success':
                        self.goto = 'game'
                        self.transition_phase = 1
                        
            except Exception as e:
                self.goto = 'start'
                self.transition_phase = 1
        
        return super().update(events, dt)

    def render(self) -> list[str]:
        displays_to_render = super().render()

        self.client.font.render(
            self.client.displays[DEFAULT_DISPLAY], 
            'Waiting for game to start...', 
            self.client.screen_size[0] / 2, 
            self.client.screen_size[1] / 2 - 100, 
            (255, 255, 255), 
            30, 
            style='center', 
            box_width=self.client.screen_size[0] - 200
        )
        
        self.client.font.render(
            self.client.displays[DEFAULT_DISPLAY], 
            f'you are player {self.client.net.side}',
            self.client.screen_size[0] / 2, 
            self.client.screen_size[1] / 2, 
            (255, 255, 255), 
            30, 
            style='center'
        )
    
        self.client.font.render(
            self.client.displays[DEFAULT_DISPLAY],
            f'Use game id {self.client.net.game_id}',
            self.client.screen_size[0] / 2,
            self.client.screen_size[1] / 2 + 200,
            (255, 255, 255),
            30,
            style='center',
            box_width=self.client.screen_size[0] - 100
        )

        super().render_overlay()

        return displays_to_render


from ..game.chess import BoardRenderer
from ..game.cards import CardsRenderer


class GameMenu(Menu):
    def __init__(self, client):
        super().__init__(client)
        self._setup_variables()

        self.goto = 'start'

        self.board_renderer = BoardRenderer(self)
        self.cards_renderer = CardsRenderer(self)

        # # import game
        # self.width, self.height = client.res
        # self.displays = client.displays
        # self.font = client.font
        # self.clock = client.clock
        # self.client = client
        
        # # assets
        # self.piece_collection = client.piece_collection
        # self.card_collection = client.card_collection

        # # transition handler
        # self.goto = 'start'

        # # chess board
        # self.white_theme = 'gryffindor_red'
        # self.black_theme = 'slytherin_green'

        # #
        # self.current_phase = 0
        # self.can_go = False
        # self.card_animation = None
        # self.card_animation_time = 0
        # self.card_animation_sparks = Sparks((0, 0), (50, 50, 50))

    def _setup_variables(self):
        # variables
        self.my_turn = False
        self.phase = 0
        self.winner = None
        self.current_animation = None
        self.animation_timer = 0
        self.animation_wait = 1

        # render
        self.theme = 'gryffindor_red'
        self.other_theme = 'gryffindor_gold'
        self.phase_msgs = [
            'Initial Phase',
            'Reaction Phase',
            'Resolve Phase',
        ]

    def _get_board_state(self, use_dummy: bool = False):
        req = {
            'method': 'get',
            'endpoint': 'board'
        }
        res = self.client.send_req(req)
        if use_dummy:
            self.dummy_board_state = np.array(res['board_state']).reshape(8,8)
        else:
            self.board_state = np.array(res['board_state']).reshape(8,8)
            self.dummy_board_state = np.array(res['board_state']).reshape(8,8)

        self.moveable_effects = res['moveable_effects']
        self.static_effects = res['static_effects']
        self.my_side_effects = res['my_side_effects']
        self.opponent_side_effects = res['opponent_side_effects']

        self.moveable_pieces = np.full((8,8), False)
        self.possible_moves = np.full((8,8), False)

    def _get_hands(self, use_dummy: bool = False):
        req = {
            'method': 'get',
            'endpoint': 'hand'
        }
        res = self.client.send_req(req)
        self.my_hand = np.array(res['my_hand'])
        self.opponent_hand = np.array(res['opponent_hand'])
        self.card_queue = np.full((self.my_hand.size, 2), -1)

        if use_dummy:
            self.my_dummy_coins = res['my_coins']
            self.opponent_dummy_coins = res['opponent_coins']
        else:
            self.my_coins = res['my_coins']
            self.opponent_coins = res['opponent_coins']
            self.my_dummy_coins = res['my_coins']
            self.opponent_dummy_coins = res['opponent_coins']

    def _get_end_turn(self):
        req = {
            'method': 'get',
            'endpoint': 'end_turn'
        }
        res = self.client.send_req(req)
        if res['status'] == 'success':
            self.current_animation = res['animation']
            return True
        return False

    def on_load(self):
        super().on_load()

        self._get_board_state()
        self._get_hands()

    def update(self, events: list[pg.Event], dt: float):
        # send requests
        if self.current_animation is None:
        
            try:
                req = {
                    'method': 'get',
                    'endpoint': 'my_turn'
                }
                res = self.client.send_req(req)
                if 'winner' in res:
                    self.winner = res['winner']
                elif self.my_turn != res['my_turn'] or self.phase != res['phase']:
                    # new phase/turn
                    self.my_turn = res['my_turn']
                    self.phase = res['phase']

                    self._get_board_state()
                    self._get_hands()

                    if self.phase == 0 and self.my_turn:
                        req = {
                            'method': 'get',
                            'endpoint': 'moveable_pieces'
                        }
                        res = self.client.send_req(req)
                        self.moveable_pieces = np.array(res['moveable_pieces']).reshape(8,8).astype(bool)
                    
                    if self.phase == 2:
                        self.current_animation = 'reveal_coins'
            
                # user input
                for event in events:
                    if event.type == pg.MOUSEMOTION:
                        if (
                            self.board_renderer.board_rect.collidepoint(event.pos) and
                            self.board_renderer.holding[0] == -1
                        ):
                            tilesize = self.board_renderer.board_rect.width // 8
                            file, rank = (np.array(event.pos) - self.board_renderer.board_rect.topleft) // tilesize
                            if self.moveable_pieces[rank,file]:
                                self.board_renderer.hovering = [rank, file]
                        else:
                            self.board_renderer.hovering = [-1,-1]
                    
                    if event.type == pg.MOUSEBUTTONUP:
                        if self.board_renderer.board_rect.collidepoint(event.pos):
                            tilesize = self.board_renderer.board_rect.width // 8
                            file, rank = (np.array(event.pos) - self.board_renderer.board_rect.topleft) // tilesize
                            
                            if self.cards_renderer.pickup_card != -1:
                                req = {
                                    'method': 'post',
                                    'endpoint': 'queue_card',
                                    'params': {
                                        'card_index': self.cards_renderer.pickup_card,
                                        'rank': int(rank),
                                        'file': int(file),
                                    }
                                }
                                res = self.client.send_req(req)
                                self.card_queue = np.array(res['card_queue']).reshape(-1,2)
                                self.my_hand = np.array(res['my_hand'])
                                self.cards_renderer.pickup_card = -1

                                self.my_side_effects = res['my_side_effects']
                                self.opponent_side_effects = res['opponent_side_effects']

                            elif self.moveable_pieces[rank,file] and self.board_renderer.holding[0] == -1:
                                self.board_renderer.holding = [rank, file]
                                req = {
                                    'method': 'post',
                                    'endpoint': 'pickup_piece',
                                    'params': {
                                        'rank': int(rank),
                                        'file': int(file),
                                    }
                                }
                                res = self.client.send_req(req)
                                self.possible_moves = np.array(res['possible_moves']).reshape(8,8).astype(bool)
                            
                            elif self.board_renderer.holding[0] != -1 and self.possible_moves[rank,file]:
                                req = {
                                    'method': 'post',
                                    'endpoint': 'lock_in_move',
                                    'params': {
                                        'rank': int(rank),
                                        'file': int(file)
                                    }
                                }
                                self.client.send_req(req)
                                self.board_renderer.holding = [-1,-1]
                                self.moveable_pieces = np.full((8,8), False)
                                self.possible_moves = np.full((8,8), False)
                            
                            else:
                                self.board_renderer.holding = [-1,-1]
                                self.possible_moves = np.full((8,8), False)
                        
                        else:
                            self.board_renderer.holding = [-1,-1]
                            self.possible_moves = np.full((8,8), False)
                            self.cards_renderer.pickup_card = -1
                        
                        for i, card_rect in enumerate(self.cards_renderer.card_rects):
                            if card_rect.collidepoint(event.pos) and self.card_queue[i][0] == -1:
                                self.cards_renderer.pickup_card = i

                    if event.type == pg.KEYUP:
                        if event.key == pg.K_RETURN:
                            req = {
                                'method': 'post',
                                'endpoint': 'lock_in',
                                'params': {}
                            }
                            self.client.send_req(req)

            except (KeyError, TypeError):
                return {
                    'exit': True
                }
            except Exception as e:
                print('Exception in GameMenu.update()')
                print(e)
        
        else:
            self.animation_timer += dt
            if self.animation_timer > self.animation_wait:
                self.create_next_animation()
            self.animate(dt)

        return super().update(events, dt)

    def animate(self, dt: float):
        if self.current_animation == 'fast_spells':
            if self.cards_renderer.animate_spell(dt):
                self.board_renderer.create_board_move_animation(self.animation_wait / 2)
            self.board_renderer.animate_board_move(dt)
        elif self.current_animation == 'board_move':
            self.board_renderer.animate_board_move(dt)
        elif self.current_animation == 'slow_spells':
            self.cards_renderer.animate_spell(dt)
        elif self.current_animation == 'field_effects':
            self.board_renderer.animate_death(dt)

    def create_next_animation(self):
        if self.current_animation == 'reveal_coins':
            self._get_hands()

            if self.cards_renderer.animate_reveal_coins():
                self.current_animation = 'fast_spells'
        
        else:
            if not self._get_end_turn():
                return
            
            if self.current_animation == 'fast_spells':
                self.board_renderer.clear_animation()
                self.cards_renderer.clear_animation()

                self._get_board_state(use_dummy=True)
                self._get_hands(use_dummy=True)

                self.cards_renderer.create_spell_animation(self.animation_wait / 2)
            elif self.current_animation == 'board_move':
                self.board_renderer.clear_animation()
                self.cards_renderer.clear_animation()

                self._get_board_state(use_dummy=True)

                self.board_renderer.create_board_move_animation(self.animation_wait / 2)
            elif self.current_animation == 'slow_spells':
                self.board_renderer.clear_animation()
                self.cards_renderer.clear_animation()

                self._get_hands(use_dummy=True)

                self.cards_renderer.create_spell_animation(self.animation_wait / 2)
            elif self.current_animation == 'field_effects':
                self.board_renderer.clear_animation()
                self.cards_renderer.clear_animation()

                self._get_board_state(use_dummy=True)

                self.board_renderer.create_death_animation(self.animation_wait / 2)
        self.animation_timer = 0

    def render(self) -> list[str]:
        displays_to_render = super().render()

        self.client.displays[EFFECTS_DISPLAY].fill((0, 0, 0))

        self.board_renderer.render(self.client.displays[DEFAULT_DISPLAY])

        self.cards_renderer.render(self.client.displays[DEFAULT_DISPLAY])

        if self.winner is None:
            self.client.font.render(
                self.client.displays[DEFAULT_DISPLAY], 
                'Your move' if self.my_turn else 'Opponents move', 
                self.client.screen_size[0] / 2, 
                self.client.screen_size[1] / 5, 
                (255, 255, 255), 
                30, 
                style='center', 
                box_width=self.client.screen_size[0] - 100
            )
            self.client.font.render(
                self.client.displays[DEFAULT_DISPLAY], 
                self.phase_msgs[self.phase], 
                self.client.screen_size[0] / 2, 
                self.client.screen_size[1] / 4, 
                (255, 255, 255), 
                30, 
                style='center', 
                box_width=self.client.screen_size[0] - 100
            )
        else:
            if self.winner == 1:
                self.client.font.render(
                    self.client.displays[DEFAULT_DISPLAY], 
                    'You Win', 
                    self.client.screen_size[0] / 2, 
                    self.client.screen_size[1] / 5, 
                    (255, 255, 255), 
                    30, 
                    style='center', 
                    box_width=self.client.screen_size[0] - 100
                )
            elif self.winner == -1:
                self.client.font.render(
                    self.client.displays[DEFAULT_DISPLAY], 
                    'You Lose', 
                    self.client.screen_size[0] / 2, 
                    self.client.screen_size[1] / 5, 
                    (255, 255, 255), 
                    30, 
                    style='center', 
                    box_width=self.client.screen_size[0] - 100
                )
            else:
                self.client.font.render(
                    self.client.displays[DEFAULT_DISPLAY], 
                    'Tie', 
                    self.client.screen_size[0] / 2, 
                    self.client.screen_size[1] / 5, 
                    (255, 255, 255), 
                    30, 
                    style='center', 
                    box_width=self.client.screen_size[0] - 100
                )

        super().render_overlay()
        
        displays_to_render.insert(1, EFFECTS_DISPLAY)
        return displays_to_render
  