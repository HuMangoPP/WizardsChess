#!/usr/bin/env python
import numpy as np
import json

DEFAULT_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


class Piece:
    EMPTY = 0
    KING, QUEEN, BISHOP, KNIGHT, ROOK, PAWN = np.arange(1, 7)

    PIECE_MAP = {
        'K': 1,
        'Q': 2,
        'B': 3,
        'N': 4,
        'R': 5,
        'P': 6,

        'k': -1,
        'q': -2,
        'b': -3,
        'n': -4,
        'r': -5,
        'p': -6,
    }

    OFFSETS = {
        1: np.array([
            [-1,-1],
            [0,-1],
            [1,-1],
            [-1,0],
            [1,0],
            [-1,1],
            [0,1],
            [1,1]
        ]),
        4: np.array([
            [-2,-1],
            [-1,-2],
            [1,-2],
            [2,-1],
            [2,1],
            [1,2],
            [-1,2],
            [-2,1]
        ]),
    }

    SLIDE = {
        2: np.array([
            [-1,-1],
            [0,-1],
            [1,-1],
            [-1,0],
            [1,0],
            [-1,1],
            [0,1],
            [1,1]
        ]),
        3: np.array([
            [-1,-1],
            [1,-1],
            [1,1],
            [-1,1]
        ]),
        5: np.array([
            [0,-1],
            [1,0],
            [0,1],
            [-1,0]
        ]),
    }

    PAWN_OFFSET = {
        6: np.array([
            [-1,0]
        ]),
        -6: np.array([
            [1,0]
        ]),
    }

    PAWN_CAPTURE = {
        6: np.array([
            [-1,1],
            [-1,-1]
        ]),
        -6: np.array([
            [1,-1],
            [1,1]
        ]),
    }
   

class BoardManager:
    def __init__(self, effects_manager, fen: str = DEFAULT_FEN):
        self._load_board_state(fen)
        self._setup_variables()
        self._get_attacked_squares(effects_manager)
        self._clear_input()
    
    def __repr__(self):
        return f"""BoardManager instance:
Board State:
{self.board_state}
To Move: {self.side}
Castling Privileges: {self.castling_priv}
En Passant: {self.en_passant}
Full Moves: {self.full_moves}
White Attacking:
{self.white_attacking}
Black Attacking:
{self.black_attacking}
Inputs: 
{np.column_stack([self.input_ranks, self.input_files])}"""

    ### interal use init ###
    def _setup_variables(self):
        # winner
        self.winner = None

        # ritual chains
        self.move_chains = {
            1: np.array([], np.int32),
            -1: np.array([], np.int32)
        }

    def _load_board_state(self, fen: str):
        # split fen string into its components
        (board_state, 
         side, 
         castling_priv, 
         en_passant, 
         full_moves, 
         _) = fen.split()

        self.side = 1 if side == 'w' else -1

        self.castling_priv = {
            1: [
                True if 'K' in castling_priv else False, 
                True if 'Q' in castling_priv else False
            ],
            -1: [
                True if 'k' in castling_priv else False, 
                True if 'q' in castling_priv else False
            ],
        }

        if en_passant == '-':
            self.en_passant = np.full(2, -1)
        else:
            file = ord(en_passant[0]) - ord('a')
            rank = 8 - int(en_passant[0])
            self.en_passant = np.array([rank,file])

        self.full_moves = int(full_moves)

        # read the board from fen string
        self.board_state = []
        for c in board_state:
            if c == '/':
                continue
            elif '0' <= c and c <= '9':
                self.board_state += [Piece.EMPTY for _ in range(int(c))]
            else:
                self.board_state.append(Piece.PIECE_MAP[c])
        self.board_state = np.array(self.board_state).reshape(8,8)

        self.removed_tiles = np.full((8,8), 0)

    def _get_attacked_squares(self, effects_manager):
        self.white_attacking = _get_attacked_squares(1, self, effects_manager)
        self.black_attacking = _get_attacked_squares(-1, self, effects_manager)

    def _clear_input(self):
        self.input_ranks = np.full(2, -1, np.int32)
        self.input_files = np.full(2, -1, np.int32)
        self.possible_moves = np.full((8,8), 0)

    ### user request ###
    def get_moveable_pieces(self, effects_manager, **kwargs):
        self.moveable_pieces = np.full((8,8), 0)
        for rank, row in enumerate(self.board_state):
            for file, tile in enumerate(row):
                effects = [moveable_effect.name for moveable_effect in effects_manager.moveable_effects[rank][file]]
                if 'cannot_move' not in effects:
                    if 'control' in effects:
                        self.moveable_pieces[rank,file] = tile * self.side < 0
                    else:
                        self.moveable_pieces[rank,file] = tile * self.side > 0

    def get_possible_moves(self, effects_manager, **kwargs):
        self.possible_moves = _get_possible_moves(
            self.input_ranks[0], 
            self.input_files[0], 
            self, 
            effects_manager
        )
    
    def pickup_piece(self, rank: int, file: int, effects_manager, **kwargs):
        if self.moveable_pieces[rank,file]:
            self.input_ranks[0] = rank
            self.input_files[0] = file
            self.get_possible_moves(effects_manager)
            return True
        return False

    def lock_in_move(self, rank: int, file: int, **kwargs):
        if self.possible_moves[rank,file]:
            self.input_ranks[1] = rank
            self.input_files[1] = file
            return True
        return False
    
    def make_move(self, effects_manager):
        # ensure move is valid
        if not self.move_locked_in():
            return False
        
        rank1, rank2 = self.input_ranks
        file1, file2 = self.input_files

        self.get_possible_moves(effects_manager)
        if self.possible_moves[rank2,file2]:
            
            # update enpassant
            # check if pawn moved two squares
            if (np.abs(self.board_state[rank1,file1]) == Piece.PAWN and 
                np.abs(rank1 - rank2) == 2 
            ):
                self.en_passant = np.array([(rank1 + rank2) // 2, file1], np.int32)
            else:
                self.en_passant = np.full(2, -1)
            
            # update castling privileges as applicable
            # castling
            if np.abs(self.board_state[rank1,file1]) == Piece.KING: # king initiate castle
                # move rook
                if file2 - file1 == 2:
                    # kingside castle
                    files = [file2 - 1, file2 + 1]
                    self.board_state[self.input_ranks, files] = self.board_state[self.input_ranks[::-1], files[::-1]]
                elif file2 - file1 == -2:
                    # queenside castle
                    files = [file2 - 2, file2 + 1]
                    self.board_state[self.input_ranks, files] = self.board_state[self.input_ranks[::-1], files[::-1]]
                
                # no castling
                self.castling_priv[self.side] = [False, False]

            # rook movement prevents castling
            if np.abs(self.board_state[rank1,file1]) == Piece.ROOK:
                if rank1 == 7 and self.side == 1:
                    if file1 == 7:
                        # white kingside castle
                        self.castling_priv[0][0] = False
                    elif file1 == 0:
                        # white queenside castle
                        self.castling_priv[0][1] = False
                elif rank1 == 0 and self.side == -1:
                    if file1 == 7:
                        # black kingside castle
                        self.castling_priv[1][0] = False
                    elif file1 == 0:
                        # black queenside castle
                        self.castling_priv[1][1] = False
            
            # rook capture prevents castling
            if np.abs(self.board_state[rank2,file2]) == Piece.ROOK:
                if rank2 == 7:
                    if file2 == 7:
                        # white kingside castle
                        self.castling_priv[0][0] = False
                    elif file2 == 0:
                        # white queenside castle
                        self.castling_priv[0][1] = False
                elif rank2 == 0:
                    if file2 == 7:
                        # white kingside castle
                        self.castling_priv[1][0] = False
                    elif file2 == 0:
                        # white queenside castle
                        self.castling_priv[1][1] = False

            # movement chain
            if (self.move_chains[self.side].size > 0 and 
                np.all(self.move_chains[self.side][-1] == np.array([rank1,file1]))
            ):
                self.move_chains[self.side] = np.array([
                    *self.move_chains[self.side],
                    [rank2,file2]
                ])
            else:
                self.move_chains[self.side] = np.column_stack([
                    self.input_ranks, self.input_files
                ])
            
            # enpassant capture
            if (self.board_state[rank1,file1] == Piece.PAWN and
                np.abs(file2 - file1) == 1
            ):
                self.board_state[rank1,file2] = Piece.EMPTY

            # move piece
            self.board_state[rank2,file2] = self.board_state[rank1,file1]
            self.board_state[rank1,file1] = Piece.EMPTY
        
        # clear input
        self._clear_input()

        return True

    def check_movement_chain(self, hands_manager):
        loop = np.where(np.all(self.move_chains[self.side][:-1] == self.move_chains[self.side][-1], axis=1))[0]
        if loop.size > 0:
            loop_length = self.move_chains[self.side].shape[0] - loop[0] - 1
            hands_manager.summon_card(self.side, loop_length)
            self.move_chains[self.side] = self.move_chains[self.side][-1:]
            return True
        return False
    
    ### external use ###
    def move_locked_in(self):
        return self.input_ranks[0] != -1

    def spell_move(self, old_tile: np.ndarray, new_tile: np.ndarray, slide: bool = False):
        if slide:
            rank1,file1 = old_tile
            rank2,file2 = new_tile
            rank_dir = 1 if rank2 >= rank1 else -1
            file_dir = 1 if file2 >= file2 else -1

            ranks = np.arange(rank1,rank2,rank_dir) + rank_dir
            files = np.arange(file1,file2,file_dir) + file_dir
            if ranks.size == 0:
                ranks = np.full_like(files, rank1)
            elif files.size == 0:
                files = np.full_like(ranks, file1)
            
            if np.all(self.board_state[ranks,files] == Piece.EMPTY):
                self.board_state[tuple(new_tile)] = self.board_state[tuple(old_tile)]
                self.board_state[tuple(old_tile)] = Piece.EMPTY
        else:
            if self.board_state[tuple(new_tile)] == Piece.EMPTY:
                self.board_state[tuple(new_tile)] = self.board_state[tuple(old_tile)]
                self.board_state[tuple(old_tile)] = Piece.EMPTY

    def remove_tile(self, rank: int, file: int):
        if not np.logical_and(self.removed_tiles[:,0] == rank, self.removed_tiles[:,1] == file):
            self.removed_tiles = np.array([
                *self.removed_tiles,
                [rank, file]
            ])
    
    def repair_tile(self, rank: int, file: int):
        mask = np.invert(np.logical_and(self.removed_tiles[:,0] == rank, self.removed_tiles[:,1] == file))
        self.removed_tiles = self.removed_tiles[mask]

    def end_turn(self, effects_manager):
        if not np.any(self.board_state == 1):
            self.winner = -1
        if not np.any(self.board_state == -1):
            if self.winner is None:
                self.winner = 1
            else:
                self.winner = 0
        
        if self.winner is None:
            self.side *= -1
            self.full_moves += 1
            self._get_attacked_squares(effects_manager)


def _get_possible_moves(rank: int, file: int, board_manager: BoardManager, effects_manager):
    board_state = board_manager.board_state
    castling_priv = board_manager.castling_priv
    side = board_manager.side
    en_passant = board_manager.en_passant

    ranks = []
    files = []

    effects = [moveable_effect.name for moveable_effect in effects_manager.moveable_effects[rank][file]]
    is_shrunk = 'shrink' in effects

    piece = board_state[rank, file]
    if piece > 0:
        opponent_attacking = board_manager.black_attacking
    else:
        opponent_attacking = board_manager.white_attacking

    # single offset
    for offset in Piece.OFFSETS.get(abs(piece), []):
        new_tile = np.array([rank, file]) + offset
        if (
            np.all(np.logical_and(0 <= new_tile, new_tile < 8))
        ):
            if (
                (board_state[new_tile[0], new_tile[1]] * side > 0) or
                (board_state[new_tile[0], new_tile[1]] * side < 0 and is_shrunk)
            ):
                continue
            ranks.append(new_tile[0])
            files.append(new_tile[1])
    
    # sliding offsets
    for offset in Piece.SLIDE.get(abs(piece), []):
        new_tile = np.array([rank, file]) + offset
        while np.all(np.logical_and(0 <= new_tile, new_tile < 8)):
            if board_state[new_tile[0], new_tile[1]] != Piece.EMPTY:
                if board_state[new_tile[0], new_tile[1]] * side < 0 and not is_shrunk:
                    ranks.append(new_tile[0])
                    files.append(new_tile[1])
                break
            ranks.append(new_tile[0])
            files.append(new_tile[1])
            new_tile = new_tile + offset
    
    # pawn move
    if piece in Piece.PAWN_OFFSET:
        offset = Piece.PAWN_OFFSET[piece][0]
        new_tile = np.array([rank, file]) + offset
        # single move
        if (
            np.all(np.logical_and(0 <= new_tile, new_tile < 8)) and
            board_state[new_tile[0], new_tile[1]] * side == Piece.EMPTY
        ):
            ranks.append(new_tile[0])
            files.append(new_tile[1])

            # double move
            new_tile = new_tile + offset
            if (
                (piece > 0 and rank == 6) and
                board_state[new_tile[0], new_tile[1]] == Piece.EMPTY
            ):
                ranks.append(new_tile[0])
                files.append(new_tile[1])

            if (
                (piece < 0 and rank == 1) and
                board_state[new_tile[0], new_tile[1]] * side == Piece.EMPTY
            ):
                ranks.append(new_tile[0])
                files.append(new_tile[1])

    # pawn captures
    for offset in Piece.PAWN_CAPTURE.get(piece, []):
        new_tile = np.array([rank, file]) + offset
        if (
            np.all(np.logical_and(0 <= new_tile, new_tile < 8)) and 
            (board_state[new_tile[0], new_tile[1]] * side < 0 or
             np.all(new_tile == en_passant)) and 
            not is_shrunk
        ):
            ranks.append(new_tile[0])
            files.append(new_tile[1])
    
    # castling
    if np.abs(piece) == Piece.KING:
        if (
            castling_priv[side][0] and 
            np.all([board_state[rank, file + i] == Piece.EMPTY for i in [1,2]]) and
            np.all([opponent_attacking[rank, file + i] == 0 for i in [0,1,2]])
        ):
            ranks.append(rank)
            files.append(file + 2)
        if (
            castling_priv[side][1] and 
            np.all([board_state[rank, file - i] == Piece.EMPTY for i in [1,2,3]]) and
            np.all([opponent_attacking[rank, file - i] == 0 for i in [0,1,2]])
        ):
            ranks.append(rank)
            files.append(file - 2)

    possible_moves = np.full((8,8), 0)
    possible_moves[ranks,files] = 1
    return possible_moves


def _get_attacked_squares(side: int, board_manager: BoardManager, effects_manager):
    board_state = board_manager.board_state

    ranks = []
    files = []

    for rank, row in enumerate(board_state):
        for file, piece in enumerate(row):
            effects = set([moveable_effect.name for moveable_effect in effects_manager.moveable_effects[rank][file]])
            # opponent piece that player cannot control
            if piece * side <= 0 and 'control' not in effects:
                continue
            
            # player piece that cannot move, be controlled, or capture
            if piece * side > 0 and len(effects.intersection(set(['cannot_move', 'control', 'shrink']))) > 0:
                continue
            
            # single offset
            for offset in Piece.OFFSETS.get(abs(piece), []):
                new_tile = np.array([rank, file]) + offset
                if np.all(np.logical_and(0 <= new_tile, new_tile < 8)):
                    ranks.append(new_tile[0])
                    files.append(new_tile[1])
            
            # sliding offsets
            for offset in Piece.SLIDE.get(abs(piece), []):
                new_tile = np.array([rank, file]) + offset
                while np.all(np.logical_and(0 <= new_tile, new_tile < 8)):
                    ranks.append(new_tile[0])
                    files.append(new_tile[1])
                    if board_state[new_tile[0], new_tile[1]] != Piece.EMPTY:
                        break
                    new_tile = new_tile + offset
            
            # pawn captures
            for offset in Piece.PAWN_CAPTURE.get(piece, []):
                new_tile = np.array([rank, file]) + offset
                if np.all(np.logical_and(0 <= new_tile, new_tile < 8)):
                    ranks.append(new_tile[0])
                    files.append(new_tile[1])

    attacked_squares = np.full((8, 8), 0)
    attacked_squares[ranks, files] = 1   
    return attacked_squares
         

class Effect:
    def __init__(self, effect_data: dict):
        self.name = effect_data['name']
        self.description = effect_data.get('description', 'No description')
        self.duration = effect_data.get('duration', 3)
    
    def to_json(self):
        return {
            'name': self.name,
            'description': self.description,
            'duration': self.duration
        }


MOVE_SPELL_OFFSETS = {
    'forward': np.array([0,-1]),
    'back': np.array([0,1]),
    'random': np.array([
        [-1,-1],
        [0,-1],
        [1,-1],
        [-1,0],
        [1,0],
        [-1,1],
        [0,1],
        [1,1]
    ])
}

DIRECTIONS = np.array([
    [0,-1],
    [-1,0],
    [1,0],
    [0,1],
])


class EffectsManager:
    def __init__(self):
        self._clear_state()
        self._clear_queue()
    
    def __repr__(self):
        printable_moveable = '\n'.join([
            f'{row}' for row in self.moveable_effects
        ])

        printable_static = '\n'.join([
            f'{row}' for row in self.moveable_effects
        ])
        return f"""EffectsManager instance:
Moveable Effects:
{printable_moveable}
Static Effects:
{printable_static}
Queued Fast Spells: {self.queued_fast_effects}
Queued Slow Spells: {self.queued_slow_effects}"""
    
    ### interal use init ###
    def _clear_state(self):
        self.moveable_effects = [
            [[] for _ in range(8)]
            for _ in range(8)
        ]
        self.static_effects = [
            [[] for _ in range(8)]
            for _ in range(8)
        ]

        self.side_effects = {
            1: [],
            -1: [],
        }

    def _clear_queue(self):
        self.queued_fast_effects = []
        self.queued_slow_effects = []

    def _check_durations(self):
        for rank, (moveable_row, static_row) in enumerate(zip(self.moveable_effects, self.static_effects)):
            for file, (moveable_effects, static_effects) in enumerate(zip(moveable_row, static_row)):
                self.moveable_effects[rank][file] = [
                    moveable_effect for moveable_effect in moveable_effects 
                    if moveable_effect.duration != 0
                ]
                self.static_effects[rank][file] = [
                    static_effect for static_effect in static_effects
                    if static_effect.duration != 0
                ]
        
        for side, side_effects in self.side_effects.items():
            for side_effect in side_effects:
                side_effect.duration -= 1
            self.side_effects[side] = [
                side_effect for side_effect in side_effects
                if side_effect.duration != 0
            ]

    # external use ###
    def queue_effects(self, fast: list, slow: list):
        self.queued_fast_effects = fast + self.queued_fast_effects
        self.queued_slow_effects = slow + self.queued_slow_effects

    def inflict_side_effect(self, side: int, effect_data: dict):
        self.side_effects[side].append(Effect(effect_data))

    def resolve_fast_effects(self, board_manager: BoardManager, hands_manager):
        if len(self.queued_fast_effects) == 0:
            return False
        
        fast_effect = self.queued_fast_effects[0]
        effect_side = fast_effect['side']
        effect_id = fast_effect['effect_id'].split('@')
        rank, file = fast_effect['target']

        # effect_id is split along the @, the element after the @ denotes the level
        # of the effect
        if len(effect_id) == 2:
            strength = int(effect_id[1])
        
        # next split the effect along the underscore
        # the first element is a core effect and the second is like a suffix
        effect_id = effect_id[0].split('_')

        # movement spells
        if effect_id[0] == 'move':
            offsets = MOVE_SPELL_OFFSETS[effect_id[1]]
            # move forward or back
            if effect_id[1] in ['forward', 'back']:
                offset = offsets * effect_side
                new_tiles = np.column_stack([
                    np.full(strength, rank, np.int32),
                    np.full(strength, file, np.int32)
                ]) + np.column_stack([
                    np.arange(1, strength + 1) * offset[0],
                    np.arange(1, strength + 1) * offset[1]
                ])
                new_tiles = new_tiles[::-1]

                strength_index = 0
                while strength_index < strength:
                    if (np.all(board_manager.board_state[new_tiles[strength_index:, 0], new_tiles[strength_index:, 1]] == Piece.EMPTY) and 
                        np.all(np.logical_and(0 <= new_tiles[strength_index:], new_tiles[strength_index:] < 8))
                    ):
                        break
                    strength_index += 1
                if strength_index < strength:
                    new_tile = new_tiles[strength_index]
                else:
                    new_tile = np.array([rank, file])
                
                board_manager.spell_move(np.array([rank, file]), new_tile)

            # move random
            elif effect_id[1] in ['random']:
                # move random or anywhere
                # anywhere is not supported right now since that needs additional input
                offsets = np.random.shuffle(offsets)
                for offset in offsets:
                    new_tile = np.array([rank, file]) + offset
                    if (board_manager.board_state[new_tile[0], new_tile[1]] == Piece.EMPTY and
                        np.all(np.logical_and(0 <= new_tile, new_tile < 8))
                    ):
                        break
                
                board_manager.spell_move(np.array([rank, file]), new_tile)

        # remove spells
        elif effect_id[0] == 'remove':
            board_manager.remove_tile(rank, file)
        
        # repair spells
        elif effect_id[0] == 'repair':
            board_manager.repair_tile(rank, file)
        
        # shield spells
        elif effect_id[0] == 'shield':
            self.moveable_effects[rank][file].append(Effect({
                'name': effect_id[0],
            }))
        
        # update hands and queued effects
        if board_manager.side > 0:
            # black then white
            if len(hands_manager.black_coins) > 0:
                hands_manager.black_coins = hands_manager.black_coins[1:]
            else:
                hands_manager.white_coins = hands_manager.white_coins[1:]
        else:
            # white then black
            if len(hands_manager.white_coins) > 0:
                hands_manager.white_coins = hands_manager.white_coins[1:]
            else:
                hands_manager.black_coins = hands_manager.black_coins[1:]
        self.queued_fast_effects = self.queued_fast_effects[1:]
    
        return True

    def resolve_slow_effects(self, board_manager: BoardManager, hands_manager):
        if len(self.queued_slow_effects) == 0:
            return False
        
        slow_effect = self.queued_slow_effects[0]
        # get the caster, effect_id, and target
        effect_id = slow_effect['effect_id'].split('@')
        rank, file = slow_effect['target']

        # there is no core/suffix encoding with slow spells (since they have such varied effects)
        if effect_id[0] in ['cannot_move', 'control']:
            """
                Name: cannot_move
                Description: pieces cannot be moved by the player
                Duration: 1-3, inf
            """

            """
                Name: control
                Description: pieces cannot be moved by the player but 
                can be moved by the opponent
                Duration: 1-3
            """

            self.moveable_effects[rank][file].append(
                Effect({
                    'name': effect_id[0],
                    'duration': int(effect_id[1])
                })
            )

        elif effect_id[0] in ['shrink', 'grow']:
            """
                Name: shrink
                Description: piece cannot capture
                Duration: 3
            """

            """
                Name: grow
                Description: piece will randomly capture an adjacent piece (if applicable)
                Duration: 3
            """

            self.moveable_effects[rank][file].append(
                Effect({
                    'name': effect_id[0]
                })
            )
        
        elif effect_id[0] in ['area_attack', 'death']:
            """
                Name: area_attack
                Description: at the end of the turn, a random piece within 
                a range of the target will be randomly captured
                Duration: end of turn
            """

            """
                Name: death
                Description: at the end of the turn, the piece
                in the target tile will be captured
                Duration: end of turn
            """

            self.static_effects[rank][file].append(
                Effect({
                    'name': '@'.join(effect_id),
                    'duration': 1
                })
            )
        
        elif effect_id[0] == 'break':
            """
                Effect Undecided
            """
            ...
        
        # update hands and queued effects
        if board_manager.side > 0:
            # black then white
            if len(hands_manager.black_coins) > 0:
                hands_manager.black_coins = hands_manager.black_coins[1:]
            else:
                hands_manager.white_coins = hands_manager.white_coins[1:]
        else:
            # white then black
            if len(hands_manager.white_coins) > 0:
                hands_manager.white_coins = hands_manager.white_coins[1:]
            else:
                hands_manager.black_coins = hands_manager.black_coins[1:]
        self.queued_slow_effects = self.queued_slow_effects[1:]
    
        return True

    def resolve_field_effects(self, board_manager: BoardManager):
        captures = np.full((8,8), False)
        for rank, (moveable_row, static_row) in enumerate(zip(self.moveable_effects, self.static_effects)):
            for file, (moveable_effects, static_effects) in enumerate(zip(moveable_row, static_row)):
                for static_effect in static_effects:
                    if static_effect.name == 'death':
                        captures[rank, file] = True
                    
                    elif static_effect.name[:11] == 'area_attack':
                        radius = int(static_effect.name[12:])
                        offsets = np.array([[0,0]])
                        for _ in np.arange(radius):
                            for offset in offsets:
                                for direction in DIRECTIONS:
                                    new_offset = offset + direction
                                    if np.any(np.logical_and(offsets[:,0] == new_offset[0], offsets[:,1] == new_offset[1])):
                                        continue
                                    offsets = np.array([*offsets, new_offset])
                        possible_targets = np.array([])
                        start = np.array([rank, file])
                        for offset in offsets:
                            tile = start + offset
                            if (np.all(np.logical_and(0 <= tile, tile < 8)) and
                                board_manager.board_state[tile[0], tile[1]] != Piece.EMPTY
                            ):
                                possible_targets = np.array([*possible_targets, tile])
                        
                        target = np.random.choice(possible_targets)
                        captures[target[0], target[1]] = True
                    static_effect.duration -= 1
        
                for moveable_effect in moveable_effects:
                    if moveable_effect.name == 'shield':
                        captures[rank, file] = True
                        moveable_effect.duration = 0
                    moveable_effect.duration -= 1

        board_manager.board_state[captures] = Piece.EMPTY

    def get_field_effects_json(self):
        moveable_field_effects = [
            [[] for _ in range(8)]
            for _ in range(8)
        ]
        static_field_effects = [
            [[] for _ in range(8)]
            for _ in range(8)
        ]
        for rank, (moveable_row, static_row) in enumerate(zip(self.moveable_effects, self.static_effects)):
            for file, (moveable_effects, static_effects) in enumerate(zip(moveable_row, static_row)):
                moveable_field_effects[rank][file] = [
                    moveable_effect.to_json() for moveable_effect in moveable_effects
                ]
                static_field_effects[rank][file] = [
                    static_effect.to_json() for static_effect in static_effects
                ]
        
        return moveable_field_effects, static_field_effects

    def get_side_effects_json(self):
        return {
            side: [side_effect.to_json() for side_effect in self.side_effects[side]]
            for side in [1,-1]
        }

    def end_turn(self):
        self._check_durations()
        self._clear_queue()


BASE_RATES_BY_LEVEL = np.array([
    80, 10, 5, 4, 1
])

CUMUL_RATES_BY_LEVEL = np.array([
    50, 10, 5, 3, 2
])


class HandsManager:
    def __init__(self):
        self._load_data()
        self._clear_hands()
        self._clear_queues()
        self._clear_coins()
    
    def __repr__(self):
        return f"""HandsManager instance:
White Hand: {self.white_hand}
White Queue: {self.white_queue}
Black Hand: {self.black_hand}
Black Queue: {self.black_queue}"""
    
    ### internal use and init ###
    def _load_data(self):
        with open('./assets/cards/card_data.json', 'r') as f:
            self.card_data = json.load(f)
        with open('./assets/cards/effect_data.json', 'r') as f:
            self.effect_data = json.load(f)

    def _clear_hands(self):
        self.white_hand = np.array(['avada_kedavra']) # card id
        self.black_hand = np.array(['cruciatus', 'imperius'])
    
    def _clear_queues(self):
        self.white_queue = np.full((self.white_hand.size, 2), -1, np.int32)
        self.black_queue = np.full((self.black_hand.size, 2), -1, np.int32)

    def _clear_coins(self):
        self.white_coins = []
        self.black_coins = []

    ### external use ###
    def summon_card(self, side: int, chain_length: int):
        # get rarity
        new_rates = BASE_RATES_BY_LEVEL + CUMUL_RATES_BY_LEVEL * chain_length
        new_rates = new_rates[::-1]
        rates = []
        for new_rate in new_rates:
            sum = int(np.sum(rates))
            rates.append(min(new_rate, 100 - sum))
        rates = np.array(rates, np.float32) / 100
        rng = np.random.rand()
        rarity = -1
        while rng > 0:
            rarity += 1
            rng -= rates[rarity]
        rarity = 5 - rarity

        # get cards in that rarity level
        cards = []
        for card_id, card_data in self.card_data.items():
            if card_data['rarity'] == rarity:
                cards.append(card_id)

        if side > 0:
            self.white_hand = np.array([
                *self.white_hand,
                np.random.choice(cards)
            ])
        else:
            self.black_hand = np.array([
                *self.black_hand,
                np.random.choice(cards)
            ])

    def end_turn(self):
        self._clear_queues()
        self._clear_coins()

    ### user request ###
    def queue_card(self, side: int, card_index: int, rank: int, file: int, **kwargs):
        if side > 0:
            # queue target at the index
            self.white_queue[card_index] = [rank, file]
            return self.white_queue
        else:
            self.black_queue[card_index] = [rank, file]
            return self.black_queue

    def lock_in_cards(self, side: int, effects_manager: EffectsManager):
        if side > 0:
            mask = self.white_queue[:,0] != -1
            cards = self.white_hand[mask]
            fast = []
            slow = []
            for card_id, rank, file in zip(cards, self.white_queue[mask,0], self.white_queue[mask,1]):
                card_data = self.card_data[card_id]
                effect_id = card_data['effect_id']

                rank, file = int(rank), int(file)

                coin_data = {
                    'side': side,
                    'card_id': card_id,
                    'effect_id': effect_id,
                    'target': [rank, file],
                    'speed': card_data['speed']
                }
                if card_data['speed'] == 1:
                    fast.append(coin_data)
                elif card_data['speed'] == 2:
                    slow.append(coin_data)
            
            effects_manager.queue_effects(fast, slow)

            mask = np.invert(mask)
            self.white_hand = self.white_hand[mask]

            self.white_coins = [*fast, *slow]
        else:
            mask = self.black_queue[:,0] >= 0
            cards = self.black_hand[mask]
            fast = []
            slow = []
            for card_id, rank, file in zip(cards, self.black_queue[mask,0], self.black_queue[mask,1]):
                card_data = self.card_data[card_id]
                effect_id = card_data['effect_id']

                rank, file = int(rank), int(file)

                coin_data = {
                    'side': side,
                    'card_id': card_id,
                    'effect_id': effect_id,
                    'target': [rank, file],
                    'speed': card_data['speed']
                }
                if card_data['speed'] == 1:
                    fast.append(coin_data)
                elif card_data['speed'] == 2:
                    slow.append(coin_data)
            
            effects_manager.queue_effects(fast, slow)

            mask = np.invert(mask)
            self.black_hand = self.black_hand[mask]

            self.black_coins = [*fast, *slow]

        self._clear_queues()

    def pickup_card(self, side: int, card_index: int, effects_manager: EffectsManager):
        if side > 0:
            card_id = self.white_hand[card_index]
        else:
            card_id = self.black_hand[card_index]
        
        if self.card_data[card_id]['speed'] == 0:
            effect_id = self.card_data[card_id]['effect_id']
            if effect_id in ['backfire']: # TODO: backfire should actually do something
                effects_manager.inflict_side_effect(-side, {
                    'name': effect_id,
                    'duration': -1,
                })
            elif effect_id in ['reveal']:
                effects_manager.inflict_side_effect(-side, {
                    'name': effect_id,
                    'duration': 1
                })
            return True
        return False


class GameState:
    def __init__(self):
        self.effects_manager = EffectsManager()
        self.board_manager = BoardManager(self.effects_manager)
        self.hands_manager = HandsManager()

        self._setup_phase_manager()
    
    def __repr__(self):
        return f"""---
{self.effects_manager}

---
{self.board_manager}"""
    
    def _setup_phase_manager(self):
        self.phase = 0
        self.can_end_turn = [False, False]
        self.current_animation = None

    def _is_turn(self, side: int):
        return ((self.phase == 0 and self.board_manager.side == side) or
                (self.phase in [1, 2] and self.board_manager.side == -side))

    def _get_request(self, req: dict) -> dict:
        side = req['side']
        if req['endpoint'] == 'my_turn':
            if self.board_manager.winner is None:
                return {
                    'status': 'success',
                    'my_turn': self._is_turn(side),
                    'phase': self.phase
                }
            else:
                if self.board_manager.winner == side:
                    winner = 1
                elif self.board_manager.winner == -side:
                    winner = -1
                else:
                    winner = 0
                return {
                    'status': 'success',
                    'my_turn': False,
                    'phase': 0,
                    'winner': winner
                }
        elif req['endpoint'] == 'end_turn':
            if side == 1:
                if np.all(self.can_end_turn):
                    self.can_end_turn = [False, False]
                    return {
                        'status': 'success',
                        'animation': self.current_animation
                    }
                
                self.can_end_turn[0] = True
            elif side == -1:
                if np.all(self.can_end_turn):
                    self.can_end_turn = [False, False]
                    return {
                        'status': 'success',
                        'animation': self.current_animation
                    }
                
                self.can_end_turn[1] = True
            
            if np.all(self.can_end_turn):
                self._finish_turn()
                return {
                    'status': 'success',
                    'animation': self.current_animation
                }
            else:
                return {
                    'status': 'wait_animation'
                }
        elif req['endpoint'] == 'board':
            moveable_effects, static_effects = self.effects_manager.get_field_effects_json()
            return {
                'status': 'success',
                'board_state': self.board_manager.board_state.flatten().tolist(),
                'moveable_effects': moveable_effects,
                'static_effects': static_effects,
                'side_effects': self.effects_manager.get_side_effects_json()
            }
        elif req['endpoint'] == 'hand':
            hands = {
                1: self.hands_manager.white_hand.tolist(),
                -1: self.hands_manager.black_hand.tolist(),
            }
            coins = {
                1: self.hands_manager.white_coins,
                -1: self.hands_manager.black_coins
            }
            return {
                'status': 'success',
                'my_hand': hands[side],
                'opponent_hand': hands[-side],
                'my_coins': coins[side],
                'opponent_coins': coins[-side]
            }
        elif req['endpoint'] == 'moveable_pieces':
            self.board_manager.get_moveable_pieces(self.effects_manager)
            return {
                'status': 'success',
                'moveable_pieces': self.board_manager.moveable_pieces.flatten().astype(int).tolist()
            }
        elif req['endpoint'] == 'possible_moves':
            self.board_manager.get_possible_moves(self.effects_manager)
            return {
                'status': 'success',
                'possible_moves': self.board_manager.possible_moves.flatten().astype(int).tolist()
            }
        elif req['endpoint'] == 'card_queue':
            card_queues = {
                1: self.hands_manager.white_queue.flatten().tolist(),
                -1: self.hands_manager.black_queue.flatten().tolist()
            }
            return {
                'status': 'success',
                'card_queue': card_queues[side]
            }
    
    def _post_request(self, req: dict) -> dict:
        if not self._is_turn(req['side']) or self.phase == 2:
            return {
                'status': 'not_my_turn'
            }
        
        side = req['side']
        params = req['params']
        
        if req['endpoint'] == 'lock_in_move':
            if not self.board_manager.lock_in_move(**params):
                return {
                    'status': 'invalid_move'
                }
        elif req['endpoint'] == 'lock_in':
            if not self.board_manager.move_locked_in():
                return {
                    'status': 'move_not_made'
                }
            self.hands_manager.lock_in_cards(side, self.effects_manager)
            self.phase += 1
        elif req['endpoint'] == 'queue_card':
            card_queue = self.hands_manager.queue_card(side, **params)
            return {
                'status': 'success',
                'card_queue': card_queue.flatten().tolist()
            }
        elif req['endpoint'] == 'pickup_piece':
            if not self.board_manager.pickup_piece(
                effects_manager=self.effects_manager, 
                **params
            ):
                return {
                    'status': 'piece_not_moveable'
                }
            return {
                'status': 'success',
                'possible_moves': self.board_manager.possible_moves.flatten().astype(int).tolist()
            }
        elif req['endpoint'] == 'pickup_card':
            if self.hands_manager.pickup_card(
                req['side'],
                **params
            ):
                return {
                    'status': 'success',
                    'side_effects': self.effects_manager.get_side_effects_json()
                }
        
        return {
            'status': 'success'
        }

    def _finish_turn(self):
        if self.phase != 2:
            self.current_animation = None
            return

        # fast effects are resolved before the move is made
        if self.effects_manager.resolve_fast_effects(self.board_manager, self.hands_manager):
            self.current_animation = 'fast_spells'
            return

        # the board move is made next
        if self.board_manager.make_move(self.effects_manager):
            self.current_animation = 'board_move'
            return
        
        if self.board_manager.check_movement_chain(self.hands_manager):
            self.current_animation = 'summon_card'
            return

        # slow effects are applied
        if self.effects_manager.resolve_slow_effects(self.board_manager, self.hands_manager):
            self.current_animation = 'slow_spells'
            return

        # lingering effects are applied
        self.effects_manager.resolve_field_effects(self.board_manager)

        # turn concludes
        self.board_manager.end_turn(self.effects_manager)
        self.effects_manager.end_turn()
        self.hands_manager.end_turn()

        self.phase = 0

        self.current_animation = 'field_effects'

    def request(self, req: dict):
        if req['method'] == 'get':
            return self._get_request(req)
        elif req['method'] == 'post':
            return self._post_request(req)
        

if __name__ == '__main__':
    ...