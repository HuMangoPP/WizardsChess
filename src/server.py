from .game_state import *

class Server:
    def __init__(self):
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
        played_cards = self.hand_manager.commit_play()
        self.board_manager.resolve_casts(played_cards, 1)
        self.board_manager.commit_play()
        self.board_manager.resolve_casts(played_cards, 2)
        self.board_manager.resolve_debuffs()
