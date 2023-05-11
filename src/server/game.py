from server_state import BoardState

class Game:
    def __init__(self, id: str):
        self.id = id
        self.board_state = BoardState()
        self.ready = False
    
    def get_board_state(self):
        return self.board_state.get_fen_str()

    def get_hand_state(self):
        ...

    def make_move(self, move: list[int, int]):
        self.board_state.make_board_move(move)
    
    def connected(self):
        return self.ready