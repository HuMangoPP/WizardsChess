import socket, json

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCKET_STREAM)
        self.server = '192.168.2.24'
        self.port = 5555
        self.addr = (self.server, self.port)
        self.json_data = self.connect()

    def get_json_data(self):
        ...
    
    def connect(self):
        try:
            self.client.connect(self.addr)
            return json.loads(self.client.recv(2048).decode())
        except:
            pass
    
    def send(self, data: str):
        try:
            self.client.send(str.encode(json.dumps(data)))
            return json.loads(self.client.recv(2048).decode())
        except socket.error as e:
            print(e)