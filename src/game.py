from .client import Client
from .server import Server

class Game:
    def __init__(self):
        self.game_running = True

        self.server = Server()
        self.client = Client()
    
    def run(self):
        while self.game_running:
            self.game_running = self.client.update(self.server)
            self.client.render(self.server)
