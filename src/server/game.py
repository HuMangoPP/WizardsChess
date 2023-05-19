from server_state import BoardState, HandState, FieldEffectsState

TURN_PHASES = ['main_phase', 'response_phase']

class Game:
    def __init__(self, id: str):
        self.id = id
        self.ffx_state = FieldEffectsState()
        self.board_state = BoardState(self.ffx_state)
        self.hand_state = HandState(self.ffx_state, self.board_state)

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
        if p_side == 'w':
            occupation = set([square for square in self.board_state.white_occupied
                              if 'control' not in set(self.ffx_state.get_field_effects(square))])
            occupation = occupation.union(set([square for square in self.board_state.black_occupied
                                               if 'control' in set(self.ffx_state.get_field_effects(square))]))
            return list(occupation)
        else:
            occupation = set([square for square in self.board_state.black_occupied
                              if 'control' not in set(self.ffx_state.get_field_effects(square))])
            occupation = occupation.union(set([square for square in self.board_state.white_occupied
                                               if 'control' in set(self.ffx_state.get_field_effects(square))]))
            return list(occupation)

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

    def get_displacements(self):
        return self.hand_state.queued_displacements

    def queue_cards(self, p_side: str, cards: list[tuple[str, int, int]]) -> list[tuple[int, int]]:
        return self.hand_state.queue_cards(p_side, cards)

    def cast_spell(self, p_side: str, card: str) -> list[int] | dict[str, list[int]]:
        res = self.hand_state.begin_cast(p_side, card)
        if isinstance(res, set):
            return list(res)
        else:
            return {
                'piece': list(res[0]), 
                'loc': list(res[1])
            }

    def end_phase(self):
        if self.current_phase == 1:
            self.hand_state.resolve_turn()
        self.current_phase = (self.current_phase + 1) % 2

    def is_ready(self):
        return self.ready