from .game_state import *

class Server:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.board_manager = BoardManager()
        self.hand_manager = HandManager()

    def hand_event(self, event_data: dict):
        self.hand_manager.pick_card(event_data)
        self.hand_manager.update_picked_card_params(event_data)  
    
    def board_event(self, board_index: int):
        if self.board_manager.pickup_piece(board_index):
            return
        self.board_manager.update_picked_piece_params(board_index)

    def end_turn(self):
        # commit cards
        played_cards = self.hand_manager.commit_play()

        # get animations
        animations = []

        # resolve quickcasts
        cast_spell_animations = self.board_manager.resolve_casts(played_cards, 1)
        for animation in cast_spell_animations:
            animation_type = animation[0]
            if animation_type == 'cast_spell':
                animations.append([*animation, -self.hand_manager.side_to_play])
            else:
                animations.append(animation)

        # move piece
        piece_move_animation = self.board_manager.commit_play()
        if piece_move_animation is not None:
            animations.append(piece_move_animation)

        # resolve slow casts
        cast_spell_animations = self.board_manager.resolve_casts(played_cards, 2)
        animations.extend([
            [*cast_spell_animation, -self.hand_manager.side_to_play] 
            for cast_spell_animation in cast_spell_animations
        ])

        # tile effects
        tile_effects = self.board_manager.resolve_debuffs()
        if tile_effects is not None:
            animations.append(tile_effects)
        return animations
