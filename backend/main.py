import json
import os
import asyncio

from datetime import datetime

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

from backend import db
from backend.manager import Manager

# =========================
# FASTAPI
# =========================
app = FastAPI()

# =========================
# MANAGER
# =========================
mgr = Manager()

# =========================
# SAVE QUEUE
# =========================
save_queue = asyncio.Queue()

# =========================
# BASE PATHS
# =========================
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "..",
    "frontend"
)

# =========================
# STATIC FILES
# =========================
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)

# =========================
# SAVE WORKER
# =========================
async def save_worker():

    while True:

        sender, receiver, msg, time = (
            await save_queue.get()
        )

        try:

            db.save(
                sender,
                receiver,
                msg,
                time
            )

            print(
                f"[SAVE] {sender} -> {receiver}"
            )

        except Exception as e:

            print(
                "[DB ERROR]",
                e
            )

# =========================
# STARTUP
# =========================
@app.on_event("startup")
async def startup():

    asyncio.create_task(
        save_worker()
    )

# =========================
# HOME PAGE
# USERS PAGE
# =========================
@app.get("/")
async def home():

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "index.html"
        )
    )

# =========================
# PRIVATE CHAT PAGE
# =========================
@app.get("/chat/{user}")
async def private_chat(user: str):

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "chat.html"
        )
    )

# =========================
# API USERS
# =========================
@app.get("/api/users")
async def api_users():

    return JSONResponse(
        mgr.users()
    )

# =========================
# CHAT HISTORY API
# =========================
@app.get("/api/messages/{user1}/{user2}")
async def api_messages(
    user1: str,
    user2: str
):

    data = db.get_messages(
        user1,
        user2
    )

    return JSONResponse(data)

# =========================
# ONLINE USERS BROADCAST
# =========================
async def broadcast_users():

    users = mgr.users()

    payload = json.dumps({
        "type": "users",
        "data": users
    })

    for ws in list(
        mgr.all_ws()
    ):

        try:

            await ws.send_text(
                payload
            )

        except:

            mgr.disconnect(ws)

# =========================
# WEBSOCKET
# =========================
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()

    try:

        while True:

            raw = await websocket.receive_text()

            data = json.loads(raw)

            t = data.get("type")

            # =====================
            # REGISTER
            # =====================
            if t == "register":

                ok = db.register(
                    data["name"],
                    data["password"]
                )

                await websocket.send_text(
                    json.dumps({
                        "type": "register",
                        "ok": ok
                    })
                )

            # =====================
            # LOGIN
            # =====================
            elif t == "login":

                ok = db.login(
                    data["name"],
                    data["password"]
                )

                if ok:

                    await mgr.connect(
                        data["name"],
                        websocket
                    )

                    await broadcast_users()

                await websocket.send_text(
                    json.dumps({
                        "type": "login",
                        "ok": ok
                    })
                )

            # =====================
            # PRIVATE MESSAGE
            # =====================
            elif t == "dm":

                sender = mgr.get_name(
                    websocket
                )

                receiver = data["to"]

                text = data["msg"]

                # empty protection
                if not text.strip():
                    continue

                # limit
                if len(text) > 3000:
                    continue

                time = datetime.now().strftime(
                    "%H:%M"
                )

                # =====================
                # ASYNC SAVE
                # =====================
                await save_queue.put((
                    sender,
                    receiver,
                    text,
                    time
                ))

                payload = json.dumps({

                    "type": "message",

                    "sender": sender,

                    "receiver": receiver,

                    "text": text,

                    "time": time,

                    "delivered": True
                })

                # =====================
                # SEND TO RECEIVER
                # =====================
                target_ws = mgr.get_ws(
                    receiver
                )

                if target_ws:

                    try:

                        await target_ws.send_text(
                            payload
                        )

                    except:
                        pass

                # =====================
                # SEND TO SENDER
                # IMPORTANT:
                # prevents duplicate issue
                # =====================
                try:

                    await websocket.send_text(
                        payload
                    )

                except:
                    pass

            # =====================
            # TYPING
            # =====================
            elif t == "typing":

                sender = mgr.get_name(
                    websocket
                )

                target_ws = mgr.get_ws(
                    data["to"]
                )

                if target_ws:

                    try:

                        await target_ws.send_text(
                            json.dumps({
                                "type": "typing",
                                "from": sender
                            })
                        )

                    except:
                        pass

            # =====================
            # SEEN
            # =====================
            elif t == "seen":

                sender = mgr.get_name(
                    websocket
                )

                target_ws = mgr.get_ws(
                    data["user"]
                )

                if target_ws:

                    try:

                        await target_ws.send_text(
                            json.dumps({
                                "type": "seen",
                                "from": sender
                            })
                        )

                    except:
                        pass

            # =====================
            # PING
            # =====================
            elif t == "ping":

                await websocket.send_text(
                    json.dumps({
                        "type": "pong",
                        "time": datetime.now().strftime(
                            "%H:%M:%S"
                        )
                    })
                )

    # =========================
    # DISCONNECT
    # =========================
    except WebSocketDisconnect:

        mgr.disconnect(
            websocket
        )

        await broadcast_users()

    # =========================
    # OTHER ERROR
    # =========================
    except Exception as e:

        print(
            "[WS ERROR]",
            e
        )

        mgr.disconnect(
            websocket
        )

        await broadcast_users()
