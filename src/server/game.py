import numpy as np

from game_state import GameState

class Game:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.game_state = GameState()
        
        self.connected = {
            1: False,
            -1: False
        }
    
    def request(self, req: dict) -> dict:
        if req['game_id'] != self.game_id:
            return {}
        
        return self.game_state.request(req)
