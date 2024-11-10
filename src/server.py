from .game_state import *

class Server:
    def __init__(self):
        self.games : dict[str, GameInstance] = {}
    
    def validate_code(self, code: str, lobby_type: str):
        if lobby_type == 'create':
            ...
        else:
            ...
        self.games[code] = GameInstance()
        return True

    def hand_event(self, code: str, event_data: dict):
        self.games[code].hand_event(event_data)
    
    def board_event(self, code: str, board_index: int):
        self.games[code].board_event(board_index)

    def end_turn(self, code: str):
        return self.games[code].end_turn()
    
    def get_render_data(self, code: str):
        return dict(
            board=self.games[code].board_manager.get_render_data(),
            hand=self.games[code].hand_manager.get_render_data()
        )
