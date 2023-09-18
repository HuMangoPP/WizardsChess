import socket, json, os


class Network:
    def __init__(self, game_id: int | None = None):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = os.getenv('SERVER')
        self.port = int(os.getenv('PORT'))
        self.addr = (self.server, self.port)
        self._connect(game_id=game_id)
    
    def _connect(self, game_id: int | None = None):
        try:
            self.client.connect(self.addr)
            if game_id is None:
                self.client.send(str.encode(json.dumps({
                    'connection': 'create'
                })))
            else:
                self.client.send(str.encode(json.dumps({
                    'connection': 'join',
                    'game_id': game_id
                })))
            res = self.client.recv(4096).decode()
            res = json.loads(res)
            if res['status'] == 'success':
                self.side = res['side']
                self.game_id = res['game_id']
            else:
                self.side = 0
                self.game_id = -1

        except Exception as e:
            print('Exception in Network._connect()')
            print(e)
        return 0, -1
        
    def send_req(self, req: dict) -> dict:
        try:
            self.client.send(str.encode(json.dumps({
                'game_id': self.game_id,
                'side': self.side,
                **req
            })))
            res = self.client.recv(4096).decode()
            res = json.loads(res)
            return res
        except socket.error as e:
            print('Exception in Network.send_req()')
            print(e)
        return {}
