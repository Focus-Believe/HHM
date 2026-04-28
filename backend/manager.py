class Manager:
    def __init__(self):
        self.name_to_ws = {}
        self.ws_to_name = {}

    async def connect(self,name,ws):
        self.name_to_ws[name]=ws
        self.ws_to_name[ws]=name

    def disconnect(self,ws):
        name=self.ws_to_name.get(ws)
        if name:
            del self.name_to_ws[name]
            del self.ws_to_name[ws]

    def get_ws(self,name):
        return self.name_to_ws.get(name)

    def get_name(self,ws):
        return self.ws_to_name.get(ws)

    def users(self):
        return list(self.name_to_ws.keys())
