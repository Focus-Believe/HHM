import json
import os
import asyncio
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend import db
from backend.manager import Manager

app = FastAPI()
mgr = Manager()

# =========================
# MESSAGE QUEUE (FAST SAVE)
# =========================
save_queue = asyncio.Queue()


# =========================
# BACKGROUND DB WORKER
# =========================
async def save_worker():
    while True:
        sender, receiver, msg, time = await save_queue.get()
        db.save_message(sender, receiver, msg, time)


@app.on_event("startup")
async def startup():
    asyncio.create_task(save_worker())


# =========================
# FRONTEND PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# =========================
# HOME PAGE
# =========================
@app.get("/")
async def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# =========================
# CHAT PAGE
# =========================
@app.get("/chat/{username}")
async def chat(username: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "chat.html"))


# =========================
# USERS LIST
# =========================
@app.get("/users")
async def users():
    data = db.get_users()
    return {"users": [u[0] for u in data]}


# =========================
# CHAT HISTORY
# =========================
@app.get("/history/{me}/{user}")
async def history(me: str, user: str):

    msgs = db.get_messages(me, user)

    return [
        {
            "sender": m[0],
            "receiver": m[1],
            "msg": m[2],
            "time": m[3]
        }
        for m in msgs
    ]


# =========================
# RECENT CHATS
# =========================
@app.get("/recent/{user}")
async def recent(user: str):

    chats = db.get_recent_chats(user)

    return {
        "users": [c[0] for c in chats]
    }


# =========================
# BROADCAST USERS
# =========================
async def send_users():

    users = mgr.users()

    for ws in list(mgr.name_to_ws.values()):
        try:
            await ws.send_text(json.dumps({
                "type": "users",
                "data": users
            }))
        except:
            mgr.disconnect(ws)


# =========================
# WEBSOCKET ENGINE (CORE)
# =========================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    try:

        while True:

            data = json.loads(await websocket.receive_text())
            t = data.get("type")


            # =====================
            # REGISTER
            # =====================
            if t == "register":

                ok = db.register(data["name"], data["password"])

                await websocket.send_text(json.dumps({
                    "type": "register",
                    "ok": ok
                }))


            # =====================
            # LOGIN
            # =====================
            elif t == "login":

                ok = db.login(data["name"], data["password"])

                if ok:
                    await mgr.connect(data["name"], websocket)
                    await send_users()

                await websocket.send_text(json.dumps({
                    "type": "login",
                    "ok": ok
                }))


            # =====================
            # PRIVATE MESSAGE (ANTI DUPLICATE FIXED)
            # =====================
            elif t == "dm":

                sender = mgr.get_name(websocket)
                receiver = data["to"]
                msg = data["msg"]
                time = datetime.now().strftime("%H:%M")

                # save async (non-blocking)
                await save_queue.put((sender, receiver, msg, time))

                payload = json.dumps({
                    "type": "message",
                    "sender": sender,
                    "text": msg,
                    "time": time,
                    "delivered": True
                })

                # send to receiver only
                target_ws = mgr.get_ws(receiver)
                if target_ws:
                    await target_ws.send_text(payload)

                # send to sender once (UI sync)
                await websocket.send_text(payload)


            # =====================
            # TYPING INDICATOR
            # =====================
            elif t == "typing":

                sender = mgr.get_name(websocket)
                receiver = data["to"]

                ws = mgr.get_ws(receiver)

                if ws:
                    await ws.send_text(json.dumps({
                        "type": "typing",
                        "from": sender
                    }))


            # =====================
            # SEEN SYSTEM
            # =====================
            elif t == "seen":

                user = mgr.get_name(websocket)
                other = data["user"]

                db.mark_seen(other, user)


            # =====================
            # HEARTBEAT (optional future stability)
            # =====================
            elif t == "ping":

                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "time": datetime.now().strftime("%H:%M:%S")
                }))


    except WebSocketDisconnect:

        mgr.disconnect(websocket)
        await send_users()
