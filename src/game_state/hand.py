import numpy as np
import pandas as pd


class _Settings:
    CARD_DATA = pd.read_csv('./assets/cards/card_data.csv', index_col=0)


class _Hand:
    def __init__(self):
        self.cards = np.array(['avada_kedavra', 'accio'], object)
        self.played_cards = {}
        self.picked_card_index = -1
        self.picked_card_params = {}
    
    def pick_card(self, card_index: int):
        """
        this function is called whenever a player picks a card from their hand. 
        there can be one of three results:

        * if the card picked has already been played, then the player rescinds the play

        * if the card picked is the one that is currently picked, then the player also rescinds the play

        * if the card picked is a new card, then the player initiates the play
        """
        self.picked_card_params = {}
        if card_index in self.played_cards:
            del self.played_cards[card_index]
        elif card_index == self.picked_card_index:
            self.picked_card_index = -1
        else:
            self.picked_card_index = card_index

    def update_picked_card_params(self, param_value):
        """
        this function is called whenever a player has initiated a play and is
        in the process of inputting the necessary params for the play to complete
        """
        if self.picked_card_index == -1:
            return
        
        card_id = self.cards[self.picked_card_index]
        param_names = _Settings.CARD_DATA.loc[card_id, 'param_names'].split()

        for param_name in param_names:
            if param_name in self.picked_card_params:
                continue

            self.picked_card_params[param_name] = param_value
            break
        
        card_has_all_params = np.all([param_name in self.picked_card_params for param_name in param_names])
        if card_has_all_params:
            self.played_cards[self.picked_card_index] = self.picked_card_params
            self.picked_card_index = -1
            self.picked_card_params = {}
    
    def commit_play(self):
        played_cards = {
            self.cards[played_card_index]: played_card_params
            for played_card_index, played_card_params in self.played_cards.items()
        }
        played_cards = {
            played_card_id: {
                **played_card_params,
                'speed': _Settings.CARD_DATA.loc[played_card_id, 'speed'],
                'debuffs': _Settings.CARD_DATA.loc[played_card_id, 'debuffs'],
                'debuff_length': _Settings.CARD_DATA.loc[played_card_id, 'debuff_length'],
                'color': _Settings.CARD_DATA.loc[played_card_id, ['r', 'g', 'b']].to_numpy()
            }
            for played_card_id, played_card_params in played_cards.items()
        }

        mask = np.ones_like(self.cards, np.bool_)
        indices = np.array([played_card_index for played_card_index in self.played_cards])
        if indices.size:
            mask[indices] = False

        self.cards = self.cards[mask]

        self.played_cards = {}
        self.picked_card_index = -1
        self.picked_card_params = {}

        return played_cards


class HandManager:
    def __init__(self):
        self.hands = {
            1: _Hand(),
            -1: _Hand()
        }
        self.side_to_play = 1
    
    def pick_card(self, event_data: dict):
        if event_data['side'] != self.side_to_play:
            return
        
        if 'card_index' in event_data:
            self.hands[self.side_to_play].pick_card(event_data['card_index'])

    def update_picked_card_params(self, event_data: dict):
        if 'board_index' in event_data:
            self.hands[self.side_to_play].update_picked_card_params(event_data['board_index'])

    def commit_play(self):
        played_cards = self.hands[self.side_to_play].commit_play()
        self.side_to_play *= -1
        return played_cards

    def get_render_data(self):
        white_played_indices = list(self.hands[1].played_cards.keys()) + [self.hands[1].picked_card_index]
        black_played_indices = list(self.hands[-1].played_cards.keys()) + [self.hands[-1].picked_card_index]
        return (
            {1: self.hands[1].cards, -1: self.hands[-1].cards},
            {1: white_played_indices, -1: black_played_indices}
        )
    