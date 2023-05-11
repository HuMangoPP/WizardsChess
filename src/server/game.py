from server_state import BoardState

class Game:
    def __init__(self, id: str):
        self.id = id
        self.board_state = BoardState()
        self.ready = False
    
    def get_board_state(self):
        return self.board_state.get_fen_str()

    def get_occupation(self, p_side: str):
        return list(self.board_state.white_occupied) if p_side == 'w' else list(self.board_state.black_occupied)

    def get_legal_moves(self, square: int):
        return list(self.board_state.pickup_piece(square))

    def get_hand_state(self):
        ...

    def make_move(self, move: list[int, int]):
        self.board_state.make_board_move(move)
    
    def is_ready(self):
        return self.ready