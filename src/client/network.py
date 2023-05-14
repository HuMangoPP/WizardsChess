import socket, json

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = '192.168.2.24'
        self.port = 5555
        self.addr = (self.server, self.port)
        self.p, self.game_id = self.connect()
    
    def get_p(self):
        return self.p
    
    def get_game_id(self):
        return self.game_id

    def connect(self) -> tuple[str, str]:
        try:
            self.client.connect(self.addr)
            res = self.client.recv(4096).decode()
            res = json.loads(res)
            return res['p'], res['game_id']
        except:
            pass
    
    def send(self, req: dict[str, str | list[int]]) -> dict[str, str | list[str]]:
        try:
            self.client.send(str.encode(json.dumps(req)))
            res = self.client.recv(4096).decode()
            res = json.loads(res)
            return res
        except socket.error as e:
            # print(e)
            return {}
            # pass