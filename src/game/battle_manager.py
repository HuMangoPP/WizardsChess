
from .cards import Hand

class BattleManager:
    def __init__(self):
        self.p1 = PlayerManager()
        self.p2 = PlayerManager()
    
class PlayerManager:
    def __init__(self):
        self.hand = Hand()