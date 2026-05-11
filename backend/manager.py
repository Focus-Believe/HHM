import time


class Manager:

    def __init__(self):

        # =========================
        # CONNECTION MAPS
        # =========================
        self.name_to_ws = {}
        self.ws_to_name = {}

        # =========================
        # USER STATUS
        # =========================
        self.online_users = set()
        self.last_seen = {}

        # =========================
        # TYPING STATE
        # =========================
        self.typing = {}

        # =========================
        # FUTURE: ROOMS / GROUP CHAT
        # =========================
        self.rooms = {}

    # =========================
    # CONNECT USER (SAFE VERSION)
    # =========================
    async def connect(self, name, ws):

        # ❗ FIX: prevent duplicate login (multi-tab / reconnect issue)
        if name in self.name_to_ws:

            old_ws = self.name_to_ws[name]

            try:
                await old_ws.close()
            except:
                pass

        self.name_to_ws[name] = ws
        self.ws_to_name[ws] = name

        self.online_users.add(name)
        self.last_seen[name] = self.now()

    # =========================
    # DISCONNECT USER
    # =========================
    def disconnect(self, ws):

        name = self.ws_to_name.get(ws)

        if not name:
            return

        # update status
        self.online_users.discard(name)
        self.last_seen[name] = self.now()

        # cleanup maps
        self.name_to_ws.pop(name, None)
        self.ws_to_name.pop(ws, None)

        # cleanup typing
        self.typing.pop(name, None)

    # =========================
    # GET WEBSOCKET
    # =========================
    def get_ws(self, name):
        return self.name_to_ws.get(name)

    # =========================
    # GET USER NAME
    # =========================
    def get_name(self, ws):
        return self.ws_to_name.get(ws)

    # =========================
    # USERS LIST (ONLINE FIRST)
    # =========================
    def users(self):

        users = list(self.name_to_ws.keys())

        # online first sort
        users.sort(key=lambda x: x not in self.online_users)

        return users

    # =========================
    # ONLINE CHECK
    # =========================
    def is_online(self, name):
        return name in self.online_users

    # =========================
    # LAST SEEN
    # =========================
    def get_last_seen(self, name):
        return self.last_seen.get(name, "never")

    # =========================
    # TYPING SYSTEM
    # =========================
    def set_typing(self, name, value=True):
        self.typing[name] = value

    def is_typing(self, name):
        return self.typing.get(name, False)

    # =========================
    # ROOM / GROUP CHAT SUPPORT
    # =========================
    def join_room(self, room, name):

        if room not in self.rooms:
            self.rooms[room] = set()

        self.rooms[room].add(name)

    def leave_room(self, room, name):

        if room in self.rooms:
            self.rooms[room].discard(name)

    def get_room_users(self, room):
        return list(self.rooms.get(room, []))

    # =========================
    # HEARTBEAT / TIME
    # =========================
    def now(self):
        return time.strftime("%H:%M:%S")
