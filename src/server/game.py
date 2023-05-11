from server_state import BoardState, HandState, FieldEffectsState

class Game:
    def __init__(self, id: str):
        self.id = id
        self.ffx_state = FieldEffectsState()
        self.board_state = BoardState(self.ffx_state)
        self.hand_state = HandState(self.ffx_state)
        self.ready = False
    
    def get_board_state(self):
        return self.board_state.get_fen_str()

    def get_occupation(self, p_side: str):
        return list(self.board_state.white_occupied) if p_side == 'w' else list(self.board_state.black_occupied)

    def get_legal_moves(self, square: int):
        return list(self.board_state.pickup_piece(square))

    def get_hand_state(self, p_side: str):
        return self.hand_state.get_hands_data(p_side)

    def get_ffx_state(self):
        return self.ffx_state.get_entire_field()

    def make_move(self, move: list[int, int]):
        self.board_state.make_board_move(move)
    
    def play_card(self, play: list[str, str, int]):
        self.hand_state.make_card_play(play)

    def is_ready(self):
        return self.ready