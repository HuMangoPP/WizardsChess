import numpy as np


class _Settings:
    PIECE_MAP = {
        'k': 1,
        'q': 2,
        'b': 3,
        'n': 4,
        'r': 5,
        'p': 6,
    }
    SIDE_MAP = lambda c : 1 if 'A' <= c <= 'Z' else -1

    PIECE_KEYS = np.array([
        'none',
        'king',
        'queen',
        'bishop',
        'knight',
        'rook',
        'pawn'
    ])

    PIECE_COLOURS = lambda board_state : board_state >= 0

    PIECE_OFFSETS = [
        [], 
        [[-1,-1],[0,-1],[1,-1],[-1,0],[1,0],[-1,1],[0,1],[1,1]],
        [[-1,-1],[0,-1],[1,-1],[-1,0],[1,0],[-1,1],[0,1],[1,1]],
        [[-1,-1],[1,-1],[-1,1],[1,1]],
        [[-1,-2],[1,-2],[-2,-1],[2,-1],[-2,1],[2,1],[-1,2],[1,2]],
        [[0,-1],[-1,0],[1,0],[0,1]],
        []
    ]
    PIECE_CAN_SLIDE = [False, False, True, True, False, True, False]

    def calculate_piece_move_indices(
        board_state: np.ndarray, 
        board_debuffs: np.ndarray,
        piece_index: int, 
        side_to_move: int, 
        en_passant: int,
        castling_privileges: list,
        captures_only: bool
    ):
        piece_move_indices = []

        piece = np.abs(board_state[piece_index])
        offsets = _Settings.PIECE_OFFSETS[piece]
        can_slide = _Settings.PIECE_CAN_SLIDE[piece]
        for offset in offsets:
            x_offset = offset[0] * side_to_move
            y_offset = offset[1] * side_to_move
            x, y = piece_index % 8, piece_index // 8
            if can_slide:
                slide_amt = 1
                while (
                    (0 <= x + x_offset * slide_amt and x + x_offset * slide_amt < 8) and
                    (0 <= y + y_offset * slide_amt and y + y_offset * slide_amt < 8)
                ):
                    index_offset = (x_offset + 8 * y_offset) * slide_amt
                    if board_debuffs[piece_index + index_offset].tile_has_debuff('destroy'):
                        break
                    elif board_state[piece_index + index_offset] * side_to_move == 0:
                        piece_move_indices.append(piece_index + index_offset)
                    elif board_state[piece_index + index_offset] * side_to_move < 0:
                        piece_move_indices.append(piece_index + index_offset)
                        break
                    else:
                        break
                    slide_amt += 1
            else:
                if 0 > x + x_offset or x + x_offset >= 8:
                    continue
                if 0 > y + y_offset or y + y_offset >= 8:
                    continue
                index_offset = x_offset + 8 * y_offset
                if (
                    board_state[piece_index + index_offset] * side_to_move <= 0 and
                    not board_debuffs[piece_index + index_offset].tile_has_debuff('destroy')
                ):
                    piece_move_indices.append(piece_index + index_offset)

        if piece == _Settings.PIECE_MAP['p']:
            # pawn movement
            x, y = piece_index % 8, piece_index // 8
            if not captures_only:
                index_offset = -side_to_move * 8
                if (
                    board_state[piece_index + index_offset] == 0 and
                    (0 <= y - side_to_move and y - side_to_move < 8) and
                    not board_debuffs[piece_index + index_offset].tile_has_debuff('destroy')
                ):
                    piece_move_indices.append(piece_index + index_offset)
                    if (
                        int((y - 3.5) / 2.5) == side_to_move and
                        board_state[piece_index + index_offset * 2] == 0 and
                        not board_debuffs[piece_index + index_offset].tile_has_debuff('destroy')
                    ):
                        piece_move_indices.append(piece_index + index_offset * 2)

            # pawn capture
            offsets = [[-1,-1], [1,-1]]
            for offset in offsets:
                x_offset = offset[0] * side_to_move
                y_offset = offset[1] * side_to_move
                if (
                    (0 <= x + x_offset and x + x_offset < 8) and
                    (0 <= y + y_offset and y + y_offset < 8)
                ):
                    index_offset = x_offset + 8 * y_offset
                    if board_debuffs[piece_index + index_offset].tile_has_debuff('destroy'):
                        continue
                    if board_state[piece_index + index_offset] * side_to_move < 0:
                        piece_move_indices.append(piece_index + index_offset)
                    elif en_passant == piece_index + index_offset:
                        piece_move_indices.append(piece_index + index_offset)

        if piece == _Settings.PIECE_MAP['k'] and not captures_only:
            opponent_checked_indices = np.hstack([
                _Settings.calculate_piece_move_indices(
                    board_state,
                    board_debuffs,
                    opponent_piece_index,
                    -side_to_move,
                    -1,
                    castling_privileges,
                    True
                )
                for opponent_piece_index in np.where(board_state * side_to_move < 0)[0]
            ])
            if ( # kingside castling
                castling_privileges[-side_to_move + 1] and
                board_state[piece_index + 1] == 0 and
                board_state[piece_index + 2] == 0 and 
                piece_index + 1 not in opponent_checked_indices and
                piece_index + 2 not in opponent_checked_indices and
                not board_debuffs[piece_index + 1].tile_has_debuff('destroy') and
                not board_debuffs[piece_index + 2].tile_has_debuff('destroy')
            ):
                piece_move_indices.append(piece_index + 2)
            
            if ( # queenside castling
                castling_privileges[-side_to_move + 2] and
                board_state[piece_index - 1] == 0 and
                board_state[piece_index - 2] == 0 and
                board_state[piece_index - 3] == 0 and 
                piece_index - 1 not in opponent_checked_indices and
                piece_index - 2 not in opponent_checked_indices and 
                not board_debuffs[piece_index - 1].tile_has_debuff('destroy') and
                not board_debuffs[piece_index - 2].tile_has_debuff('destroy') and
                not board_debuffs[piece_index - 3].tile_has_debuff('destroy')
            ):
                piece_move_indices.append(piece_index - 2)

        return np.array(piece_move_indices)

    def make_move_on_board(
        board_state: np.ndarray,
        board_debuffs: np.ndarray,
        piece_index: int,
        new_piece_index: int,
        side_to_move: int,
        en_passant: int,
        castling_privileges: list
    ):  
        new_board_state = board_state.copy()
        new_board_debuffs = np.array([debuff.copy() for debuff in board_debuffs])
        new_castling_privileges = castling_privileges.copy()
        
        piece = new_board_state[piece_index]
        new_board_state[new_piece_index] = piece
        new_board_state[piece_index] = 0

        new_board_debuffs[new_piece_index].copy_from(new_board_debuffs[piece_index])
        new_board_debuffs[piece_index].clear_debuffs()

        piece = np.abs(piece)
        if piece == _Settings.PIECE_MAP['p']: 
            # check if capture was en passant
            if new_piece_index == en_passant:
                new_board_state[en_passant + side_to_move * 8] = 0
                new_board_debuffs[en_passant + side_to_move * 8].clear_debuffs()

            # updating enpassant
            index_change = np.abs(new_piece_index - piece_index)
            if index_change == 16:
                new_en_passant = piece_index - side_to_move * 8
            else:
                new_en_passant = -1
        else:
            new_en_passant = -1
        
        if piece == _Settings.PIECE_MAP['k']:
            if side_to_move != 0:
                index_change = new_piece_index - piece_index
                if index_change == 2: # kingside castling
                    new_board_state[piece_index + 1] = new_board_state[piece_index + 3]
                    new_board_state[piece_index + 3] = 0

                    new_board_debuffs[piece_index + 1].copy_from(new_board_debuffs[piece_index + 3])
                    new_board_debuffs[piece_index + 3].clear_debuffs()
                elif index_change == -2: # queenside castling
                    new_board_state[piece_index - 1] = new_board_state[piece_index - 4]
                    new_board_state[piece_index - 4] = 0

                    new_board_debuffs[piece_index - 1].copy_from(new_board_debuffs[piece_index - 4])
                    new_board_debuffs[piece_index - 4].clear_debuffs()
            
            new_castling_privileges[-side_to_move + 1] = False
            new_castling_privileges[-side_to_move + 2] = False

        if piece == _Settings.PIECE_MAP['r']:
            if piece_index == 0:
                new_castling_privileges[3] = False
            elif piece_index == 7:
                new_castling_privileges[2] = False
            elif piece_index == 56:
                new_castling_privileges[1] = False
            elif piece_index == 63:
                new_castling_privileges[0] = False
        
        return new_board_state, new_board_debuffs, new_en_passant, new_castling_privileges

    def filter_out_illegal_moves(
        board_state: np.ndarray, 
        board_debuffs: np.ndarray,
        piece_index: int, 
        side_to_move: int, 
        en_passant: int,
        castling_privileges: list,
        piece_move_indices: np.ndarray
    ):
        mask = np.ones_like(piece_move_indices, np.bool_)
        for i, new_piece_index in enumerate(piece_move_indices):
            new_board_state, new_board_debuffs, new_en_passant, new_castling_privileges = _Settings.make_move_on_board(
                board_state,
                board_debuffs,
                piece_index,
                new_piece_index,
                side_to_move,
                en_passant,
                castling_privileges
            )
            king_index = np.where(new_board_state * side_to_move == 1)[0][0]
            opponent_checked_indices = np.hstack([
                _Settings.calculate_piece_move_indices(
                    new_board_state,
                    new_board_debuffs,
                    opponent_piece_index,
                    -side_to_move,
                    new_en_passant,
                    new_castling_privileges,
                    True
                )
                for opponent_piece_index in np.where(new_board_state * side_to_move < 0)[0]
            ])
            mask[i] = king_index not in opponent_checked_indices
        
        return piece_move_indices[mask]

    def make_move_on_board_spell(
        board_state: np.ndarray,
        board_debuffs: np.ndarray,
        piece_index: int,
        new_piece_index: int,
        castling_privileges: list
    ):
        new_board_state, new_board_debuffs, _, new_castling_privileges = _Settings.make_move_on_board(
            board_state,
            board_debuffs,
            piece_index,
            new_piece_index,
            0, -1,
            castling_privileges
        )

        return new_board_state, new_board_debuffs, new_castling_privileges

    def displace_spell_effect(
        board_state: np.ndarray,
        board_debuffs: np.ndarray,
        side_to_move: int,
        castling_privileges: list,
        target_index: int, 
        displace_type: str
    ):
        if 'forward' in displace_type:
            displace_strength = int(displace_type[-1])
            for i in range(displace_strength):
                new_piece_index = target_index - side_to_move * 8 * (i + 1)
                if (
                    new_piece_index < 0 or
                    new_piece_index >= 64 or
                    board_state[new_piece_index] != 0
                ):
                    return board_state, castling_privileges
            new_board_state, new_board_debuffs, new_castling_privileges = _Settings.make_move_on_board_spell(
                board_state,
                board_debuffs,
                target_index,
                target_index - side_to_move * 8 * displace_strength,
                castling_privileges
            )
        elif 'backward' in displace_type:
            displace_strength = int(displace_type[-1])
            for i in range(displace_strength):
                new_piece_index = target_index + side_to_move * 8 * (i + 1)
                if (
                    new_piece_index < 0 or
                    new_piece_index >= 64 or
                    board_state[new_piece_index] != 0
                ):
                    return board_state, castling_privileges
            new_board_state, new_board_debuffs, new_castling_privileges = _Settings.make_move_on_board_spell(
                board_state,
                board_debuffs,
                target_index,
                target_index + side_to_move * 8 * displace_strength,
                castling_privileges
            )
        elif 'random' in displace_type:
            displace_strength = int(displace_type[-1])
            moves = _Settings.calculate_n_steps_away(target_index, displace_strength)
            for move in moves:
                if board_state[move] != 0:
                    moves.remove(move)
            moves = list(moves)
            if len(moves) == 0:
                move = target_index
            else:
                move = np.random.choice(moves)
            new_board_state, new_board_debuffs, new_castling_privileges = _Settings.make_move_on_board_spell(
                board_state,
                board_debuffs,
                target_index,
                move,
                castling_privileges
            )
        elif 'anywhere' in displace_type:
            new_board_state, new_board_debuffs, new_castling_privileges = _Settings.make_move_on_board_spell(
                board_state,
                board_debuffs,
                target_index,
                target_index + 0,
                castling_privileges
            )
        
        return new_board_state, new_board_debuffs, new_castling_privileges
    
    def calculate_n_steps_away(target_index: int, n_steps: int) -> set[int]:
        moves = set([target_index])
        if n_steps == 0:
            return moves
        x, y = target_index % 8, target_index // 8
        possible_moves = [[-1,0],[1,0],[0,-1],[0,1]]
        moves = set()
        for possible_move in possible_moves:
            new_x = x + possible_move[0]
            new_y = y + possible_move[1]
            if 0 > new_x or new_x >= 8 or 0 > new_y or new_x >= 8:
                continue
            new_tile_index = new_x + new_y * 8
            moves = moves.union(_Settings.calculate_n_steps_away(new_tile_index, n_steps-1))
        return moves
        
        
class TileDebuffs:
    def __init__(self):
        self.debuffs = []
    
    def copy(self):
        new_debuffs = TileDebuffs()
        new_debuffs.debuffs = self.debuffs.copy()
        return new_debuffs

    def update_debuffs(self, debuff: str, debuff_length: int):
        if debuff_length < 0:
            self.debuffs.append(dict(debuffs_name=debuff, debuff_length=-1))
        else:
            self.debuffs.append(dict(debuff_name=debuff, debuff_length=debuff_length+1))
    
    def _get_tile_debuffs(self):
        return [debuff['debuff_name'] for debuff in self.debuffs]

    def tile_has_debuff(self, debuff: str):
        return debuff in self._get_tile_debuffs()

    def resolve_debuffs(self, board_state: np.ndarray, tile_index: int):
        destroy_tiles = []
        for debuff in self.debuffs:
            if 'death' in debuff['debuff_name']:
                destroy_tiles.append(tile_index)
            elif 'dangerous' in debuff['debuff_name']:
                debuff_strength = int(debuff['debuff_name'][-1])
                possible_tiles_to_destroy = _Settings.calculate_n_steps_away(tile_index, debuff_strength)
                possible_tiles_to_destroy.remove(tile_index)
                for possible_tile_to_destroy in possible_tiles_to_destroy:
                    if board_state[possible_tile_to_destroy] == 0:
                        possible_tiles_to_destroy.remove(possible_tile_to_destroy)
                possible_tiles_to_destroy = list(possible_tiles_to_destroy)
                if len(possible_tiles_to_destroy) > 0:
                    destroy_tiles.append(np.random.choice(possible_tiles_to_destroy))
        
        return destroy_tiles

    def clear_debuffs(self):
        self.debuffs = []

    def copy_from(self, debuff):
        self.debuffs = debuff.debuffs

    def end_round(self):
        for i, debuff in enumerate(self.debuffs):
            if debuff['debuff_length'] > 0:
                self.debuffs[i] = dict(
                    debuff_name=debuff['debuff_name'],
                    debuff_length=debuff['debuff_length']-1
                )
        
        self.debuffs = [debuff for debuff in self.debuffs if debuff['debuff_length'] == 0]


class BoardManager:
    def __init__(self):
        self.board_state = []
        self.castling_privileges = []
        self.side_to_move = 1
        self.en_passant = -1
        self._init_from_string()

        self.board_debuffs = np.full(64, TileDebuffs(), object)
    
        self.picked_piece_index = -1
        self.picked_piece_params = {}
        self.can_pickup_indices = []
        self.piece_move_indices = []
        self._calculate_can_pickup_indices()

    def _init_from_string(self, position: str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR 1 1111 -1'):
        """
        this function will initialize the board state given a custom string.
        the string is similar to fen notation but slightly different as it makes
        computation easier for me.

        the string consists of 4 parts:

        * a sequence of characters represent pieces. rows are separated by `/`. and
        numbers represent empty space

        * `1` denotes white to move, `-1` denotes black to move

        * a binary string which encodes the castling privileges in the order of KQkq

        * a number, which denote the square where an en passant capture can occur
        """

        board_state, side_to_move, castling_privileges, en_passant = position.split()

        self.board_state = np.zeros(64, np.int32)
        index = 0
        for c in board_state:
            if c == '/':
                pass
            elif c.isnumeric():
                index += int(c)
            else:
                self.board_state[index] = _Settings.PIECE_MAP[c.lower()] * _Settings.SIDE_MAP(c)
                index += 1

        self.side_to_move = int(side_to_move)

        self.castling_privileges = [bool(c) for c in castling_privileges]

        self.en_passant = en_passant

    def _calculate_piece_move_indices(self):
        """
        this function is called whenever a player initates a play.
        this function will calculate all of the possible indices the player
        can move the piece they have picked up
        """
        if self.picked_piece_index == -1:
            return
        self.piece_move_indices = _Settings.calculate_piece_move_indices(
            self.board_state,
            self.board_debuffs,
            self.picked_piece_index,
            self.side_to_move,
            self.en_passant,
            self.castling_privileges,
            False
        )
        self.piece_move_indices = _Settings.filter_out_illegal_moves(
            self.board_state,
            self.board_debuffs,
            self.picked_piece_index,
            self.side_to_move,
            self.en_passant,
            self.castling_privileges,
            self.piece_move_indices
        )

        if self.board_debuffs[self.picked_piece_index].tile_has_debuff('shrink'):
            self.piece_move_indices = self.piece_move_indices[self.board_state[self.piece_move_indices] != 0]

    def _calculate_can_pickup_indices(self):
        """
        this function is called at the start of a player turn.
        this function will calculate all of the indices which have
        a piece the player can pickup (and control)
        """

        # get pieces that are the right colour
        can_pickup_indices = self.board_state * self.side_to_move > 0

        # get tile debuffs
        control = np.where([debuff.tile_has_debuff('control') for debuff in self.board_debuffs])[0]
        stationary = np.where([debuff.tile_has_debuff('stationary') for debuff in self.board_debuffs])[0]

        # restrictions
        can_pickup_indices[control] = True
        can_pickup_indices[stationary] = False

        self.can_pickup_indices = np.where(can_pickup_indices)[0]

    def _validate_move(self):
        if self.board_debuffs[self.picked_piece_index].tile_has_debuff('displace'):
            return False
        
        self._calculate_piece_move_indices()
        return self.picked_piece_params['move_to_index'] in self.piece_move_indices

    def pickup_piece(self, board_index: int):
        """
        this funtion is called whenever a player picks up a piece from the board.
        there can be one of three results:

        * if the player picks a piece after already moving, the player rescinds the previous play
        and initiates the new play

        * if the piece picked is the one that is currently picked, the player also rescinds the play
        
        * if the piece is a new piece, then the player initiates the play
        """
        if board_index in self.can_pickup_indices:
            self.picked_piece_params = {}
            if board_index == self.picked_piece_index:
                self.picked_piece_params = {}
                self.picked_piece_index = -1
                self.piece_move_indices = []
            else:
                self.picked_piece_params = {}
                self.picked_piece_index = board_index
                self._calculate_piece_move_indices()
            return True
        return False

    def update_picked_piece_params(self, board_index: int):
        if 'move_to_index' in self.picked_piece_params:
            return
        
        if board_index not in self.piece_move_indices:
            return
        
        self.picked_piece_params['move_to_index'] = board_index
        self.piece_move_indices = []
        
    def commit_play(self):
        """
        this function is called when the player inputs the end turn command.
        this function will check if the appropriate conditions are met for
        the player to end their turn (they have made a move) and will commit the player.
        the board state will be updated as a result.
        """
        if self.picked_piece_index == -1:
            return
        
        if not self.picked_piece_params:
            return
        
        if self._validate_move():
            self.board_state, self.board_debuffs, self.en_passant, self.castling_privileges = _Settings.make_move_on_board(
                self.board_state,
                self.board_debuffs,
                self.picked_piece_index,
                self.picked_piece_params['move_to_index'],
                self.side_to_move,
                self.en_passant,
                self.castling_privileges
            )

        self.side_to_move *= -1
        self.picked_piece_index = -1
        self.picked_piece_params = {}
        self.piece_move_indices = []
        self._calculate_can_pickup_indices()

    def resolve_casts(self, played_cards: dict, speed: int):
        for _, played_card_params in played_cards.items():
            if played_card_params['speed'] != speed:
                continue
            
            target_index = played_card_params['target_index']
            debuffs = self.board_debuffs[target_index]
            new_debuffs = played_card_params['debuffs']
            debuff_length = played_card_params['debuff_length']

            if 'displace' in new_debuffs:
                self.board_state, self.board_debuffs, self.castling_privileges = _Settings.displace_spell_effect(
                    self.board_state,
                    self.board_debuffs,
                    self.side_to_move,
                    self.castling_privileges,
                    target_index,
                    new_debuffs.split(' ')[-1]
                )
                debuffs.update_debuffs(new_debuffs, 'displace')
            else:
                debuffs.update_debuffs(new_debuffs, debuff_length)

    def resolve_debuffs(self):
        destroy_tiles = np.hstack([
            debuff.resolve_debuffs(self.board_state, i) 
            for i, debuff in enumerate(self.board_debuffs)
        ]).astype(int)
        self.board_state[destroy_tiles] = 0
        [debuff.clear_debuffs() for debuff in self.board_debuffs]

        [debuff.end_round() for debuff in self.board_debuffs]

    def get_render_data(self):
        return (
            _Settings.PIECE_KEYS[np.abs(self.board_state)], 
            _Settings.PIECE_COLOURS(self.board_state),
            self.piece_move_indices
        )

