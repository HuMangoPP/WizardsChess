from server_state import BoardState, HandState, FieldEffectsState

TURN_PHASES = ['main_phase', 'response_phase']

class Game:
    def __init__(self, id: str):
        self.id = id
        self.ffx_state = FieldEffectsState()
        self.board_state = BoardState(self.ffx_state)
        self.hand_state = HandState(self.ffx_state)

        self.current_phase = 0
        self.phase_fulfilled = 0

        self.ready = False
    
    def get_turn_phase(self, p_side: str):
        go_p_side = 'w' if self.board_state.move == 0 else 'b'
        match self.current_phase:
            case 0:
                return {
                    'phase': self.current_phase,
                    'can_go': p_side == go_p_side
                }
            case 1:
                return {
                    'phase': self.current_phase,
                    'can_go': p_side != go_p_side
                }
            case 2:
                return {
                    'phase': self.current_phase,
                    'can_go': False
                }        

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

    def get_queued_move(self):
        return self.board_state.queued_move

    def queue_move(self, move: tuple[int, int]):
        self.board_state.queue_move(move)

    def queue_cards(self, p_side: str, cards: list[str]):
        self.hand_state.queue_cards(p_side, cards)

    def end_phase(self):
        if self.current_phase == 1:
            if self.board_state.make_board_move():
                self.hand_state.make_card_plays()
        self.current_phase = (self.current_phase + 1) % 2

    def is_ready(self):
        return self.ready